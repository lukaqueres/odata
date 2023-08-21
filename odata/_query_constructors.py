from __future__ import annotations

import os
import datetime
from dataclasses import dataclass

import typing
from typing import Literal
import logging

if typing.TYPE_CHECKING:
    from odata.client import Client

import odata.errors as errors
from odata._types import ODataCoordinate, OProductsCollection
from odata._helpers import TimeConverter


class QueryConstructor:
    def __init__(self, client: Client):
        self._client = client


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
