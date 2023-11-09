class KeyCloakPlatform:
    def __init__(self, domain: str, realm: str, user_id: str):
        self.__domain: str = domain
        self.__realm: str = realm
        self.__id: str = user_id

    @property
    def scheme(self) -> str:
        return "{domain}/admin/realms/{realm}".format(domain=self.__domain, realm=self.__realm)


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
