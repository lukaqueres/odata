import asyncio
import os
import time
import typing
import logging
import requests

import odata.errors as errors
import odata._types as _types
import odata._query_constructors as _constructors

from odata.http import Token, Http

logger = logging.getLogger("odata")


class Client:

    def __init__(self, source: typing.Literal["creodias", "codede"] = "creodias"):
        self.__loop: asyncio.AbstractEventLoop = asyncio.new_event_loop()
        self.__run_event: asyncio.Event = asyncio.Event()
        self.__token: typing.Optional[Token] = None
        self.http: typing.Optional[Http] = None

        self.source = source

        self.__on_ready: typing.Optional[typing.Any] = None
        self.__ready_event: asyncio.Event = asyncio.Event()

        self.email: str = ""

    @property
    def product(self) -> _constructors.OProductsQueryConstructor:
        return _constructors.OProductsQueryConstructor(self)

    def run(self, email: str, password: str, totp_key: str = "",
            totp_code: str | typing.Callable[[], str] = "",
            platform: str = "creodias"):

        self.email = email

        self.__token = Token(email, password, totp_key, totp_code, platform, self.__loop)

        self.http = Http(self.__token)

        logger.info(f"Client connection for {self.email} is live")

        if self.__on_ready:
            task = self.__loop.create_task(self.__exceptions(self.__on_ready()))
            result = asyncio.ensure_future(task)
        self.__loop.run_forever()

    async def stop(self):
        self.__token.stop()

    def ready(self, func: typing.Callable[[], None]):
        self.__on_ready: typing.Callable[[], None] = func
        return func

    @staticmethod
    async def __exceptions(function):
        try:
            return await function
        except Exception:
            raise
