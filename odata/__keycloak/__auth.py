"""
@version 2.2

Authentication & __keycloak of user

@author lukaqueres

"""

from __future__ import annotations

import asyncio
import aiohttp
import logging
import datetime
import pyotp
from typing import Optional, Union, Callable, Coroutine, Any

import odata.errors as errors

logger = logging.getLogger("odata.auth")


class _Totp:
    def __init__(self, totp_key: str = "",
                 totp_code: str | Callable[[], str] = ""):
        self.__totp_key: Optional[str] = totp_key
        self.__totp_code: Optional[str | Callable[[], str]] = totp_code

    @classmethod
    def set(cls, value: Union[str, Callable[[], str]]) -> _Totp:
        value = value.replace(" ", "")
        return _Totp(totp_key=value if len(value) > 6 else "",
                     totp_code=value if len(value) == 6 or isinstance(value, Callable) else ""
                     )

    def __str__(self) -> str:
        if self.__totp_key:
            totp = pyotp.TOTP(self.__totp_key)
            code = totp.now()
        elif isinstance(self.__totp_code, Callable):
            code = self.__totp_code()
        else:
            code = self.__totp_code
        return code


class ODataAuthPlatform:

    _host: str = ""
    _realm: str = ""
    _id: str = ""

    def __init__(self, email: str, password: str, totp: Optional[Union[str, Callable[[], str]]] = None):
        self._email: str = email
        self._password: str = password
        self._totp: Optional[_Totp] = _Totp.set(totp) if totp else None

    def payload(self) -> dict:
        data = {
            "client_id": self.id(),
            "username": self._email,
            "password": self._password,
            "grant_type": "password",
            "totp": self._totp
        }

        return data

    @classmethod
    def host(cls) -> str:
        return cls._host

    @classmethod
    def realm(cls) -> str:
        return cls._realm

    @classmethod
    def id(cls) -> str:
        return cls._id

    @classmethod
    def auth(cls) -> [str, str]:
        return f"{cls.host()}auth/realms/{cls.realm()}/protocol/openid-connect/token"


class Creodias(ODataAuthPlatform):
    _host: str = "https://identity.cloudferro.com/"
    _realm: str = "Creodias-new"
    _id: str = "CLOUDFERRO_PUBLIC"


class CodeDE(ODataAuthPlatform):
    _host: str = "https://auth.cloud.code-de.org/"
    _realm: str = "code-de"
    _id: str = "finder"


class Copernicus(ODataAuthPlatform):
    _host: str = "https://identity.dataspace.copernicus.eu/"
    _realm: str = "CDSE"
    _id: str = "cdse-public"


class Platform:
    Creodias: Creodias = Creodias
    CodeDE: CodeDE = CodeDE
    Copernicus: Copernicus = Copernicus


class AuthSession:
    """
    Authorization Token

        >>> import os
        >>> platform = Platform.Copernicus(os.environ.get("email"), os.environ.get("password"))

        >>> loop = asyncio.new_event_loop()
        >>> session = loop.run_until_complete(AuthSession.authorize(platform))
        >>> loop.run_until_complete(session.sustain(2))
        >>> loop.run_until_complete(asyncio.sleep(7))

    """

    __sustain_time_margin = 20

    def __init__(self, platform: Union[Creodias, Copernicus, CodeDE], token: Token,
                 loop: Optional[asyncio.AbstractEventLoop] = None):
        self.__platform:  Union[Creodias, Copernicus, CodeDE] = platform
        self.__loop: asyncio.AbstractEventLoop = loop or asyncio.new_event_loop()

        self.__token: Token = token
        self.__tokens: list[Token] = []

        self.__sustain: Optional[asyncio.Task] = None
        self.__debug_sustain_interval = 10

        self.__established: datetime.datetime = datetime.datetime.now()

    @property
    def debug(self) -> dict:
        stats: dict = {
            "established": self.__established,
            "tokens": len(self.__tokens),

        }
        return stats

    @classmethod
    async def authorize(cls, platform: Union[Creodias, Copernicus, CodeDE],
                        loop: Optional[asyncio.AbstractEventLoop] = None) -> AuthSession:
        session = AuthSession(platform, await Token.new(platform), loop=loop)

        return session

    async def refresh(self):
        self.__tokens.append(self.__token)
        await self.__token.refresh.refresh()

    async def __new(self):
        self.__tokens.append(self.__token)
        self.__token = await Token.new(self.__platform)

    async def token(self) -> str:
        """
        Checks if token is still valid, if not refreshes or generates new. Returns token

        @return: Current token string
        """
        if self.__token:
            pass
        elif not self.__token and self.__token.refresh:
            await self.refresh()
        else:
            await self.__new()
        return str(self.__token)

    async def sustain(self, interval: Optional[int] = 0):
        if self.__sustain and not (self.__sustain.cancelled() or self.__sustain.done()):
            raise RuntimeError("Session Keep alive is already running.")
        logger.debug(f"Session - Sustain")
        self.__sustain = asyncio.create_task(self._alive(interval or None), name="Session Token automatic refresh")
        future = asyncio.ensure_future(self.__sustain)
        self.__sustain.add_done_callback(self._handle)  # TODO: Is always canceled (?)

    async def _alive(self, interval: Optional[int] = 0):
        while True:
            try:
                interval = interval or self.__debug_sustain_interval or (
                        self.__token.expires_in - self.__sustain_time_margin)
                logger.debug(f"Session - Sustain : Trigger - next in {interval}")
                await asyncio.sleep(interval)
                await self.refresh()
            except asyncio.CancelledError:
                print("cancel")
                break
            except Exception as e:
                raise e

    @staticmethod
    def _handle(task: asyncio.Task) -> None:
        try:
            task.result()
        except asyncio.CancelledError:
            logger.debug(f"Session - Sustain : Cancelled")
        except Exception as e:
            logger.exception(f"Exception {e.__class__.__name__} raised during task {task.get_name()}")
            raise e


class AuthToken:
    def __init__(self, platform: Union[Creodias, Copernicus, CodeDE], value: str, expires_in: int):
        self._platform: Union[Creodias, Copernicus, CodeDE] = platform
        self._value: str = value
        self._expires_in: int = expires_in
        self.expires: datetime.datetime = datetime.datetime.now() + datetime.timedelta(0, self._expires_in)

        self.revoked = False

    @property
    def expires_in(self):
        return (self.expires - datetime.datetime.now()).total_seconds()

    def __str__(self) -> str:
        return self._value

    def __bool__(self):
        return self.expires > datetime.datetime.now() and not self.revoked

    def __eq__(self, other) -> bool:
        if not isinstance(other, AuthToken):
            return NotImplemented

        return str(self) == str(other)

    @staticmethod
    async def _request(url: str, data: dict) -> dict[str, dict]:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=data) as response:
                logger.debug(f"{url} - {response.status} : {response.reason}")
                if not response.ok:
                    logger.error(await response.content.read())
                    raise errors.AuthenticationFailed(response.status, response.reason)
                data = await response.json()
            return {
                "token": {"value": data["access_token"], "expires": data["expires_in"]},
                "refresh": {"value": data["refresh_token"], "expires": data["refresh_expires_in"]}
            }


class Token(AuthToken):
    """

        >>> import os
        >>> platform = Platform.Copernicus(os.environ.get("email"), os.environ.get("password"))

        >>> token = asyncio.run(Token.new(platform))
        >>> bool(token)
        True


    """

    def __init__(self, platform: Union[Creodias, Copernicus, CodeDE], value: str, expires_in: int,
                 refresh_token: RefreshToken):
        super().__init__(platform, value=value, expires_in=expires_in)
        self.__refresh_token: RefreshToken = refresh_token

    @classmethod
    async def new(cls, platform: Union[Creodias, Copernicus, CodeDE]) -> Token:
        result = await cls._request(platform.auth(), platform.payload())

        token = Token(platform=platform, value=result["token"]["value"], expires_in=result["token"]["expires"],
                      refresh_token=RefreshToken(platform, value=result["refresh"]["value"],
                                                 expires_in=result["refresh"]["expires"]))

        token.refresh.token = token
        logger.debug(f"New Token - expires {token.expires}; {token.expires_in}s left; \n")
        logger.debug(f"Refresh Token - valid until {token.refresh.expires}; {token.refresh.expires_in}s left")

        return token

    @property
    def refresh(self) -> RefreshToken:
        return self.__refresh_token

    def revoke(self):
        self.revoked = self.refresh.revoked = True


class RefreshToken(AuthToken):
    """

        >>> import os
        >>> platform = Platform.Copernicus(os.environ.get("email"), os.environ.get("password"))

        >>> token = asyncio.run(Token.new(platform))
        >>> new_token = asyncio.run(token.refresh.refresh())
        >>> new_token == token
        False

    """
    def __init__(self, platform: [Creodias, Copernicus, CodeDE], value: str, expires_in: int):
        super().__init__(platform, value=value, expires_in=expires_in)
        self.token: Optional[Token] = None

    @property
    def __payload(self) -> dict:
        data = {"client_id": self._platform.id(),
                "grant_type": "refresh_token",
                "refresh_token": self._value
                }
        return data

    async def __call__(self, *args, **kwargs) -> Token:
        return await self.refresh()

    async def refresh(self) -> Token:
        result = await self._request(self._platform.auth(), self.__payload)
        self.revoked = self.token.revoked = True

        token = Token(platform=self._platform, value=result["token"]["value"], expires_in=result["token"]["expires"],
                      refresh_token=RefreshToken(self._platform, value=result["refresh"]["value"],
                                                 expires_in=result["refresh"]["expires"]))
        token.refresh.token = token

        logger.debug(f"Token refreshed - expires {token.expires}; {token.expires_in}s left")
        logger.debug(f"New Refresh Token - valid until {token.refresh.expires}; "
                     f"{token.refresh.expires_in}s left")
        return token


if __name__ == "__main__":
    import doctest
    doctest.testmod(verbose=True)
