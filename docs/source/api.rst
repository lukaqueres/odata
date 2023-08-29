.. meta::
    :title: Odata API
    :description: Odata python library documentation
    :keywords: python, library, odata, documentation, api, creodias, codede

.. toctree::
    :maxdepth: 2

    index
    types

.. class:: odata.Client( *, source="creodias", **options )

    .. rst-class:: attributes

    .. hlist::
        :columns: 2

        * **Attributes**
        * :ref:`email<client-email>`
        * :ref:`http<client-http>`
        * :ref:`products<client-products>`
        * :ref:`workflows<client-workflows>`
        * **Methods**
        * :ref:`@ ready<client-ready>`
        * :ref:`def run<client-run>`
        * :ref:`async stop<client-stop>`

    Represents connection to odata API. You use this class to interact with data.

    **Parameters:**

    - :attr:`source Optional[ str ]` -
        Default "creodias", source of data. Accepts "creodias" & "codede"

    .. _client-email:

    .. attribute:: email

        :type: Optional[ str ]

        Email of authorized user. ``None`` if no user is authorized.

    .. _client-http:

    .. attribute:: http

        :type: odata.Http

        Returns Http object used by client to make ``HTTP`` requests.

    .. _client-products:

    .. attribute:: products

        :type: :ref:`OProductsQueryConstructor`

        Property, returns query constructor for product calls.

        You need this to fetch products.

    .. _client-workflows:

    .. attribute:: workflows

        :type: OWorkflowsQueryConstructor

        Property, workflows call query constructor.

    .. _client-ready:

    .. decoratormethod:: ready(function)

        Decorated function will be called after client is ready.

        .. code-block::

            @client.ready
            async def on_ready():
                print(f"Logged in as {client.email} with some ms latency")

    .. _client-run:

    .. method:: run(email: str, password: str, totp_key: str = "", totp_code: str | typing.Callable[[], str] = "", platform: str = "creodias")

        :type: None

        :attr:`email`

            :type: str

            Email associated with account, used for generating token.

        :attr:`password`

            :type: str

            Password used with email.

        :attr:`totp_key`

            :type: Optional[str]

            Secret key of 2FA tokens. Allows to generate totp codes by client.

        :attr:`totp_code`

            :type: Optional[Union[str, Callable[[], str]]]

            Current totp code.
            If callable was passed, code will run it for code.

        :attr:`platform`

            :type: str = "creodias"

            Platform account used is from, default `"creodias"`
            Currently supported:

            * `creodias <https://cloudferro.com/case-studies/creodias/>`_
            * `codede <https://cloudferro.com/case-studies/code-de/>`_
            * `copernicus <https://www.copernicus.eu/en>`_

        Code example:

        .. code-block::

            client = odata.Client(source="creodias")

            client.run(email=os.environ.get("email"),
                password=os.environ.get("password"),
                platform="copernicus")

        And with 2FA:

        .. code-block::

            def ask_code() -> str:
                print("Please enter 2FA Code:")
                return input()

            client.run(email=os.environ.get("email"),
                password=os.environ.get("password"),
                totp_code=ask_code,
                platform="creodias")

    .. _client-stop:

    .. coroutinemethod:: stop()

        :type: None

        Stops client, and halts token refresh process.

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