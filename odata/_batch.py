from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from odata.client import Client


from odata._workflow import WorkflowOptions


time_format = "%Y-%m-%dT%H:%M:%S.%fZ"


class BatchOrders:

    def __init__(self, client: Client):
        self._client = client

    def new(self) -> ODataBatchOrderResponse:
        pass

    def list(self) -> ODataBatchOrdersCollection:
        pass

    def get(self, order_id: int):
        pass


class ODataBatchObject:

    def __init__(self, client):
        self._client = client


class ODataBatchOrdersCollection(ODataBatchObject):
    def __init__(self, client: Client, orders: dict, context: str, next_link: Optional[str] = "",
                 count: Optional[int] = None):
        super().__init__(client)

        self.context: str = context
        self.next_link: str = next_link
        self.count: int = count

        self.orders: list[ODataBatchOrder] = [ODataBatchOrder.factory(client, order) for order in orders]


class ODataBatchOrderResponse(ODataBatchObject):

    def __init__(self, client, context: str, order: ODataBatchOrder):
        super().__init__(client)

        self.context: str = context

        self.order: ODataBatchOrder = order


class ODataBatchOrder(ODataBatchObject):

    def __init__(self, client, name: str, workflow_name: str, order_id: int, status: str,
                 submission_date: datetime.datetime, keycloak_uuid: str, workflow_id: int,
                 priority: Optional[int] = 0,
                 notification_endpoint: Optional[str] = "", notification_username: Optional[str] = "",
                 notification_status: Optional[str] = "",
                 workflow_options: Optional[dict] = None, estimated_date: Optional[datetime.datetime] = None,
                 summary: Optional[dict] = None):

        super().__init__(client)

        self.name = name
        self.priority = priority
        self.notifications: BatchOrderNotificationsEndpoint = BatchOrderNotificationsEndpoint(
            notification_endpoint, notification_username, notification_status
        )

        self.id = order_id
        self.status = status
        self.submitted: datetime.datetime = submission_date
        self.estimated: datetime.datetime = estimated_date

        self.keycloak_uuid = keycloak_uuid
        self.summary: BatchOrderSummary = BatchOrderSummary.factory(summary)

        self.workflow: BatchOrderWorkflow = BatchOrderWorkflow(workflow_name, workflow_id, workflow_options)

    @classmethod
    def factory(cls, client, data) -> ODataBatchOrder:
        order = ODataBatchOrder(
            client=client,
            name=data["Name"],
            workflow_name=data["WorkflowName"],
            order_id=data["Id"],
            status=data["Status"],
            submission_date=datetime.datetime.strptime(data["SubmissionDate"], time_format),
            keycloak_uuid=data["KeycloakUUID"],
            workflow_id=data["WorkflowId"],
            priority=data.get("Priority"),
            notification_endpoint=data.get("NotificationEndpoint"),
            notification_status=data.get("NotificationStatus"),
            notification_username=data.get("NotificationEpUsername"),
            workflow_options=data.get("WorkflowOptions"),
            estimated_date=data.get("EstimatedDate"),
            summary=data.get("Summary")
        )

        return order


class BatchOrderNotificationsEndpoint:

    def __init__(self, endpoint: str, name: str, status: str):
        self.endpoint = endpoint
        self.name = name
        self.status = status


class BatchOrderWorkflow:
    def __init__(self, name: str, workflow_id: int, options: Optional[dict]):
        self.name = name
        self.id = workflow_id
        self.options = WorkflowOptions.factory(options or {})


class BatchOrderSummary:

    def __init__(self, status: str, downloading_order_items_count: int, done_order_items_count: int,
                 already_done_order_items_count: int, queued_order_items_count: int,
                 last_order_item_change_timestamp: datetime.datetime):

        self.status: str = status
        self.downloading_items: int = downloading_order_items_count
        self.done: int = done_order_items_count
        self.already_done: int = already_done_order_items_count
        self.queued: int = queued_order_items_count
        self.last_modified: datetime.datetime = last_order_item_change_timestamp

    @classmethod
    def factory(cls, data) -> BatchOrderSummary:
        data.update(
            last_order_change_timestamp=datetime.datetime.strptime(data["last_order_change_timestamp"], time_format)
        )

        summary = BatchOrderSummary(
            **data
        )

        return summary


class ODataBatchOrderItem(ODataBatchObject):
    def __init__(self, client, item_id: int, order_id: int, input_product_reference: str,
                 submission_date: datetime.datetime, status: str, processed_name: Optional[str] = "",
                 processed_size: Optional[int] = 0, output_uuid: Optional[str] = "", status_message: Optional[str] = "",
                 completed_date: Optional[datetime.datetime] = None):

        super().__init__(client=client)

        self.id: int = item_id
        self.order_id: int = order_id
        self.input_product: str = input_product_reference
        self.submitted: datetime.datetime = submission_date
        self.status: str = status
        self.processed_name: str = processed_name
        self.processed_size: int = processed_size
        self.output_uuid: str = output_uuid
        self.status_message: str = status_message
        self.completed: datetime.datetime = completed_date

