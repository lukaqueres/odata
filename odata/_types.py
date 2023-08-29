from __future__ import annotations

import datetime
from dataclasses import dataclass

import typing
import logging
import aiohttp

if typing.TYPE_CHECKING:
    from odata.client import Client

import odata.errors as errors

from odata._helpers import TimeConverter

logger = logging.getLogger("odata")

_timeconverter = TimeConverter


@dataclass
class ODataCoordinate:
    x: float
    y: float

    def __str__(self):
        return f"{self.x} {self.y}"

"""

class General:

    def __init__(self, client: Client):
        self._client: Client = client


class ProductionOrder(General):
    def __init__(self, client):
        super().__init__(client)

    async def get(self, order_id: int) -> typing.Optional[ODataProductionOrderResponse]:
        return await ODataProductionOrder.fetch(self._client, order_id)

    async def new(self, name: str, workflow_id: str, workflow_name: str, workflow_version: str,
                  workflow_options: list[dict], input_product_reference: InputProductReferenceModel, priority: int = 0,
                  notification_endpoint: str = "", notification_endpoint_username: str = "",
                  notification_endpoint_password: str = "") -> typing.Optional[ODataProductionOrderResponse]:
        return await ODataProductionOrder.new(client=self._client, name=name, workflow_id=workflow_id,
                                              workflow_name=workflow_name,
                                              workflow_version=workflow_version, workflow_options=workflow_options,
                                              input_product_reference=input_product_reference, priority=priority,
                                              notification_endpoint=notification_endpoint,
                                              notification_endpoint_username=notification_endpoint_username,
                                              notification_endpoint_password=notification_endpoint_password
                                              )

    async def estimate(self, name: str, workflow_id: str, workflow_name: str, workflow_version: str,
                       workflow_options: list[dict], input_product_reference: InputProductReferenceModel,
                       priority: int = 0,
                       notification_endpoint: str = "", notification_endpoint_username: str = "",
                       notification_endpoint_password: str = "") -> typing.Optional[ProductionOrderCostEstimate]:
        return await ODataProductionOrder.estimate(client=self._client, name=name, workflow_id=workflow_id,
                                                   workflow_name=workflow_name,
                                                   workflow_version=workflow_version, workflow_options=workflow_options,
                                                   input_product_reference=input_product_reference, priority=priority,
                                                   notification_endpoint=notification_endpoint,
                                                   notification_endpoint_username=notification_endpoint_username,
                                                   notification_endpoint_password=notification_endpoint_password
                                                   )


class Type:
    def __init__(self, client: Client):
        self._client = client


class ODataProductionOrderCollection(Type):

    def __init__(self, client: Client, data: dict):
        super().__init__(client)
        self.context = data["@odata.context"]
        self.next_link = data.get("@odata.nextLink", "")
        self.count = data.get("@odata.count", 0)
        self.list: tuple[ODataProductionOrder] = tuple(ODataProductionOrder(client, value) for value in data["value"])
        self.__current = 0

    @staticmethod
    async def fetch(client: Client, query_filter: str = "", order_by: str = "", count: bool = False,
                    top: int = 1000, skip: int = 0) -> typing.Optional[ODataProductionOrderCollection]:

        if not 0 <= top <= 1000:
            raise ValueError("Invalid top value, must be between 0 and 1000")
        if not skip >= 0:
            raise ValueError("Skip value must equal or be higher than 0")
        data: dict = {
            "$filter": query_filter,
            "$orderby": order_by,
            "$count": count,
            "$top": top,
            "$skip": skip
        }

        response = await client.fetch("get", "ProductionOrders", params=data)

        if not response.ok:
            return None

        result = response.json()

        order_collection = ODataProductionOrderCollection(client, result)

        return order_collection

    def __getitem__(self, item):
        return self.list[item]

    def __len__(self):
        return len(self.list)

    def __iter__(self):
        self.__current = 0
        return self

    def __next__(self):
        if self.__current >= len(self.list):
            self.__current = 0
            raise StopIteration

        current = self.list[self.__current]
        self.__current += 1
        return current

    def __nonzero__(self) -> bool:
        return bool(self.list)

    async def next(self) -> typing.Optional[ODataProductionOrderCollection]:
        if not self.next_link:
            return None

        response = await self._client.fetch("get", url=self.next_link)

        result = response.json()

        if not response.ok:
            return None

        return ODataProductionOrderCollection(self._client, result)


class ODataProductionOrderResponse:
    def __init__(self, client, data):
        self.context: str = data["@odata.context"]
        self.next_link: str = data.get("@odata.nextLink", "")
        self.count: int = data.get("@odata.count", 0)

        self.order: ODataProductionOrder(client, data["value"])


class ODataProductionOrder(Type):
    def __init__(self, client: Client, data: dict):
        super().__init__(client)

        self.id: str = data["Id"]
        self.status: str = data["Status"]
        self.status_message: str = data["StatusMessage"]
        self.submission_date: datetime.datetime = _timeconverter.to_date(data["SubmissionDate"])
        self.name: str = data.get("Name")
        self.estimated_date: datetime.datetime = _timeconverter.to_date(data.get("EstimatedDate"))
        self.input_product_reference: InputProductReferenceModel = InputProductReferenceModel(
            data["InputProductReference"].get("Reference", ""),
            ContentDateModel(
                data["InputProductReference"]["ContentDate"]["Start"],
                data["InputProductReference"]["ContentDate"]["End"]
            )
        )
        self.workflow_options: list[WorkflowOption] = [
            WorkflowOption(
                i["Name"],
                i["Value"]
            )
            for i in data["WorkflowOptions"]
        ]
        self.workflow_name: str = data["WorkflowName"]
        self.workflow_id: str = data.get("WorkflowId", "")
        self.priority: int = data.get("Priority", 0)
        self.notification_endpoint: str = data.get("NotificationEndpoint", "")
        self.notification_endpoint_username: str = data.get("NotificationEpUsername", "")

    @staticmethod
    async def fetch(client: Client, order_id: int) -> typing.Optional[ODataProductionOrderResponse]:
        response = await client.fetch("get", f"ProductionOrder({order_id})/Product")
        result = response.json()

        if not response.ok:
            return None

        return ODataProductionOrderResponse(client, result)

    @property
    async def details(self) -> typing.Optional[OdataOrderResult]:
        response = await self._client.fetch("get", f"ProductionOrder({self.id})/Product")
        result = response.json()

        if not response.ok:
            return None

        details = OdataOrderResult(
            **result
        )

        return details

    @property
    async def value(self) -> typing.Optional[str]:
        response = await self._client.fetch("get", f"ProductionOrder({self.id})/Product/$value")

        if not response.ok:
            return None

        result = response.json()

        return result

    async def cancel(self) -> typing.Optional[ODataProductionOrderResponse]:
        response = await self._client.fetch("post", f"ProductionOrder({self.id})/OData.CSC.Cancel")
        result = response.json()

        if not response.ok:
            return None

        return ODataProductionOrderResponse(self._client, result)

    @staticmethod
    async def new(client, name: str, workflow_id: str, workflow_name: str, workflow_version: str,
                  workflow_options: list[dict], input_product_reference: InputProductReferenceModel, priority: int = 0,
                  notification_endpoint: str = "", notification_endpoint_username: str = "",
                  notification_endpoint_password: str = "") -> typing.Optional[ODataProductionOrderResponse]:

        conv_input_product_reference: dict = {
            "Reference": input_product_reference.reference,
            "ContentDate": {
                "Start": _timeconverter.to_str(input_product_reference.content_date.start),
                "End": _timeconverter.to_str(input_product_reference.content_date.end)
            }
        }

        data = NewProcessingOrderData(**{
            "Name": name,
            "WorkflowId": workflow_id,
            "WorkflowName": workflow_name,
            "WorkflowVersion": workflow_version,
            "WorkflowOptions": workflow_options,
            "InputProductReference": conv_input_product_reference,
            "Priority": priority,
            "NotificationEndpoint": notification_endpoint,
            "NotificationEpUsername": notification_endpoint_username,
            "NotificationEpPassword": notification_endpoint_password,
        })

        response = await client.fetch("post", f"ProductionOrder/OData.CSC.Order", data=data)
        result = response.json()

        if not response.ok:
            return None

        return ODataProductionOrderResponse(client, result)

    @staticmethod
    async def estimate(client, name: str, workflow_id: str, workflow_name: str, workflow_version: str,
                       workflow_options: list[dict], input_product_reference: InputProductReferenceModel,
                       priority: int = 0,
                       notification_endpoint: str = "", notification_endpoint_username: str = "",
                       notification_endpoint_password: str = "") -> typing.Optional[ProductionOrderCostEstimate]:

        conv_input_product_reference: dict = {
            "Reference": input_product_reference.reference,
            "ContentDate": {
                "Start": _timeconverter.to_str(input_product_reference.content_date.start),
                "End": _timeconverter.to_str(input_product_reference.content_date.end)
            }
        }

        data = NewProcessingOrderData(**{
            "Name": name,
            "WorkflowId": workflow_id,
            "WorkflowName": workflow_name,
            "WorkflowVersion": workflow_version,
            "WorkflowOptions": workflow_options,
            "InputProductReference": conv_input_product_reference,
            "Priority": priority,
            "NotificationEndpoint": notification_endpoint,
            "NotificationEpUsername": notification_endpoint_username,
            "NotificationEpPassword": notification_endpoint_password,
        })

        response = await client.fetch("post", f"ProductionOrder/OData.CSC.Order", data=data)
        result = response.json()

        if not response.ok:
            return None

        return ProductionOrderCostEstimate(client, data, result["tokens"])


@dataclass
class OdataOrderResult:
    processed_name: str = ""
    output_uuid: str = ""
    processed_size: int = 0
    processing_metadata: dict = field(default_factory=lambda: {})


@dataclass
class InputProductReferenceModel:
    reference: str
    content_date: ContentDateModel


@dataclass
class ContentDateModel:
    start: datetime.datetime
    end: datetime.datetime


@dataclass
class WorkflowOption:
    name: str
    value: str


class ProductionOrderCostEstimate:
    def __init__(self, client, order_data, result):
        self._client: Client = client
        self.__order_data: NewProcessingOrderData = order_data
        self.tokens: int = result["tokens"]

    async def order(self) -> typing.Optional[ODataProductionOrderResponse]:
        data = self.__order_data

        input_product_reference = InputProductReferenceModel(
            data.InputProductReference.get("Reference", ""),
            ContentDateModel(
                data.InputProductReference["ContentDate"]["Start"],
                data.InputProductReference["ContentDate"]["End"]
            )
        )

        return await ODataProductionOrder.new(self._client, name=data.Name, workflow_id=data.WorkflowId,
                                              workflow_name=data.WorkflowName, workflow_version=data.WorkflowVersion,
                                              workflow_options=data.WorkflowOptions,
                                              input_product_reference=input_product_reference, priority=data.Priority,
                                              notification_endpoint=data.NotificationEndpoint,
                                              notification_endpoint_username=data.NotificationEpUsername,
                                              notification_endpoint_password=data.NotificationEpPassword)


@dataclass
class NewProcessingOrderData:
    WorkflowId: str
    WorkflowName: str
    WorkflowVersion: str
    InputProductReference: dict
    WorkflowOptions: list[dict]
    Priority: int
    NotificationEndpoint: str
    NotificationEpUsername: str
    NotificationEpPassword: str
    Name: str


class ODataWorkflowsCollection(Type):
    def __init__(self, client: Client, data: dict):
        super().__init__(client)
        self.context: str = data["@odata.context"]
        self.next_link: str = data.get("@odata.nextLink", "")
        self.count: int = data.get("@odata.count", 0)
        self.list: tuple[ODataWorkflow] = tuple([ODataWorkflow(client, d) for d in data.get("value", [])])

        self.__current: int = 0

    @staticmethod
    async def fetch(client: Client, expand, query_filter: str, order_by: str, count: bool = False, top: int = 1000,
                    skip: int = 0) -> typing.Optional[ODataWorkflowsCollection]:
        data: dict = {
            "$expand": expand,
            "$filter": query_filter,
            "$orderby": order_by,
            "$count": count,
            "$top": top,
            "$skip": skip
        }
        response = await client.fetch("get", f"Workflows", params=data)  # TODO: Fix 422 - UnProcessable Entity error
        result = response.json()

        if not response.ok:
            return None

        return ODataWorkflowsCollection(client, result)

    def __getitem__(self, item):
        return self.list[item]

    def __len__(self):
        return len(self.list)

    def __iter__(self):
        self.__current = 0
        return self

    def __next__(self):
        if self.__current >= len(self.list):
            self.__current = 0
            raise StopIteration

        current = self.list[self.__current]
        self.__current += 1
        return current

    def __nonzero__(self) -> bool:
        return bool(self.list)

    async def next(self) -> typing.Optional[ODataWorkflowsCollection]:
        if not self.next_link:
            return None

        response = await self._client.fetch("get", url=self.next_link)

        result = response.json()

        if not response.ok:
            return None

        return ODataWorkflowsCollection(self._client, result)


class ODataWorkflow(Type):
    def __init__(self, client: Client, data: dict):
        super().__init__(client)

        self.id: str = data["Id"]
        self.uuid: str = data.get("Uuid", "")
        self.name: str = data["Name"]
        self.display_name: str = data["DisplayName"]
        self.documentation: str = data.get("Documentation", "")
        self.description: str = data.get("Description", "")
        self.input_product_type: str = data.get("InputProductTypes", "")
        self.input_product_types: list[str] = data["InputProductsTypes"]
        self.output_product_type: str = data.get("OutputProductType", "")
        self.output_product_types: list[str] = data["OutputProductTypes"]
        self.version: str = data.get("WorkflowVersion", "")
        self.options: list[ODataWorkflowOption] = [ODataWorkflowOption(o["Name"], o.get("Description"), o["Type"],
                                                                       o.get("Default"), o.get("value"), o["Required"]
                                                                       ) for o in data.get("WorkflowOptions", [])]
        self.custom_input_source: bool = True


@dataclass
class ODataWorkflowOption:
    name: str
    description: str
    type: str
    default: str
    value: str
    required: bool = True


class EOProducts(General):
    def __init__(self, client):
        super().__init__(client=client)

    async def get(self, product_id: str) -> typing.Optional[EOProduct]:
        return await EOProduct.fetch(self._client, product_id)


class EOProductsCollection(Type):
    def __init__(self, client, data):
        super().__init__(client=client)

        self.context: str = data["@odata.context"]
        self.next_link: str = data.get("@odata.nextLink", "")
        self.count: int = data.get("@odata.count", 0)

        self.list: list[EOProduct] = [EOProduct(client, d) for d in data["value"]]

        self.__current: int = 0

    @staticmethod
    async def fetch(client: Client, query_filter: str, order_by: str, top: int = 1000, skip: int = 0,
                    count: bool = False, expand: str = "") -> typing.Optional[EOProductsCollection]:

        data: dict = {
            "$filter": query_filter,
            "$orderby": order_by,
            "$top": top,
            "$skip": skip,
            "$count": count,
            "expand": expand
        }

        response = await client.fetch("get", f"Products", params=data)
        result = response.json()

        if not response.ok:
            return None

        return EOProductsCollection(client, result)

    def __getitem__(self, item):
        return self.list[item]

    def __len__(self):
        return len(self.list)

    def __iter__(self):
        self.__current = 0
        return self

    def __next__(self):
        if self.__current >= len(self.list):
            self.__current = 0
            raise StopIteration

        current = self.list[self.__current]
        self.__current += 1
        return current

    def __nonzero__(self) -> bool:
        return bool(self.list)

    async def next(self) -> typing.Optional[EOProductsCollection]:
        if not self.next_link:
            return None

        response = await self._client.fetch("get", url=self.next_link)

        result = response.json()

        if not response.ok:
            return None

        return EOProductsCollection(self._client, result)


class EOProduct(Type):
    def __init__(self, client: Client, data: dict):
        super().__init__(client)

        self.context: str = data.get("@odata.context", "")

        if "value" in data.keys():
            data = data["value"][0]

        self.media_type: str = data["@odata.mediaContentType"]
        self.id: str = data["Id"]
        self.name: str = data["Name"]
        self.content_type: str = data.get("ContentType")
        self.content_length: int = data.get("ContentLength", 0)
        self.origin_date: datetime.date = TimeConverter.to_date(data["OriginDate"])
        self.publication_date: datetime.date = TimeConverter.to_date(data["PublicationDate"])
        self.modification_date: datetime.date = TimeConverter.to_date(data["ModificationDate"])
        self.online: bool = data.get("Online", False)
        self.eviction_date: datetime.date = TimeConverter.to_date(data["EvictionDate"])
        self.s3_path: str = data["S3Path"]
        self.checksum: list = data.get("Checksum", [])
        self.content_date: EOProductContentDateModel = EOProductContentDateModel(
            TimeConverter.to_date(data["ContentDate"].get("Start", "")),
            TimeConverter.to_date(data["ContentDate"].get("End", ""))
        )
        self.footprint: str = data["Footprint"]
        self.geo_footprint: EOProductGeoFootprintModel = EOProductGeoFootprintModel(
            data["GeoFootprint"]["type"],
            [ODataCoordinate(c[0], c[1]) for c in data["GeoFootprint"]["coordinates"][0]]
        )

    @staticmethod
    async def fetch(client: Client, product_id: str) -> typing.Optional[EOProduct]:
        response = await client.fetch("get", f"Products({product_id})")
        result = response.json()

        if not response.ok:
            return None

        return EOProduct(client, result)

    @property
    async def nodes(self) -> typing.Optional[EOProductNodesCollection]:
        response = await self._client.fetch("get", f"Products({self.id})/Nodes")
        result = response.json()

        if not response.ok:
            return None

        return EOProductNodesCollection(self._client, result)


@dataclass
class EOProductContentDateModel:
    start: datetime.date
    end: datetime.date


@dataclass
class EOProductGeoFootprintModel:
    type: str
    coordinates: list[ODataCoordinate]


@dataclass
class EOCoordinate:
    x: int
    y: int


class EOProductNodesCollection(Type):
    def __init__(self, client, data):
        super().__init__(client=client)

        self.list: list[EOProductNode] = [EOProductNode(client, d) for d in data["result"]]

        self.__current: int = 0

    def __getitem__(self, item):
        return self.list[item]

    def __len__(self):
        return len(self.list)

    def __iter__(self):
        self.__current = 0
        return self

    def __next__(self):
        if self.__current >= len(self.list):
            self.__current = 0
            raise StopIteration

        current = self.list[self.__current]
        self.__current += 1
        return current

    def __nonzero__(self) -> bool:
        return bool(self.list)


class EOProductNode(Type):
    def __init__(self, client, data):
        super().__init__(client=client)

        self.id: str = data["Id"]
        self.name: str = data["Name"]
        self.content_length: int = data.get("ContentLength", 0)
        self.children_number: int = data.get("ChildrenNumber", 0)
        self.nodes_uri: EOProductNodeNodesModel = EOProductNodeNodesModel(
            data["Nodes"]["uri"]
        )

    @property
    async def nodes(self) -> typing.Optional[EOProductNodesCollection]:
        response = await self._client.fetch("get", self.nodes_uri.uri)
        result = response.json()

        if not response.ok:
            return None

        return EOProductNodesCollection(self._client, result)


@dataclass
class EOProductNodeNodesModel:
    uri: str

"""


class ODataObject:
    def __init__(self, client: Client, response: aiohttp.ClientResponse):
        self._client: Client = client

        self._response: aiohttp.ClientResponse = response


class ODataObjectCollection(ODataObject):
    def __init__(self, client: Client, response: aiohttp.ClientResponse):
        super().__init__(client, response)

        self.items: list[typing.Type[ODataObject]] = []

        self._current = 0

    def __getitem__(self, item):
        return self.items[item]

    def __len__(self):
        return len(self.items)

    def __iter__(self):
        self._current = 0
        return self

    def __next__(self):
        if self._current >= len(self.items):
            self._current = 0
            raise StopIteration

        current = self.items[self._current]
        self._current += 1
        return current

    def __nonzero__(self) -> bool:
        return bool(self.items)


class OProductsCollection(ODataObjectCollection):
    def __init__(self, client: Client, response: typing.Optional[aiohttp.ClientResponse] = None, data: dict = {}):
        super().__init__(client, response)

        self.context: str = data.get("@odata.context", "")
        self.next_link: str = data.get("@odata.nextLink", "")
        self.count: int = data.get("@odata.count", 0)

        self.items: list[OProduct] = [OProduct(client, d, response) for d in data["value"]]


class OProduct(ODataObject):
    """
        Single product record.

    """

    def __init__(self, client: Client, data: dict, response: typing.Optional[aiohttp.ClientResponse] = None):
        super().__init__(client, response)
        self.media_type: str = data["@odata.mediaContentType"]
        self.id: str = data["Id"]
        self.name: str = data["Name"]
        self.content_type: str = data.get("ContentType")
        self.content_length: int = data.get("ContentLength", 0)
        self.origin_date: datetime.date = TimeConverter.to_date(data["OriginDate"])
        self.publication_date: datetime.date = TimeConverter.to_date(data["PublicationDate"])
        self.modification_date: datetime.date = TimeConverter.to_date(data["ModificationDate"])
        self.online: bool = data.get("Online", False)
        self.eviction_date: datetime.date = TimeConverter.to_date(data["EvictionDate"])
        self.s3_path: str = data["S3Path"]
        self.checksum: list = data.get("Checksum", [])
        self.content_date: OProductContentDateModel = OProductContentDateModel(
            TimeConverter.to_date(data["ContentDate"].get("Start", "")),
            TimeConverter.to_date(data["ContentDate"].get("End", ""))
        )
        self.footprint: str = data["Footprint"]
        self.geo_footprint: OProductGeoFootprintModel = OProductGeoFootprintModel(
            data["GeoFootprint"]["type"],
            [ODataCoordinate(c[0], c[1]) for c in data["GeoFootprint"]["coordinates"][0]]
        )

        self.attributes: dict[OProductAttributes] = {a["Name"]: OProductAttributes(a["@odata.type"],
                                                                                   a["Name"],
                                                                                   a["Value"],
                                                                                   a["ValueType"]
                                                                                   ) for a in data.get("Attributes", [])
                                                     }

    @property
    async def nodes(self) -> typing.Optional[OProductNodesCollection]:
        response = await self._client.http.request("get", self._client.http.url("Products({self.id})/Nodes"))
        if not response.ok:
            return None

        return OProductNodesCollection(self._client, response, await response.json())

    async def save(self, name: str = ""):
        name = name or self.name
        result = await self._client.http.download(self._client.http.url(f"Products({self.id})/$value"),
                                                  f"{name}.zip")


class OProductNodesCollection(ODataObjectCollection):
    def __init__(self, client, data, response):
        super().__init__(client, response)

        self.items: list[OProductNode] = [OProductNode(client, response, d) for d in data["result"]]


class OProductNode(ODataObject):
    def __init__(self, client, response, data):
        super().__init__(client, response)

        self.id: str = data["Id"]
        self.name: str = data["Name"]
        self.content_length: int = data.get("ContentLength", 0)
        self.children_number: int = data.get("ChildrenNumber", 0)
        self.nodes_uri: OProductNodeNodesModel = OProductNodeNodesModel(
            data["Nodes"]["uri"]
        )

    @property
    async def nodes(self) -> typing.Optional[OProductNodesCollection]:
        response = await self._client.http.request("get", self.nodes_uri.uri)
        result = await response.json()

        if not response.ok:
            return None

        return OProductNodesCollection(self._client, response, result)


@dataclass
class OProductContentDateModel:
    start: datetime.date
    end: datetime.date


@dataclass
class OProductGeoFootprintModel:
    type: str
    coordinates: list[ODataCoordinate]


@dataclass
class OProductNodeNodesModel:
    uri: str


@dataclass
class OProductAttributes:
    type: str
    name: str
    value: str
    value_type: str


class ODataWorkflowsCollection(ODataObjectCollection):
    def __init__(self, client, response, data: dict):
        super().__init__(client, response)
        self.context: str = data["@odata.context"]
        self.next_link: str = data.get("@odata.nextLink", "")
        self.count: int = data.get("@odata.count", 0)
        self.items: tuple[ODataWorkflow] = tuple([ODataWorkflow(client, response, d) for d in data.get("value", [])])


class ODataWorkflow(ODataObject):
    def __init__(self, client: Client, response, data: dict):
        super().__init__(client, response)

        self.id: str = data["Id"]
        self.uuid: str = data.get("Uuid", "")
        self.name: str = data["Name"]
        self.display_name: str = data["DisplayName"]
        self.documentation: str = data.get("Documentation", "")
        self.description: str = data.get("Description", "")
        self.input_product_type: str = data.get("InputProductType", "")
        self.input_product_types: list[str] = data["InputProductTypes"]
        self.output_product_type: str = data.get("OutputProductType", "")
        self.output_product_types: list[str] = data["OutputProductTypes"]
        self.version: str = data.get("WorkflowVersion", "")
        self.options: list[ODataWorkflowOption] = [ODataWorkflowOption(o["Name"], o.get("Description"), o["Type"],
                                                                       o.get("Default"), o.get("value"), o["Required"]
                                                                       ) for o in data.get("WorkflowOptions", [])]
        self.custom_input_source: bool = True


@dataclass
class ODataWorkflowOption:
    name: str
    description: str
    type: str
    default: str
    value: str
    required: bool = True
