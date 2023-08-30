import logging

from odata.client import Client
from odata._query_constructors import QueryFilter as Filter

import odata.types as types

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s : %(message)s', level=logging.DEBUG)

odata_logger = logging.getLogger("odata")


odata_logger.level = logging.DEBUG


class _Source:
    __base_url: str = "{_platforms[self.platform]}auth/realms/{_realms[self.platform]}/protocol/openid-connect/token"

    def __init__(self, api_url: str, name: str, platform: str, realm: str):
        pass


class Source:
    creodias: _Source = _Source("creodias",
                                "https://datahub.creodias.eu/odata/v1/",
                                )