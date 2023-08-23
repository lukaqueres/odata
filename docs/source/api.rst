""""""
Client
""""""
 `class` odata. **Client** ( `*, source="creodias", **options` )

===================      ========================
Attributes               Methods
===================      ========================
:ref:`client-email`      `@`     ready
live                     `async` run
product                  `async` stop
source                   `async` wait_until_ready
token

===================      ========================

Represents connection to odata API. You use this class to interact data.

**Parameters:**

- **source** ``(Optional[ str ])`` -
    Default "creodias", source of data. Accepts "creodias" & "codede"

.. _client-email:

email
=====
    Email of authorized user. ``None`` if no user is authorized.

    **Type:**
        Optional[ str ]

