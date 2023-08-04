from __future__ import annotations

from dataclasses import dataclass, field

import requests
import datetime
import typing

import odata.errors as errors
from odata.__authentication import Token


class Group:
    _api_url = "https://datahub.creodias.eu/odata/v1/"

    def __init__(self, token: str | Token = ""):
        self._token: Token | str = token

    def token(self, token: Token | str) -> typing.Self:
        self._token = token
        return self

    @staticmethod
    def time_converter(time: str) -> datetime.date:
        return datetime.datetime.strptime(time, "%Y-%m-%dT%H:%M:%SZ").date()

    async def _get(self, endpoint: str, data: dict, *args, **kwargs) -> requests.Response:
        with requests.Session() as session:
            session.headers["authorization"] = f"Bearer {self._token}"

            response: requests.Response = session.get(self._url(endpoint), *args, data=data, **kwargs)

        if response.status_code in (401, 403):
            raise errors.UnauthorizedError(response.status_code, response.reason)

        return response

    async def _post(self, endpoint: str, data, *args, **kwargs) -> requests.Response:
        with requests.Session() as session:
            session.headers["authorization"] = f"Bearer {self._token}"

            response: requests.Response = session.post(self._url(endpoint), *args, json=data, **kwargs)

        if response.status_code in (401, 403):
            raise errors.UnauthorizedError(response.status_code, response.reason)

        return response

    def _url(self, endpoint: str) -> str:
        return f"{self._api_url}{endpoint}"


class Production(Group):
    def __init__(self, token: str | Token):
        super().__init__(token)

    async def create(self, workflow_id: str, workflow_name: str, workflow_version: str, input_product_reference: dict,
                     workflow_options: dict, name: str, priority: int = 0,
                     notification_endpoint: str = "") -> SingleProductionOrders | RequestInvalid:
        # TODO: Figure out a way to handle notifications with events, could use a flask integration / support?

        data: dict = {
            "WorkflowId": workflow_id,
            "WorkflowName": workflow_name,
            "WorkflowVersion": workflow_version,
            "InputProductReference": input_product_reference,
            "WorkflowOptions": workflow_options,
            "Priority": priority,
            "NotificationEndpoint": notification_endpoint,
            "Name": name
        }

        response = await self._post("ProductionOrder/OData.CSC.Order", data=data)

        result = response.json()

        if response.status_code == 422:
            invalidation_result = RequestInvalid(
                "",
                response,
                [RequestInvalidDetail(i["loc"], i["msg"], i["type"]) for i in result["detail"]]
            )

            return invalidation_result

        production_order = ProductionOrder(
            _token=self._token,
            response=response,
            id=result["Id"],
            status=result["Status"],
            status_message=result["StatusMessage"],
            submission_date=self.time_converter(result["SubmissionDate"]),
            name=result["Name"],
            estimated_date=self.time_converter(result["EstimatedDate"]),
            input_product_reference=InputProductReference(
                result["InputProductReference"]["Reference"],
                ProductionReferenceContentDate(
                    start=self.time_converter(result["InputProductReference"]["Start"]),
                    end=self.time_converter(result["InputProductReference"]["End"])
                )),
            workflow_name=result["WorkflowName"],
            workflow_options=result["WorkflowOptions"],
            workflow_id=result["WorkflowId"],
            priority=result["Priority"]
        )

        single_production_orders = SingleProductionOrders(
            _token=self._token,
            response=response,
            context=result["@odata.context"],
            production_order=production_order
        )

        return single_production_orders

    async def cost(self, workflow_id: str, workflow_name: str, workflow_version: str, input_product_reference: dict,
                   workflow_options: dict, name: str, priority: int = 0,
                   notification_endpoint: str = "") -> ProductionOrderCostEstimate | RequestInvalid:

        data: dict = {
            "WorkflowId": workflow_id,
            "WorkflowName": workflow_name,
            "WorkflowVersion": workflow_version,
            "InputProductReference": input_product_reference,
            "WorkflowOptions": workflow_options,
            "Priority": priority,
            "NotificationEndpoint": notification_endpoint,
            "Name": name
        }

        response = await self._post("ProductionOrder/OData.CSC.EstimateCost", data=data)

        result = response.json()

        if response.status_code == 422:
            invalidation_result = RequestInvalid(
                "",
                response,
                [RequestInvalidDetail(i["loc"], i["msg"], i["type"]) for i in result["detail"]]
            )

            return invalidation_result

        cost = ProductionOrderCostEstimate(result["tokens"])

        return cost

    async def order(self, order_id):
        response = await self._get("ProductionOrder({id}".format(id=order_id), {})
        result = response.json()
        production_order = ProductionOrder(
            _token=self._token,
            response=response,
            id=result["Id"],
            status=result["Status"],
            status_message=result["StatusMessage"],
            submission_date=self.time_converter(result["SubmissionDate"]),
            name=result["Name"],
            estimated_date=self.time_converter(result["EstimatedDate"]),
            input_product_reference=InputProductReference(
                result["InputProductReference"]["Reference"],
                ProductionReferenceContentDate(
                    start=self.time_converter(result["InputProductReference"]["Start"]),
                    end=self.time_converter(result["InputProductReference"]["End"])
                )),
            workflow_name=result["WorkflowName"],
            workflow_options=result["WorkflowOptions"],
            workflow_id=result["WorkflowId"],
            priority=result["Priority"]
        )

        single_production_orders = SingleProductionOrders(
            _token=self._token,
            response=response,
            context=result["@odata.context"],
            production_order=production_order
        )

        return single_production_orders

    async def orders(self, query_filter: str = "", order_by: str = "", count: bool = False, top: int = 1000,
                     skip: int = 0) -> ProductionOrders:
        if not 0 <= top <= 1000:
            raise ValueError("Invalid top value, must be between 0 and 1000")
        if not skip >= 0:
            raise ValueError("Skip value must equal or be higher than 0")
        data: dict = {
            "filter": query_filter,
            "orderby": order_by,
            "count": count,
            "top": top,
            "skip": skip
        }

        response = await self._get("ProductionOrders", data)

        result = response.json()
        orders = []
        for order in result["value"]:
            orders.append(ProductionOrder(
                _token=self._token,
                response=response,
                id=order["Id"],
                status=order["Status"],
                status_message=order["StatusMessage"],
                submission_date=self.time_converter(order["SubmissionDate"]),
                name=order["Name"],
                estimated_date=self.time_converter(order["EstimatedDate"]),
                input_product_reference=InputProductReference(
                    order["InputProductReference"]["Reference"],
                    ProductionReferenceContentDate(
                        start=self.time_converter(order["InputProductReference"]["Start"]),
                        end=self.time_converter(order["InputProductReference"]["End"])
                    )),
                workflow_name=order["WorkflowName"],
                workflow_options=order["WorkflowOptions"],
                workflow_id=order["WorkflowId"],
                priority=order["Priority"]
            ))

        production_orders = ProductionOrders(
            _token=self._token,
            response=response,
            context=result["@odata.context"],
            production_orders=orders
        )

        return production_orders


@dataclass
class Type(Group):
    _token: Token | str
    response: typing.Optional[requests.Response]

    @property
    def latency(self) -> float:
        """ Get connection latency

        :return: Object's initial requests latency in ms
        """
        if not self.response:
            return 0
        return self.response.elapsed.total_seconds() * 1000


@dataclass
class SingleProductionOrders(Type):
    context: str = ""
    production_order: typing.Optional[ProductionOrder] = None

    def __nonzero__(self) -> bool:
        return bool(self.production_order)


@dataclass
class ProductionOrders(Type):
    context: str = ""
    next_link: str = ""
    count: int = 0
    production_orders: list[ProductionOrder] = field(default_factory=lambda: [])
    __current: int = 0

    def __getitem__(self, item):
        return self.production_orders[item]

    def __len__(self):
        return len(self.production_orders)

    def __iter__(self):
        self.__current = 0
        return self

    def __next__(self):
        if self.__current >= len(self.production_orders):
            self.__current = 0
            raise StopIteration
        self.__current += 1
        return self.production_orders[self.__current]

    def __nonzero__(self) -> bool:
        return bool(self.production_orders)


@dataclass
class ProductionOrder(Type):
    id: str
    status: str
    status_message: str
    submission_date: datetime.date
    name: str
    estimated_date: datetime.date
    input_product_reference: InputProductReference
    workflow_options: dict
    workflow_name: str
    workflow_id: str
    priority: int

    async def cancel(self) -> SingleProductionOrders:
        response = await self._post("ProductionOrder({id})/OData.CSC.Cancel".format(id=self.id), {})
        result = response.json()
        production_order = ProductionOrder(
            _token=self._token,
            response=response,
            id=result["Id"],
            status=result["Status"],
            status_message=result["StatusMessage"],
            submission_date=self.time_converter(result["SubmissionDate"]),
            name=result["Name"],
            estimated_date=self.time_converter(result["EstimatedDate"]),
            input_product_reference=InputProductReference(
                result["InputProductReference"]["Reference"],
                ProductionReferenceContentDate(
                    start=self.time_converter(result["InputProductReference"]["Start"]),
                    end=self.time_converter(result["InputProductReference"]["End"])
                )),
            workflow_name=result["WorkflowName"],
            workflow_options=result["WorkflowOptions"],
            workflow_id=result["WorkflowId"],
            priority=result["Priority"]
        )

        single_production_orders = SingleProductionOrders(
            _token=self._token,
            response=response,
            context=result["@odata.context"],
            production_order=production_order
        )

        return single_production_orders

    async def output(self) -> Product:
        response = await self._get("ProductionOrder({id})/OData.CSC.Cancel".format(id=self.id), {})

        result = response.json()
        product = Product(
            _token=self._token,
            response=response,
            name=result["processed_name"],
            uuid=result["output_uuid"],
            processed_size=result["processed_size"],
            metadata=result["processing_metadata"]
        )

        return product

    async def value(self) -> str:
        response = await self._get("ProductionOrder({id})/Product".format(id=self.id), {})
        return str(response.content)  # TODO: Check if it is string with output product

    def __nonzero__(self) -> bool:
        return bool(self.id)


@dataclass
class Product(Type):
    name: str
    uuid: str
    processed_size: int
    metadata: dict

    def __nonzero__(self) -> bool:
        return bool(self.name)


@dataclass
class ProductionReferenceContentDate:
    start: datetime.date
    end: datetime.date


@dataclass
class InputProductReference:
    reference: str
    content_date: ProductionReferenceContentDate


@dataclass
class RequestInvalidDetail:
    loc: [str, int]
    message: str
    type: str


@dataclass
class ProductionOrderCostEstimate:
    tokens: int


@dataclass
class RequestInvalid(Type):
    detail: list[RequestInvalidDetail]


@dataclass
class Workflow(Type):
    id: str
    uuid: str
    name: str
    display_name: str
    documentation: str
    description: str
    input_product_type: str
    input_product_types: list[str]
    output_product_type: str
    output_