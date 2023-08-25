from __future__ import annotations

import os
import datetime
from dataclasses import dataclass

import typing
from typing import Literal
from string import Formatter
import logging
import aiohttp

if typing.TYPE_CHECKING:
    from odata.client import Client

import odata.errors as errors
from odata._types import OProductNodesCollection, OProductsCollection, ODataWorkflowsCollection
from odata._helpers import TimeConverter

logger = logging.getLogger("odata")


@dataclass
class Coordinates:
    x: float
    y: float

    def __str__(self):
        return f"{self.x} {self.y}"


class Attribute:
    def __init__(self, name: str, a_type: str):
        self.name: str = name
        self.type: str = a_type


class Attributes:
    Origin = Attribute("origin", "OData.CSC.StringAttribute")
    Authority = Attribute("authority", "OData.CSC.StringAttribute")
    Timeliness = Attribute("timeliness", "OData.CSC.StringAttribute")
    Coordinates = Attribute("coordinates", "OData.CSC.DoubleAttribute")
    OrbitNumber = Attribute("orbitNumber", "OData.CSC.IntegerAttribute")
    ProductType = Attribute("productType", "OData.CSC.StringAttribute")
    SliceNumber = Attribute("sliceNumber", "OData.CSC.IntegerAttribute")
    ProductClass = Attribute("productClass", "OData.CSC.StringAttribute")
    EndingDateTime = Attribute("endingDateTime", "OData.CSC.DateTimeOffsetAttribute")
    OrbitDirection = Attribute("orbitDirection", "OData.CSC.StringAttribute")
    OperationalMode = Attribute("operationalMode", "OData.CSC.StringAttribute")
    ProcessingLevel = Attribute("processingLevel", "OData.CSC.StringAttribute")
    SwathIdentifier = Attribute("swathIdentifier", "OData.CSC.StringAttribute")
    BeginningDateTime = Attribute("beginningDateTime", "OData.CSC.DateTimeOffsetAttribute")
    PlatformShortName = Attribute("platformShortName", "OData.CSC.StringAttribute")
    SpatialResolution = Attribute("spatialResolution", "OData.CSC.DoubleAttribute")
    InstrumentShortName = Attribute("instrumentShortName", "OData.CSC.StringAttribute")
    RelativeOrbitNumber = Attribute("relativeOrbitNumber", "OData.CSC.IntegerAttribute")
    PolarisationChannels = Attribute("polarisationChannels", "OData.CSC.StringAttribute")
    PlatformSerialIdentifier = Attribute("platformSerialIdentifier", "OData.CSC.StringAttribute")

    @staticmethod
    def satisfies(attribute: Attribute,
                  operator: Literal["eq", "==", "le", "<=", "lt", "<", "ge", ">=", "gt", ">", "!=", "in"],
                  value: typing.Union[str, int, float, datetime.datetime,
                                      list[typing.Union[str, int, float, datetime.datetime]]]
                  ) -> TFilter | TFilterGroup:

        if operator == "!=":
            return AttributesFilter(
                "not Attributes/{_type}/any(att:att/Name eq '{_name}' and att/{_type}/Value {_operator} {_value})",
                attribute, "eq", value
            )

        if operator == "in":
            return OrFilterGroup((AttributesFilter(
                "Attributes/{_type}/any(att:att/Name eq '{_name}' and att/{_type}/Value {_operator} {_value})",
                attribute, "eq", v) for v in value))

        operators: dict = {
            "eq": "eq",
            "==": "eq",
            "le": "le",
            "<=": "le",
            "lt": "lt",
            "<": "lt",
            "ge": "ge",
            ">=": "ge",
            "gt": "gt",
            ">": "gt",
            "!=": "eq",
            "in": "eq"
        }

        return AttributesFilter(
            "Attributes/{_type}/any(att:att/Name eq '{_name}' and att/{_type}/Value {_operator} {_value})",
            attribute, operators[operator], value
        )


class Filter:

    def __init__(self, filter_format: str):
        self._format: str = filter_format

        self.__demo = "This value will be taken to format if needed"

    def __str__(self) -> str:
        formats = [fn for _, fn, _, _ in Formatter().parse(self._format) if fn is not None]
        formatters = {  # Passes attributes or from parsed result
            a: getattr(self, a) if not hasattr(self, f"{a}_parser") or not callable(getattr(self, f"{a}_parser"))
            else getattr(self, f"{a}_parser")()
            for a in formats
        }
        return self._format.format(**formatters)

    def dump(self) -> str:
        return str(self)

    def __demo_parser(self) -> str:
        """ This method will be called for __demo attribute if exists, and its value will be taken instead"""
        return self.__demo


TFilter = typing.TypeVar("TFilter", bound=Filter)


class Collection:
    def __init__(self, name: str):
        self.name: str = name


class CollectionFilter(Filter):
    def __init__(self, name: str):
        super().__init__("Collection/Name eq '{name}'")
        self.name = name


class Collections:
    SENTINEL_1 = Collection("SENTINEL-1")
    SENTINEL_2 = Collection("SENTINEL-2")
    SENTINEL_3 = Collection("SENTINEL-3")
    SENTINEL_5P = Collection("SENTINEL-5P")
    SENTINEL_6 = Collection("SENTINEL-6")
    SENTINEL_1_RTC = Collection("SENTINEL-1-RTC")
    LANDSAT_5 = Collection("LANDSAT-5")
    LANDSAT_7 = Collection("LANDSAT-7")
    LANDSAT_8 = Collection("LANDSAT-8")
    SMOS = Collection("SMOS")
    TERRAAQUA = Collection("TERRAAQUA")
    COP_DEM = Collection("COP-DEM")
    ENVISAT = Collection("ENVISAT")
    S2GLC = Collection("S2GLC")

    @staticmethod
    def is_in(*collections: Collection) -> TFilterGroup:
        return OrFilterGroup([CollectionFilter(c.name) for c in collections])

    @staticmethod
    def is_from(collection: Collection) -> TFilter:
        return CollectionFilter(collection.name)


class AttributesFilter(Filter):
    def __init__(self, filter_format: str, attribute: Attribute, operator: str,
                 value: typing.Union[str, int, float, datetime.datetime]):
        super().__init__(filter_format)

        self._attribute: Attribute = attribute

        self._name = attribute.name
        self._type = attribute.type

        self._operator = operator
        self._value = value

    def _value_parser(self) -> str:
        if isinstance(self._value, str):
            return f"'{self._value}'"
        return str(self._value)  # TODO: Test date types


class QueryConstructorFilterParser:
    def __init__(self, constructor: TQueryConstructor):
        self.filters: typing.Union[TFilterGroup, TFilter, None] = None
        self._constructor: TQueryConstructor = constructor

    def clear(self) -> TQueryConstructor:
        self.filters = None
        return self._constructor

    def where(self, *filters: typing.Union[TFilter, TFilterGroup]) -> TQueryConstructor:
        self.filters = FilterGroup(filters)
        return self._constructor

    def __str__(self) -> str:
        return str(self.filters)

    def __bool__(self) -> bool:
        return bool(self.filters)

    def __len__(self) -> int:
        return len(self.filters)

    def or_where(self, *filters: typing.Union[TFilter, TFilterGroup]) -> TQueryConstructor:
        self.filters = OrFilterGroup(filters)
        return self._constructor

    def where_not(self, *filters: typing.Union[TFilter, TFilterGroup]) -> TQueryConstructor:
        self.filters = NotFilter(FilterGroup(filters))
        return self._constructor


class PublicationDate(Filter):
    def __init__(self, string_format: str, date: datetime.datetime, end_date: datetime.datetime = None):
        super().__init__(string_format)
        self._date: datetime.datetime = date
        self._end_date: datetime.datetime = end_date

    def _date_parser(self) -> str:
        return self._date.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    def _end_date_parser(self) -> str:
        return self._end_date.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    @staticmethod
    def start(date: datetime.datetime) -> TFilter:
        return PublicationDate("PublicationDate ge {_date}", date)

    @staticmethod
    def span(start: datetime.datetime, end: datetime.datetime) -> TFilter:
        date = start
        return PublicationDate("PublicationDate ge {_date} and PublicationDate le {_end_date}", date, end)

    @staticmethod
    def end(date: datetime.datetime) -> TFilter:
        return PublicationDate("PublicationDate le {_date}", date)


class SensingDate(Filter):
    def __init__(self, string_format: str, date: datetime.datetime, end_date: datetime.datetime = None):
        super().__init__(string_format)
        self._date: datetime.datetime = date
        self._end_date: datetime.datetime = end_date

    def _date_parser(self) -> str:
        return self._date.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    @staticmethod
    def start(date: datetime.datetime) -> TFilter:
        return PublicationDate("ContentDate/Start gt {_date}", date)

    @staticmethod
    def span(start: datetime.datetime, end: datetime.datetime) -> TFilter:
        date = start
        return PublicationDate("ContentDate/Start ge {_date} and ContentDate/End le {_end_date}", date, end)

    @staticmethod
    def end(date: datetime.datetime) -> TFilter:
        return PublicationDate("ContentDate/End lt {_date}", date)


class Name(Filter):
    def __init__(self, string_format: str, name: str):
        super().__init__(string_format)
        self.name = name

    @staticmethod
    def has(characters: str) -> TFilter:
        return Name("contains(Name, '{name}')", characters)

    @staticmethod
    def starts_with(characters: str) -> TFilter:
        return Name("startswith(Name, '{name}')", characters)

    @staticmethod
    def ends_with(characters: str) -> TFilter:
        return Name("endswith(Name, '{name}')", characters)

    @staticmethod
    def exact(characters: str) -> TFilter:
        return Name("Name eq '{name}'", characters)


class Geographic(Filter):
    def __init__(self, geodata_point: Coordinates = None, geodata_polygon: tuple[Coordinates] = ()):
        super().__init__("OData.CSC.Intersects(area=geography'SRID=4326;{_geo_data}')")
        self._geodata_point: Coordinates = geodata_point
        self._geodata_polygon: tuple[Coordinates] = geodata_polygon

    def _geo_data_parser(self) -> str:
        if self._geodata_point:
            return f"POINT({self._geodata_point})"
        else:
            return f"POLYGON(({', '.join([str(g) for g in self._geodata_polygon])}))"

    @staticmethod
    def point(coordinates: Coordinates) -> TFilter:
        return Geographic(geodata_point=coordinates)

    @staticmethod
    def polygon(*coordinates: Coordinates) -> TFilter:
        return Geographic(geodata_polygon=coordinates)


class QueryFilter:
    name: Name = Name
    publication: PublicationDate = PublicationDate
    sensing: SensingDate = SensingDate
    geographic: Geographic = Geographic

    attribute: Attributes = Attributes
    collection: Collections = Collections

    @staticmethod
    def where(*filters: typing.Union[TFilter, TFilterGroup]) -> TFilterGroup:
        return FilterGroup(filters)

    @staticmethod
    def or_where(*filters: typing.Union[TFilter, TFilterGroup]) -> TFilterGroup:
        return OrFilterGroup(filters)

    @staticmethod
    def where_not(*filters: typing.Union[TFilter, TFilterGroup]) -> TFilter:
        return NotFilter(FilterGroup(filters))


class FilterGroup:
    def __init__(self, group: typing.Union[list, tuple][typing.Union[TFilter, TFilterGroup]]):
        self.group: list[TFilter] = group
        self._operator: str = " and "

    def __str__(self) -> str:
        return f"( {self._operator.join([str(g) for g in self.group])} )"


TFilterGroup = typing.TypeVar("TFilterGroup", bound=FilterGroup)


class OrFilterGroup(FilterGroup):
    def __init__(self, group: typing.Union[list, tuple][typing.Union[TFilter, TFilterGroup]]):
        super().__init__(group)
        self._operator = " or "


class NotFilter(Filter):
    def __init__(self, *negate_filter: typing.Union[list, tuple][typing.Union[TFilter, TFilterGroup]]):
        super().__init__("not {filter}")
        self.negate_filter = negate_filter

        self.filter = ""

    def filter_parser(self) -> str:
        return str(self.negate_filter)


class QueryConstructor:

    def __init__(self, client: Client):
        self.filter: QueryConstructorFilterParser = QueryConstructorFilterParser(self)
        self._client = client

        self._top: int = 0
        self._skip: int = 0
        self._count: bool = False
        self._expand: str = ""
        self._order_by: list[str] = []
        self._order_by_options: list[str] = []

    def _query_url(self) -> str:
        api_urls = {
            "creodias": "https://datahub.creodias.eu/odata/v1/",
            "codede": os.environ.get("CODEDE_TEST_URL")  # TODO: Update after release
        }

        return api_urls[self._client._source]

    def _parse_params(self) -> dict:
        params = {}
        if self._top:
            params.update({"$top": self._top})
        if self._skip:
            params.update({"$skip": self._skip})
        if self._count:
            params.update({"$count": self._count})
        if self._expand:
            params.update({"$expand": self._expand})
        if self._order_by:
            params.update({"$orderby": f"{self._order_by[0]} {self._order_by[1]}"})

        if self.filter:
            params.update({"$filter": str(self.filter)})
        return params

    def top(self, number: int) -> TQueryConstructor:
        if not 0 <= number <= 1000:
            raise errors.InvalidNumberError(number, [0, 1000])
        self._top = number
        return self

    def skip(self, number: int) -> TQueryConstructor:
        if not 0 <= number <= 10000:
            raise errors.InvalidNumberError(number, [0, 10000])
        self._skip = number
        return self

    def count(self, count: bool) -> TQueryConstructor:
        self._count = count
        return self

    def expand(self, category: Literal["Attributes"]) -> TQueryConstructor:
        self._expand = category
        return self

    def order_by(self, argument: str,
                 direction: Literal["asc", "desc"] = "asc") -> TQueryConstructor:
        if argument not in self._order_by_options:
            errors.InvalidFromSelectionError(argument, self._order_by_options)
            self._order_by = [argument, direction]
        return self


TQueryConstructor = typing.TypeVar("TQueryConstructor", bound=QueryConstructor)


class OWorkflowsQueryConstructor(QueryConstructor):
    def __init__(self, client: Client):
        super().__init__(client)

        self.__expand: str = ""
        self.__order_by: list[str] = []

        self.__top: int = 0
        self.__skip: int = 0
        self.__count: bool = False

        self._order_by_options: list = []

    async def get(self) -> typing.Optional[ODataWorkflowsCollection]:
        params = self._parse_params()
        url = "https://datahub.creodias.eu/odata/v1/Workflows"
        response, result = await self._client.http.request("get", url, params=params)

        if not response.ok:
            return None

        collection = ODataWorkflowsCollection(self._client, response, result)
        return collection


class OProductsQueryConstructor(QueryConstructor):
    def __init__(self, client: Client):
        super().__init__(client)

        self._order_by_options: list[str] = ["ContentDate/Start", "ContentDate/End", "PublicationDate", "ModificationDate"]

    async def get(self, *ids: str) -> typing.Optional[OProductsCollection]:
        data = {}
        params = {}

        if len(ids) > 1:
            url = "https://datahub.creodias.eu/odata/v1/Products/OData.CSC.FilterList"
            data = {
                "FilterProducts": [{"Name": nid for nid in ids}]
            }
            method = "post"
        elif len(ids) == 1:
            url = f"https://datahub.creodias.eu/odata/v1/Products({ids[0]})"
            method = "get"
        else:
            params = self._parse_params()
            url = "https://datahub.creodias.eu/odata/v1/Products"
            method = "get"
        response, result = await self._client.http.request(method, url, params=params, data=data)

        if not response.ok:
            return None

        collection = OProductsCollection(self._client, response, result)
        return collection

    async def nodes(self, product_id: str) -> typing.Optional[OProductNodesCollection]:
        data, response = await self._client.http.request("get", f"https://datahub.creodias.eu/odata/v1/Products({product_id})/Nodes")

        if not response.ok:
            return None

        return OProductNodesCollection(self._client, data, response)


"""

class OProductsQueryConstructor(QueryConstructor):
    def __init__(self, client: Client):
        super().__init__(client)

        self.__top: int = 0
        self.__skip: int = 0
        self.__count = False
        self.__expand: str = ""
        self.__order_by: list[str] = ["", "asc"]

        self.__logic_arguments: list[OProductsQueryConstructorLogicArgument] = []

    @property
    def __api_url(self):
        api_urls = {
            "creodias": "https://datahub.creodias.eu/odata/v1/",
            "codede": os.environ.get("CODEDE_TEST_URL")  # TODO: Update after release
        }
        return api_urls[self._client.source]

    def url(self, endpoint: str, params: str) -> str:
        url: str = self.__api_url + endpoint + params
        return url

    @property
    def and_(self) -> OProductsQueryConstructorLogicArgument:
        if not self.__logic_arguments:
            raise ValueError("There are not any other arguments, use filter method instead.")
        argument = OProductsQueryConstructorLogicArgument(self, "and")
        self.__logic_arguments.append(argument)
        return argument

    @property
    def filter(self) -> OProductsQueryConstructorLogicArgument:
        if self.__logic_arguments:
            raise ValueError("There are other arguments, use logic operator instead.")
        argument = OProductsQueryConstructorLogicArgument(self, "")
        self.__logic_arguments.append(argument)
        return argument

    @property
    def or_(self) -> OProductsQueryConstructorLogicArgument:
        if not self.__logic_arguments:
            raise ValueError("There are not any other arguments, use filter method instead.")
        argument = OProductsQueryConstructorLogicArgument(self, "or")
        self.__logic_arguments.append(argument)
        return argument

    def top(self, number: int) -> OProductsQueryConstructor:
        if not 0 <= number <= 1000:
            raise errors.InvalidNumberError(number, [0, 1000])
        self.__top = number
        return self

    def skip(self, number: int) -> OProductsQueryConstructor:
        if not 0 <= number <= 10000:
            raise errors.InvalidNumberError(number, [0, 10000])
        self.__top = number
        return self

    def count(self, count: bool) -> OProductsQueryConstructor:
        self.__count = count
        return self

    def expand(self, category: Literal["Attributes"]) -> OProductsQueryConstructor:
        self.__expand = category
        return self

    def order_by(self, argument: Literal["ContentDate/Start", "ContentDate/End", "PublicationDate", "ModificationDate"],
                 direction: Literal["asc", "desc"] = "asc") -> OProductsQueryConstructor:
        if argument not in ["ContentDate/Start", "ContentDate/End", "PublicationDate", "ModificationDate"]:
            errors.InvalidFromSelectionError(argument, ["ContentDate/Start", "ContentDate/End", "PublicationDate",
                                                        "ModificationDate"])
            self.__order_by = [argument, direction]
        return self

    def __parse_filter_params(self) -> str:
        final: str = ""
        for argument in self.__logic_arguments:
            final += str(argument)
        return final

    def __parse_order_by_param(self) -> str:
        if not self.__order_by[0]:
            return ""
        final: str = f"{self.__order_by[0]} {self.__order_by[1]}"
        return final

    def __parse_query_params(self, parameters: dict[str, typing.Any]) -> str:
        final: str = ""
        first: bool = True
        for param, value in parameters.items():
            if value:
                if first:
                    final += "?"
                else:
                    final += "&"
                first = False
                param = param if not param == "order_by" else "orderby"

                if isinstance(value, str):
                    value = value.strip()
                final += f"${param}={value}"

        return final

    # Executors ->

    async def get(self, parameters: dict = {}) -> typing.Optional[OProductsCollection]:
        params: dict = {
            "filter": self.__parse_filter_params(),
            "order_by": self.__parse_order_by_param(),
            "top": self.__top,
            "skip": self.__skip,
            "count": self.__count,
            "expand": self.__expand
        }

        params.update(parameters)

        url = self.url("Products", self.__parse_query_params(params))
        result = await self._client.fetch("get", url=url)

        if not result.ok:
            return None

        return OProductsCollection(self._client, result.json(), result)

    async def id(self, product_id: str, expand: Literal["Attributes"] = None) -> typing.Optional[OProductsCollection]:
        url = self.url(f"Products({product_id})", self.__parse_query_params({"expand": expand}))
        result = await self._client.fetch("get", url=url)

        if not result.ok:
            return None

        return OProductsCollection(self._client, result.json(), result)

    async def names(self, product_names: list[str]) -> typing.Optional[OProductsCollection]:
        url = self.url("Products/OData.CSC.FilterLists", self.__parse_query_params({}))
        result = await self._client.fetch("post", url=url, data={
            "FilterProducts": [{"Name": name} for name in product_names]
        })

        if not result.ok:
            return None

        return OProductsCollection(self._client, result.json(), result)


class OProductsQueryConstructorLogicArgument:
    def __init__(self, constructor: OProductsQueryConstructor, operator: Literal["and", "", "or"]):

        self.__constructor: OProductsQueryConstructor = constructor
        self.__operator: str = operator

        self._attribute: bool = False
        self._attribute_name: str = ""
        self._attribute_operator: str = ""
        self._attribute_value: str | float | int | datetime.datetime = ""
        self._attribute_raw: str = ""

        self._geography_area: str = "geography'SRID=4326"

        self._geography_point: bool = False
        self._geography_point_x: float = 0.0
        self._geography_point_y: float = 0.0

        self._geography_polygon: bool = False
        self._geography_polygon_list: list[ODataCoordinate] = []

        self._sensing_date: bool = False
        self._sensing_date_start: typing.Optional[datetime.datetime] = None
        self._sensing_date_end: typing.Optional[datetime.datetime] = None

        self._publication_date: bool = False
        self._publication_date_start: typing.Optional[datetime.datetime] = None
        self._publication_date_end: typing.Optional[datetime.datetime] = None

        self._collection: bool = False
        self._collection_name: str = ""

        self._name_is: bool = False
        self._name_is_value: str = ""

        self._name_has: bool = False
        self._name_has_value: str = ""

        self._name_starts_with: bool = False
        self._name_starts_with_value: str = ""

        self._name_ends_with: bool = False
        self._name_ends_with_value: str = ""

    def __check_lock(self) -> None:
        if self.type:
            raise errors.ParameterReadOnlyError("This parameter was set before and can not be changed.")

    @property
    def type(self) -> typing.Optional[str]:
        if self._attribute:
            return "attribute"
        elif self._geography_point:
            return "geographic_point"
        elif self._geography_polygon:
            return "geographic_polygon"
        elif self._sensing_date:
            return "sensing_date"
        elif self._publication_date:
            return "publication_date"
        elif self._collection:
            return "collection"
        elif self._name_is:
            return "name_is"
        elif self._name_has:
            return "name_has"
        elif self._name_starts_with:
            return "name_starts_with"
        elif self._name_ends_with:
            return "name_ends_with"
        return None

    @property
    def not_(self) -> OProductsQueryConstructorLogicArgument:
        self.__operator += " not"
        return self

    def attribute(self, name: Literal["authority", "timeliness", "coordinates", "orbitNumber", "productType", "sliceNumber",
                                      "productClass", "endingDateTime", "orbitDirection", "operationalMode",
                                      "processingLevel", "swathIdentifier", "beginningDateTime", "platformShortName",
                                      "spatialResolution", "instrumentShortName", "relativeOrbitNumber",
                                      "polarisationChannels", "platformSerialIdentifier"],
                  operator: Literal["eq", "le", "lt", "ge", "gt"], value: str | int | float | datetime.datetime
                  ) -> OProductsQueryConstructor:
        self.__check_lock()

        self._attribute = True
        self._attribute_name = name
        self._attribute_operator = operator
        self._attribute_value = value

        return self.__constructor

    def raw_attributes(self, raw) -> OProductsQueryConstructor:
        self.__check_lock()

        self._attribute_raw = raw

        return self.__constructor

    def geographic_polygon(self, polygon: list[list[float, float]]) -> OProductsQueryConstructor:
        self.__check_lock()

        self._geography_polygon = True
        for coordinate in polygon:
            self._geography_polygon_list.append(ODataCoordinate(coordinate[0], coordinate[1]))

        return self.__constructor

    def geographic_point(self, x: float, y: float) -> OProductsQueryConstructor:
        self.__check_lock()

        self._geography_point = True
        self._geography_point_x = x
        self._geography_point_y = y

        return self.__constructor

    def sensing_date(self, start: typing.Optional[datetime.datetime] = None, end: typing.Optional[datetime.datetime] = None) -> OProductsQueryConstructor:
        self.__check_lock()

        self._sensing_date = True
        self._sensing_date_start = start
        self._sensing_date_end = end

        return self.__constructor

    def publication_date(self, start: typing.Optional[datetime.datetime] = None, end: typing.Optional[datetime.datetime] = None) -> OProductsQueryConstructor:
        self.__check_lock()

        self._publication_date = True
        self._publication_date_start = start
        self._publication_date_end = end

        return self.__constructor

    def collection(self, name: typing.Literal["SENTINEL-1", "SENTINEL-2", "SENTINEL-3", "SENTINEL-5P", "SENTINEL-6",
                                              "SENTINEL-1-RTC", "LANDSAT-5", "LANDSAT-7", "LANDSAT-8", "SMOS",
                                              "TERRAAQUA", "COP-DEM", "ENVISAT", "S2GLC"]) -> OProductsQueryConstructor:
        self.__check_lock()

        self._collection = True
        self._collection_name = name

        return self.__constructor

    def name_is(self, name: str) -> OProductsQueryConstructor:
        self.__check_lock()

        self._name_is = True
        self._name_is_value = name

        return self.__constructor

    def name_has(self, name: str) -> OProductsQueryConstructor:
        self.__check_lock()

        self._name_has = True
        self._name_has_value = name

        return self.__constructor

    def name_starts_with(self, name: str) -> OProductsQueryConstructor:
        self.__check_lock()

        self._name_starts_with = True
        self._name_starts_with_value = name

        return self.__constructor

    def name_ends_with(self, name: str) -> OProductsQueryConstructor:
        self.__check_lock()

        self._name_ends_with = True
        self._name_ends_with_value = name

        return self.__constructor

    def __str__(self):
        final: str = ""
        if self.__operator:
            final = f"{self.__operator} "
        match self.type:
            case "attribute":
                final += self.__parse_attribute()
            case "geographic_point":
                final += (f"OData.CSC.Intersects(area={self._geography_area};"
                          f"POINT({self._geography_point_x} {self._geography_point_y})')")
            case "geographic_polygon":
                final += (f"OData.CSC.Intersects(area={self._geography_area};"
                          f"POLYGON(({','.join([str(point) for point in self._geography_polygon_list])}))')")
            case "sensing_date":
                if self._sensing_date_start:
                    final += f"ContentDate/Start gt {TimeConverter.to_str(self._sensing_date_start)}"
                    if self._sensing_date_end:
                        final += " and "
                if self._sensing_date_end:
                    final += f"ContentDate/End lt {TimeConverter.to_str(self._sensing_date_end)}"
            case "publication_date":
                if self._sensing_date_start:
                    final += f"PublicationDate ge {TimeConverter.to_str(self._sensing_date_start)}"
                    if self._sensing_date_end:
                        final += " and "
                if self._sensing_date_end:
                    final += f"PublicationDate le {TimeConverter.to_str(self._sensing_date_end)}"
            case "collection":
                final += f"Collection/Name eq '{self._collection_name}'"
            case "name_is":
                final += f"Name eq '{self._name_is_value}'"
            case "name_has":
                final += f"contains(Name,'{self._name_has_value}')"
            case "name_starts_with":
                final += f"startswith(Name,'{self._name_starts_with_value}')"
            case "name_ends_with":
                final += f"endswith(Name,'{self._name_ends_with_value}')"

        final += " "
        return final

    def __attribute_value_parser(self) -> str:
        value = self._attribute_value
        if isinstance(value, str):
            return f"'{value}'"
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, datetime.datetime):
            return TimeConverter.to_str(value)

    def __parse_attribute(self) -> str:
        str_format: str = "Attributes/OData.CSC.{attribute_type}/any(att:att/Name eq '{attribute_name}' and att/OData.CSC.{attribute_type}/Value eq {attribute_value})"

        types: dict[str, str] = {
            "str": "StringAttribute",
            "float": "DoubleAttribute",
            "int": "IntegerAttribute",
            "datetime.datetime": "DateTimeOffsetAttribute"  # TODO: EXTRA ATTENTION TO THIS ATTRIBUTE ( UNCLEAR )
        }

        parsed = str_format.format(attribute_type=types[type(self._attribute_value).__name__],
                                   attribute_name=self._attribute_name,
                                   attribute_value=self.__attribute_value_parser())

        return parsed


"""
