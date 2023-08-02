from __future__ import annotations

import asyncio
import dataclasses
import datetime
import typing
import logging
import pyotp
import requests

import odata.errors as errors

logger = logging.getLogger("odata")

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


class Token:
    def __init__(self, credentials: Credentials):
        self.__token: str = ""
        self.__token_expires: datetime.datetime = datetime.datetime.now() - datetime.timedelta(1, 0)

        self.__refresh_token: str = ""
        self.__refresh_expires: datetime.datetime = datetime.datetime.now() - datetime.timedelta(1, 0)

        self.__credentials = credentials

        self.keep_alive = True
        self._alive_task: typing.Optional[asyncio.Task] = None

    def __str__(self) -> str:
        if self.__token_expires < self.__time_now < self.__refresh_expires:
            self.__refresh()
        elif self.__token_expires < self.__time_now or self.__refresh_expires < self.__time_now:
            self._update()
        return self.__token

    def __refresh(self):
        with requests.Session() as session:
            data = {
                "client_id": self.__credentials.client_id,
                "grant_type": "refresh_token",
                "refresh_token": self.__refresh_token
            }
            response = session.post(url=self.__credentials.url, data=data)
        if self.__save(response):
            logger.debug(f"Token refreshed")
        return

    def _update(self):
        with requests.Session() as session:
            data = {
                "client_id": self.__credentials.client_id,
                "username": self.__credentials.email,
                "password": self.__credentials.password,
                "grant_type": "password",
                # "totp": self.__credentials.totp
            }
            response = session.post(self.__credentials.url, data=data, verify=True)
        if self.__save(response):
            logger.debug(f"Token created for {response.json()['expires_in']}s")
        return

    def __save(self, response: requests.Response):
        if not response.ok:
            raise errors.AuthorizationFailedError(response.status_code, response.reason)
        data = response.json()
        self.__token = data["access_token"]
        expires = float(data["expires_in"])
        self.__token_expires: datetime.datetime = self.__time_now + datetime.timedelta(0, expires)

        self.__refresh_token = data["refresh_token"]
        refresh_expires = float(data["refresh_expires_in"])
        self.__refresh_expires: datetime.datetime = self.__time_now + datetime.timedelta(0, refresh_expires)
        return True

    async def _keep_alive(self):
        logger.debug(f"Keeping alive; refresh after {(self.__refresh_expires - self.__time_now).total_seconds() - 10}s")
        await asyncio.sleep((self.__token_expires - self.__time_now).total_seconds() - 10)
        if self.keep_alive:
            self.__refresh()
        await self._keep_alive()

    @property
    def __time_now(self) -> datetime.datetime:
        return datetime.datetime.now()

    @staticmethod
    async def new(email: str, password: str, totp_key: typing.Optional[str] = "",
                  totp_code: str | typing.Callable[[], str] = "",
                  platform: str = "creodias") -> Token:

        if platform not in _platforms:
            raise errors.InvalidPlatformError(platform, list(_platforms.keys()))
        logger.debug(f"Creating new token for {email}")
        totp = Totp(totp_key=totp_key, totp_code=totp_code)
        token = Token(credentials=Credentials(email, password, platform, totp))
        token._update()

        token._alive_task = asyncio.create_task(token._keep_alive())

        return token

    async def stop(self):
        self._alive_task.cancel()


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
