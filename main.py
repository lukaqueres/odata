import asyncio
import datetime
import os

import aiohttp

import odata
from odata import Filter


def ask_code() -> str:
    print("Please enter 2FA Code:")
    return input()


client = odata.Client(platform=odata.Platform.Copernicus, download_directory="products", source="copernicus")


async def on_ready():
    print(f"Logged in as {client.email} with some ms latency")


"""Filter.or_where(
    Filter.name.has("CARD-COH12"),
    Filter.name.has("CARD-COH6"),
    Filter.name.has("CARD-BS"),
),"""


async def test_req(session: aiohttp.ClientSession):
    async with session.get(f"https://zipper.dataspace.copernicus.eu/odata/v1/Products(db0c8ef3-8ec0-5185-a537-812dad3c58f8)/$value") as request:
        print(f"REQUEST: {request.status}: {request.reason} - {await request.content.read() if not request.ok else 'OK'}")



@client.ready
async def main():
    #collection = await client.products.expand("Attributes").get()
    # products = await client.products.filter.where(Filter.name.has("MSIL2A")).get()

    #for product in products:
    #    await product.save()
    product = await client.products.get("0d0e1241-cff8-4ff4-9611-233b460fa446")
    print(product.name)
    # await product.save("test_prod")
    #await client.http.download("https://zipper.dataspace.copernicus.eu/odata/v1/Products(5a7f18e7-0127-40e1-9528-e90255f3a61d)/Nodes(S2B_MSIL2A_20231017T090859_N0509_R050_T33NXG_20231017T123325.SAFE)/Nodes", "inspier_product")
    return

    # for product in collection:
    #    print(product.attributes)
    # await product.save()

    # Filter.attribute.satisfies(Filter.attribute.ProductType, "==", "EW_GRDH_1S-COG"),

    # collection = await client.products.filter.where(
    #     Filter.name.has("LA"),
    #     Filter.sensing.span(datetime.datetime.now() - datetime.timedelta(days=900), datetime.datetime.now())
    # ).expand("Attributes").get()
    #
    # for product in collection:
    #     print(f"{product.name} - {product.attributes['productType'].value}")
    #
    # print(collection.next_link)

    workflow_list = await client.workflows.get()
    for workflow in workflow_list:
        print(workflow.name)

    workflows = await client.workflows.filter.where(Filter.name.exact("card_bs")).get()

    # print(f"Workflows: {len(workflows)} ")
    # for workflow in workflows:
    # print(workflow.description)
    # print(f"{workflow.name}: {workflow.input_product_types}")
    workflow = workflows[0]
    print(workflow.input_product_types)

    collection = await client.products.filter.where(
         # Filter.name.exact("LS05_RKSE_TM__GTC_1P_19850423T093257_19850423T093325_006086_0193_0024_DCC8"),
         Filter.collection.is_from(Filter.collection.SENTINEL_3)
         # Filter.attribute.satisfies(Filter.attribute.ProductType, "in", workflow.input_product_types)
    ).expand("Attributes").top(1).get()

    # collection = await client.products.expand("Attributes").order_by("ContentDate/Start", "desc").get()

    for product in collection:
        print(f"{product.name} - {product.content_date.start}")
        # await product.save()

    # batch_response, batch_result = await client.http.request("get", "https://datahub.creodias.eu/odata/v1/BatchOrder")
    #
    # print(batch_result["value"])
    #
    batch_response, batch_result = await client.http.request("get", "https://datahub.creodias.eu/odata/v1/BatchOrder(2136786)")
    print(batch_result)

    async with aiohttp.ClientSession() as session:
        session.headers.update({"Authorization": f"Bearer {await client.token}"})
        await asyncio.gather(*[asyncio.create_task(test_req(session=session)) for i in range(16)])

    await asyncio.sleep(10)
    await client.stop()
    await asyncio.sleep(10)


client.run(email=os.environ.get("creodias_login"),
           password=os.environ.get("creodias"),
           totp_code="920503",
           platform="creodias")

