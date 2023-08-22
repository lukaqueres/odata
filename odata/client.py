import asyncio
import os
import time
import typing
import logging
import requests

import odata.errors as errors
import odata._types as _types
import odata._query_constructors as _constructors

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
    def product(self) -> _constructors.OProductsQueryConstructor:
        return _constructors.OProductsQueryConstructor(self)

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

    async def workflows(self, expand, query_filter: str, order_by: str, count: bool = False, top: int = 1000,
                        skip: int = 0) -> _types.ODataWorkflowsCollection:
        return await _types.ODataWorkflowsCollection.fetch(client=self, expand=expand, query_filter=query_filter,
                                                           order_by=order_by, count=count, top=top, skip=skip)

    async def production_orders(self, query_filter: str = "", order_by: str = "", count: bool = False,
                                top: int = 1000, skip: int = 0) -> _types.ODataProductionOrderCollection:
        return await _types.ODataProductionOrderCollection.fetch(self, query_filter, order_by, count, top, skip)

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
