import asyncio
import os
import time
import typing
import logging

import odata.errors as errors
import odata.types as types

from odata.http import Token, Http

logger = logging.getLogger("odata")


class Client:
    """
    Represents connection to odata API. You use this class to interact with data.

    @var email: Email of authenticated user
    @var http: Class Http for HTTP authorization & requests
    """
    def __init__(self, source: typing.Literal["creodias", "codede", "copernicus"] = "creodias",
                 download_directory: str = "", **options):
        """
        Creates client instance with configuration

        @param source: Name of platform to source from. Note not every platform has every endpoint.
        @param download_directory: Preferably absolute path to directory to store downloaded products from. Default directory of script.
        @param options: Other options.
        """
        self.__loop: asyncio.AbstractEventLoop = asyncio.new_event_loop()
        self.__run_event: asyncio.Event = asyncio.Event()
        self.__token: typing.Optional[Token] = None
        self.http: typing.Optional[Http] = None

        self._download_directory = download_directory or os.getcwd()
        self._source = source

        self.__on_ready: typing.Optional[typing.Any] = None
        self.__ready_event: asyncio.Event = asyncio.Event()

        self.email: str = ""

    @property
    def products(self) -> types.OProductsQueryConstructor:
        """
        Returns query constructor for product calls.

        Returned class is used to make requests for products.

        @return: Products query constructor
        """
        return types.OProductsQueryConstructor(self)

    @property
    def workflows(self) -> types.OWorkflowsQueryConstructor:
        """
        Query constructor for workflow calls

        @return: Workflow query constructor
        """
        return types.OWorkflowsQueryConstructor(self)

    def run(self, email: str, password: str, totp_key: str = "",
            totp_code: str | typing.Callable[[], str] = "",
            platform: str = "creodias") -> None:
        """
        Authenticates user by provided credentials, generates token. If any funtion was set on ready, it will be called.

        @param email: Email for account
        @param password: Password associated with email
        @param totp_key: If account has 2FA, you can pass totp secret and 2FA code will be generated automatically
        @param totp_code: In case of 2FA, you can pass single code which will be used. Function can be provided for automatic calls.
        @param platform: Platform provided account is on. Supported "creodias", "copernicus" and "codede"
        @return: None
        """

        self.email = email

        self.__token = Token(email, password, totp_key, totp_code, platform, self.__loop)

        self.http = Http(self.__token, self._source, self._download_directory)

        logger.info(f"Client connection for {self.email} is live")

        if self.__on_ready:
            task = self.__loop.create_task(self.__exceptions(self.__on_ready()))
            result = asyncio.ensure_future(task)
        self.__loop.run_forever()

    async def stop(self):
        """
        Halts client. Token will not be refreshed.

        @return: None
        """
        self.__token.stop()
        self.__loop.stop()  # TODO: Fix errors notification

    def ready(self, func: typing.Callable[[], None]) -> typing.Callable[[], None]:
        """
        Decorated function will be called when client will be ready

        @param func: Asynchronous function
        @return: No wrapper is created
        """
        self.__on_ready: typing.Callable[[], None] = func
        return func

    @staticmethod
    async def __exceptions(function):
        try:
            return await function
        except Exception as e:
            logger.exception(f"Exception {e.__class__.__name__} raised during task execution:")

            # raise e.__cause__
