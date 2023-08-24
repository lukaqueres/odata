Client
~~~~~~
 `class` odata. **Client** ( `*, source="creodias", **options` )

.. hlist::
    :columns: 2

    * **Attributes**
    * **Methods**
    * source
    * def run
    * email
    * async stop
    * product
    * @ ready
    * http

Represents connection to odata API. You use this class to interact with data.

**Parameters:**

- **source** ``(Optional[ str ])`` -
    Default "creodias", source of data. Accepts "creodias" & "codede"

.. _client-email:

email
=====
    Email of authorized user. ``None`` if no user is authorized.

    :type: **Type:**
        Optional[ str ]

