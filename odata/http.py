from __future__ import annotations

import asyncio
import dataclasses
import datetime
import typing
import logging
import pyotp
import aiohttp

import odata.errors as errors

logger = logging.getLogger("odata.http")

_platforms: dict[str, str] = {
    "creodias": "https://identity.cloudferro.com/",
    "codede": "https://auth.cloud.code-de.org/",
    "copernicus": "https://identity.dataspace.copernicus.eu/"
}

_realms: dict[str, str] = {
    "creodias": "Creodias-new",
    "codede": "code-de",
    "copernicus": "CDSE"
}

_client_ids: dict[str, str] = {
    "creodias": "CLOUDFERRO_PUBLIC",
    "codede": "finder",
    "copernicus": "cdse-public"
}


@dataclasses.dataclass
class Credentials:
    email: str
    password: str
    platform: str
    __totp: Totp

    @property
    def client_id(self) -> str:
        return _client_ids[self.platform]

    @property
    def url(self) -> str:
        url = f"{_platforms[self.platform]}auth/realms/{_realms[self.platform]}/protocol/openid-connect/token"
        return url

    @property
    def totp(self):
        return self.__totp


class RefreshToken:
    def __init__(self, value: str, expires: int):
        self.value = value
        self.expires: datetime.datetime = datetime.datetime.now() + datetime.timedelta(0, expires)

    def __nonzero__(self) -> bool:
        return datetime.datetime.now() < self.expires


class Token:
    """
    Class for storing and refreshing access token. __str__ returns access token.
    >>> import os
    >>> token: Token = Token(os.environ.get("email"), os.environ.get("password"), platform="copernicus")
    >>> print(token.value)
    # TODO: Check tests

    """
    __time_margin = 20
    __keep_alive = True

    def __init__(self, email: str, password: str, totp_key: typing.Optional[str] = "",
                 totp_code: str | typing.Callable[[], str] = "",
                 platform: str = "creodias", loop: asyncio.AbstractEventLoop = None):
        if platform not in _platforms:
            raise errors.InvalidPlatformError(platform, list(_platforms.keys()))

        totp = Totp(totp_key=totp_key, totp_code=totp_code)
        self.__credentials: Credentials = Credentials(email, password, platform, totp)
        self.__token, self.expires, self.__refresh_token = asyncio.run(self.__get())
        self.__loop = loop or asyncio.new_event_loop()

        self.alive: asyncio.Task = self.__loop.create_task(self.__exceptions(self.__alive()))
        result = asyncio.ensure_future(self.alive)

        logger.debug(f"Token created for user {self.__credentials.email} valid for {self.__seconds_to(self.expires)}s")

    @staticmethod
    def __seconds_to(date: datetime.datetime) -> float:
        return (date - datetime.datetime.now()).total_seconds() - Token.__time_margin

    @property
    async def value(self) -> str:
        if not datetime.datetime.now() < self.expires and self.__refresh_token:
            await self.__refresh()
        elif not datetime.datetime.now() < self.expires or not self.__refresh_token:
            await self.__get()
        return self.__token

    async def __alive(self):
        start = datetime.datetime.now()
        try:
            while True:
                await asyncio.sleep(self.__seconds_to(self.expires))
                if self.__keep_alive:
                    await self.__refresh()
                    logger.debug(f"Token for {self.__credentials.email} refreshed. Valid for {self.__seconds_to(self.expires)}s")
        except asyncio.CancelledError:
            logger.debug(f"Token refresh interval interrupted after {(datetime.datetime.now() - start).total_seconds()}s of runtime; "
                         f"{self.__credentials.email} valid for {self.__seconds_to(self.expires) + self.__time_margin}s more")
            raise
        finally:
            self.alive = None

    def stop(self):
        if not self.alive.cancelled():
            self.alive.cancel()

    async def __refresh(self):
        async with aiohttp.ClientSession() as session:
            data = {
                "client_id": self.__credentials.client_id,
                "grant_type": "refresh_token",
                "refresh_token": self.__refresh_token
            }
            response = await session.post(url=self.__credentials.url, data=data)
        if not response.ok:
            raise errors.AuthorizationFailedError(response.status, response.reason)
        logger.debug(f"Token for {self.__credentials.email} refreshed")

        self.__token = data["access_token"]
        self.expires = datetime.datetime.now() + datetime.timedelta(0, data["expires_in"])
        self.__refresh_token = RefreshToken(data["refresh_token"], data["refresh_expires_in"])

        return

    async def __get(self) -> [str, datetime.datetime, typing.Optional[RefreshToken]]:
        async with aiohttp.ClientSession() as session:
            data = {
                "client_id": self.__credentials.client_id,
                "username": self.__credentials.email,
                "password": self.__credentials.password,
                "grant_type": "password",
                "totp": self.__credentials.totp
            }
            async with session.post(self.__credentials.url, data=data) as response:
                if not response.ok:
                    raise errors.AuthorizationFailedError(response.status, response.reason)
                data = await response.json()
                values = [
                    data["access_token"],
                    datetime.datetime.now() + datetime.timedelta(0, data["expires_in"]),
                    RefreshToken(data["refresh_token"], data["refresh_expires_in"])
                ]
                return values
        return "", datetime.datetime.now(), None

    @staticmethod
    async def __exceptions(function):
        try:
            return await function
        except Exception as e:
            logger.exception(f"Exception raised during task execution:")

            raise e.__cause__


class Totp:
    def __init__(self, totp_key: str = "",
                 totp_code: str | typing.Callable[[], str] = ""):
        self.__totp_key: typing.Optional[str] = totp_key
        self.__totp_code: typing.Optional[str | typing.Callable[[], str]] = totp_code

    def __str__(self) -> str:
        if self.__totp_key:
            totp = pyotp.TOTP(self.__totp_key)
            code = totp.now()
        elif isinstance(self.__totp_code, typing.Callable):
            code = self.__totp_code()
        else:
            code = self.__totp_code
        return code


class Http:
    def __init__(self, token):
        self.__token: Token = token

    async def request(self, method: str, url: str, **kwargs) -> [dict, aiohttp.ClientResponse]:
        async with aiohttp.ClientSession() as session:
            session.headers["authorization"] = f"Bearer {await self.__token.value}"
            async with session.request(method, url, **kwargs) as response:

                logger.debug(f"{response.method} {response.status} - {response.url}")

                if not response.ok:
                    logger.debug(f"Endpoint for {url} returned {response.status} - {response.reason}")

                if response.status in (401, 403):
                    raise errors.UnauthorizedError(response.status, response.reason)

                return response, await response.json()


if __name__ == "__main__":
    import doctest
    doctest.testmod(verbose=True)
