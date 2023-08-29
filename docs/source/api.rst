.. meta::
    :title: Odata API
    :description: Odata python library documentation
    :keywords: python, library, odata, documentation, api, creodias, codede

.. automodule:: odata
    :members:

.. class:: OProductsQueryConstructor(client: :ref:`Client`)

    .. rst-class:: attributes

    .. list::

        * **Attributes**
        * :ref:`filter <OProductsQueryConstructor-filter>`
        * **Methods**
        * :ref:`def top <OProductsQueryConstructor-top>`
        * :ref:`def skip <OProductsQueryConstructor-skip>`
        * :ref:`def count <OProductsQueryConstructor-count>`
        * :ref:`def expand <OProductsQueryConstructor-expand>`
        * :ref:`def order_by <OProductsQueryConstructor-order_by>`

    Represents connection to odata API. You use this class to interact with data.

    **Parameters:**

    - :attr:`client Client` -
        Client instance used to make requests

    .. _OProductsQueryConstructor-filter:

    .. attribute:: filter

        :type: QueryConstructorFilterParser

        Collects filters for query.

    .. _OProductsQueryConstructor-top:

    .. method:: top( number: int )

        :attr:`number`

            :type: int

        Limits number of records query will return. 20 if not set. Must be greater than 0 and not higher than 1000.

        Returns `Self` for method chaining.

    .. _OProductsQueryConstructor-skip:

    .. method:: skip( number: int )

        :attr:`number`

            :type: int

        Skips number of records in returned collection. Must be not lower than 0 and not higher than 10000.

        Returns `Self` for method chaining.

    .. _OProductsQueryConstructor-count:

    .. method:: count( count: bool )

        :attr:`count`

            :type: bool

        If true, query will return `count` attribute with exact number of products matching request query.

        Returns `Self` for method chaining.


    .. _OProductsQueryConstructor-expand:

    .. method:: expand( category: bool )

        :attr:`category`

            :type: Literal["Attributes", "Assets"]

        Returned records have additional data, relative to category.  Categories are: `Attributes` and `Assets`

        Returns `Self` for method chaining.

    .. _OProductsQueryConstructor-order_by:

    .. method:: order_by( argument: str, direction: Literal["asc", "desc"] = "asc" )

        :attr:`argument`

            :type: str

            Order of records will be determined by provided parameter

            Available arguments:

                - ContentDate/Start",
                - "ContentDate/End",
                - "PublicationDate",
                - "ModificationDate"

        :attr:`direction`

            :type: Literal["asc", "desc"] = "asc"

            Determines if results are ascending or descending by order by argument.

        Orders records by argument in order by direction.

        Returns `Self` for method chaining.

    .. method:: get( *ids: str )

        :attr:`*ids`

            :type: str

            None, One or more ids of products to fetch.

        If no id was passed, standard query will be executed with any parameters from previous methods & filters.

        And if any id were passed, query without any filters & limits will be sent only for ids.

        Returns `Optional[OProductsCollection]`

        If request was successful, :class:`OProductsCollection` class with result will be returned. In any other case, `None`.