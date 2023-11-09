from __future__ import annotations

import functools
import re
import typing
from typing import TYPE_CHECKING, Optional, Union, Any, Callable, Literal

if TYPE_CHECKING:
    from odata.client import Client

__Filters_names = Literal["Name", "LOL"]
__Operators = Literal["is", "like"]

__Names_available: typing.List[__Filters_names] = list(typing.get_args(__Filters_names))
__Operators_available: typing.List[__Operators] = list(typing.get_args(__Operators))


def _filter(name: str, operators: list[str]):
    def filter_decor(func: Callable[[str, Any], Union[Filter, Query]]):
        @functools.wraps(func)
        def filter_wrap(*args, **kwargs):
            if not kwargs["operator"] in operators:
                raise AttributeError(f"{kwargs['operator']} is not a valid operator for {name} filter")

            output = func(*args, **kwargs)
            return output

        return filter_wrap
    return filter_decor


class Query:
    """
    >>> query = Query()
    >>> print(query.where(name="Name", operator="like", value="name%like%this%end"))  # returns self
    contains(Name,'like') and contains(Name,'this') and endswith(Name,'end') and startswith(Name,'name')
    >>> print(query.clear().name("like", "clear%does%not_matter"))
    contains(Name,'does') and endswith(Name,'not_matter') and startswith(Name,'clear')
    >>> print(query.clear().where_not(Query.name("is", "i_hate_js")))
    not Name eq 'i_hate_js'
    """

    def __init__(self, *filters: Union[Filter, Query]):
        self.__filters: list[Union[Filter, Query]] = list(filters)
        self.logic: Literal["and", "or", "not"] = "and"

        self.name = self._instance_name

    def __str__(self) -> str:
        return f" {self.logic} " + " ".join([f"{f.logic} {str(f)}" for f in self.__filters if str(f)]).rstrip()

    def clear(self) -> Query:

        self.__filters = []
        return self

    def where(self, *filters: Union[Filter, Query],
              name: __Filters_names = None, operator: __Operators_available = None, value: Any = None) -> Query:
        self.__filters.append(Query(*filters))

        if name and operator and value:
            self.__filters.append(self.__filter_factory(name, operator, value))

        return self

    def or_where(self, *filters: Union[Filter, Query],
                 name: __Filters_names = None, operator: __Operators_available = None, value: Any = None) -> Query:
        for f in filters:
            f.logic = "or"
        self.__filters.append(Query(*filters))

        if name and operator and value:
            new = self.__filter_factory(name, operator, value)
            new.logic = "or"
            self.__filters.append(new)

        return self

    def where_not(self, *filters: Union[Filter, Query],
                  name: __Filters_names = None, operator: __Operators_available = None, value: Any = None) -> Query:
        for f in filters:
            f.logic = "not"
        self.__filters.append(Query(*filters))

        if name and operator and value:
            new = Query(self.__filter_factory(name, operator, value))
            new.logic = "not"
            self.__filters.append(new)

        return self

    def __filter_factory(self, name: str, operator: str, value: Any) -> Union[Filter, Query]:
        match name:

            case "Name":
                return self.__name(operator=operator, value=value)

    def _instance_name(self, operator, name) -> Query:
        self.__filters.append(self.__name(operator=operator, value=name))
        return self

    @staticmethod
    def name(operator, name) -> Union[Filter, Query]:
        return Query.__name(operator=operator, value=name)

    @staticmethod
    @_filter("Name", ["is", "like"])
    def __name(operator: str, value: Any) -> Union[Filter, Query]:
        """
        @note: Value example%lend will be expressed by 'contains BOTH "example" and "lend" in any order or position.
               In this example name containing "examplend" will be included in result!

        @param operator:
        @param value:
        @return:
        """

        result_filters: list[Filter] = []

        match operator:
            case "is":
                result_filters.append(Filter("Name", "eq", [value, ], "{name} {operator} '{}'", "Name"))

            case "like":

                patterns: dict[str, str] = {
                    r"(?<=%)([^%]+?)(?=%)": "contains",
                    r"(?<=%)([^%]+?)$": "endswith",
                    r"^([^%]+?)(?=%)": "startswith",
                }

                for pattern, operator in patterns.items():
                    result_filters.extend([
                        Filter("Name", operator, [find, ], "{operator}({name},'{}')", "Name")
                        for find in re.findall(pattern, value)
                    ])

        return result_filters[0] if len(result_filters) == 1 else Query(*result_filters)


class Filter:

    def __init__(self, name: str, operator: str, values: list[Any], filter_format: str, category: str,
                 logic: Literal["and", "or", "not"] = "and"):
        self._name = name
        self._operator = operator
        self._values: list[Any] = values
        self._category = category

        self.__format = filter_format

        self.logic = logic

    def __str__(self) -> str:
        return self.__format.format(operator=self._operator, name=self._name, *self._values)


if __name__ == '__main__':
    import doctest
    doctest.testmod(extraglobs={'q': Query()})
