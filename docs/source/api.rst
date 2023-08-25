Client
#######
.. class:: `class` odata.Client( `*, source="creodias", **options` )

.. rst-class:: attributes

.. hlist::
    :columns: 2

    * **Attributes**
    * :ref:`_client-email` email
    * http
    * product
    * source
    * **Methods**
    * @ ready
    * def run
    * async stop

Represents connection to odata API. You use this class to interact with data.

**Parameters:**

- **source** ``(Optional[ str ])`` -
    Default "creodias", source of data. Accepts "creodias" & "codede"

.. _client-email:

.. attribute:: email

    Email of authorized user. ``None`` if no user is authorized.

    :type: **Type:**
        Optional[ str ]

.. attribute:: `property` http

    Email of authorized user. ``None`` if no user is authorized.

    :type: **Type:**
        Optional[ str ]