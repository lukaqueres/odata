from __future__ import annotations

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from odata.client import Client


class ODataWorkflowObject:

    def __init__(self, client: Client):
        self._client = client


class WorkflowOption:

    def __init__(self, name: str, value: str):
        self.name: str = name
        self.value: str = value


class WorkflowOptions:
    def __init__(self, *options):
        self.options: list[WorkflowOption] = list(options)

    @classmethod
    def factory(cls, data: dict) -> WorkflowOptions:
        options = WorkflowOptions([WorkflowOption(name, value) for name, value in data.items()])
        return options
