import asyncio
import time
import typing
import logging
import requests

import odata.errors as errors
import odata.types as types

from odata.__authentication import Token


logger = logging.getLogger("odata")


class Client:
    def __init__(self):
        self.__live: bool = False
        self.__run_event: asyncio.Event = asyncio.Event()
        self.token: typing.Optional[Token] = None

        self.__on_ready: typing.Optional[typing.Any] = None
        self.__ready_event: asyncio.Event = asyncio.Event()

        self.__loop = asyncio.get_event_loop()

        self.email: str = ""

        self.production: typing.Optional[types.Production] = None
        self.workflows: typing.Optional[types.WorkflowsGroup] = None

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

    async def run(self, email: str, password: str, totp_key: str = "",
                  totp_code: str | typing.Callable[[], str] = "",
                  platform: str = "creodias"):

        self.email = email

        self.token = await Token.new(email, password, totp_key, totp_code, platform)
        self.live = True

        self.production = types.Production(self.token)
        self.workflows = types.WorkflowsGroup(self.token)

        logger.info(f"Client connection for {self.email} is live")
        asyncio.ensure_future(self.__run_event.wait())
        return

    async def stop(self):
        logger.debug(f"Client revoked")
        await self.token.stop()
        self.__run_event.clear()

        self.live = False
        self.token = None

    async def latency(self) -> float:
        production_orders = await self.production.orders(
            "",
            "",
            False,
            0
        )
        return production_orders.latency

    def ready(self, func: typing.Callable[[], None]):
        self.__on_ready: typing.Callable[[], None] = func
        return func

    async def wait_until_ready(self):
        await self.__ready_event.wait()
        return
