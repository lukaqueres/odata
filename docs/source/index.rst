.. https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html
.. https://devguide.python.org/documentation/markup/

.. meta::
    :title: Welcome to odata documentation
    :description: Odata python library documentation
    :keywords: python, library, odata, documentation, api, creodias, codede

#############
Odata library
#############

odata is still evolving python library for odata data access with creodias or codede API.

**Features:**

- Download odata directly
- Process odata
- Batch orders
- User Workspace access

**Links:**

- `Github repository <https://github.com/lukaqueres/odata>`__
- `API documentation on creodias <https://creodias.docs.cloudferro.com/en/latest/eodata/EOData-Catalogue-API-Manual-on-Creodias.html>`__

"""""""""""
Basic usage
"""""""""""

Example of running client instance. If authorization passed you can use you client instance for requests.

.. code-block:: python

    import odata
    import asyncio

    client = odata.Client(source="creodias")
    # change to "codede" if you want to use codede as a source

    @client.ready
    async def main():
        print("If you see me, client is ready! ")
        await asyncio.sleep(10)
        await client.stop()  # Client will run forever unless stopped

    client.run(email=os.environ.get("email"),
                     password=os.environ.get("password"),
                     totp_code=000000,
                     # Input your 2FA code here, you can find more options in documentation.
                     platform="creodias")

