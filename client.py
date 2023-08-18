import asyncio
import os
import time
import typing
import logging
import requests

import odata.errors as errors
import odata._types as _types

from odata.__authentication import Token

logger = logging.getLogger("odata")


class Client:

    def __init__(self, source: typing.Literal["creodias", "codede"] = "creodias", ssl_verify: bool = True):
        self.__live: bool = False
        self.__run_event: asyncio.Event = asyncio.Event()
        self.token: typing.Optional[Token] = None

        if source not in ("creodias", "codede"):
            raise ValueError(f"Invalid data source. Try `creodias` or `codede`")
        self.source = source

        self._ssl_verify = ssl_verify

        self.__on_ready: typing.Optional[typing.Any] = None
        self.__ready_event: asyncio.Event = asyncio.Event()

        self.production_order = _types.ProductionOrder(client=self)

        self.email: str = ""

    @property
    def live(self) -> bool:
        return self.__live

    @live.setter
    def live(self, value: bool):
        self.__live = value
        if value is True:
            asyncio.create_task(self.__on_ready())
            self.__ready_event.set()
        else:
            self.__ready_event: asyncio.Event = asyncio.Event()
            self.__run_event: asyncio.Event = asyncio.Event()

    @property
    def __api_url(self):
        api_urls = {
            "creodias": "https://datahub.creodias.eu/odata/v1/",
            "codede": os.environ.get("CODEDE_TEST_URL")  # TODO: Update after release
        }
        return api_urls[self.source]

    async def fetch(self, method: typing.Literal["post", "get"], endpoint: str = "", params: dict = {}, data: dict = {},
                    url: str = "",
                    *args, **kwargs) -> requests.Response:
        with requests.Session() as session:

            if self.source != "codede":  # TODO: TEMPORARY FIX FOR CODEDE REQUESTS
                session.headers["authorization"] = f"Bearer {self.token}"

            if method == "get":
                params = {k: v for k, v in params.items() if v}
                response: requests.Response = session.get(f"{self.__api_url}{endpoint}" if not url else url, *args,
                                                          params=params, **kwargs, verify=self._ssl_verify)
            else:
                response: requests.Response = session.post(f"{self.__api_url}{endpoint}" if not url else url, *args,
                                                           data=data, **kwargs, verify=self._ssl_verify)

        if response.status_code in (401, 403):
            raise errors.UnauthorizedError(response.status_code, response.reason)

        if not response.ok:
            logger.debug(f"Endpoint for {endpoint} returned {response.status_code} - {response.reason}")

        return response

    async def workflows(self, expand, query_filter: str, order_by: str, count: bool = False, top: int = 1000,
                        skip: int = 0) -> _types.ODataWorkflowsCollection:
        return await _types.ODataWorkflowsCollection.fetch(client=self, expand=expand, query_filter=query_filter,
                                                           order_by=order_by, count=count, top=top, skip=skip)

    async def production_orders(self, query_filter: str = "", order_by: str = "", count: bool = False,
                                top: int = 1000, skip: int = 0) -> _types.ODataProductionOrderCollection:
        return await _types.ODataProductionOrderCollection.fetch(self, query_filter, order_by, count, top, skip)

    async def products(self, query_filter: str, order_by: str, top: int = 1000, skip: int = 0,
                       count: bool = False, expand: str = "") -> _types.EOProductsCollection:

        return await _types.EOProductsCollection.fetch(self, query_filter=query_filter, order_by=order_by, top=top,
                                                       skip=skip, count=count, expand=expand)

    async def run(self, email: str, password: str, totp_key: str = "",
                  totp_code: str | typing.Callable[[], str] = "",
                  platform: str = "creodias"):

        self.email = email

        self.token = await Token.new(email, password, totp_key, totp_code, platform)
        self.live = True

        logger.info(f"Client connection for {self.email} is live")
        asyncio.ensure_future(self.__run_event.wait())
        return

    async def stop(self):
        logger.debug(f"Client revoked")
        await self.token.stop()
        self.__run_event.clear()

        self.live = False
        self.token = None

    def ready(self, func: typing.Callable[[], None]):
        self.__on_ready: typing.Callable[[], None] = func
        return func

    async def wait_until_ready(self):
        await self.__ready_event.wait()
        return
