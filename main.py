import asyncio
import os

import odata

from odata._helpers import TimeConverter  # TODO: TMP FIND BETTER SOLUTION


def ask_code() -> str:
    print("Please enter 2FA Code:")
    return input()


client = odata.Client(source="creodias", ssl_verify=False)


@client.ready
async def on_ready():
    print(f"Logged in as {client.email} with some ms latency")


async def main():
    # await client.run(email=os.environ.get("LOGIN"), password=os.environ.get("PASSWORD"), totp_code=ask_code)
    await client.run(email=os.environ.get("COPERNICUS"),
                     password=os.environ.get("COPERNICUS_PASS"),
                     platform="copernicus")

    await client.wait_until_ready()

    # orders = await client.production.orders()
    # order = await client.production.order(7)
    print(await client.production_orders())

    order = await client.production_order.get(10)

    if order:
        cancelled = await order.cancel()

    workflows = await client.workflows("", "", "", top=2, count=True)
    print(workflows.count)
    for workflow in workflows:
        print(f"{workflow.display_name} - {workflow.description}")
    await asyncio.sleep(900)
    await client.stop()


async def product_tests():
    await client.run(email=os.environ.get("COPERNICUS"),
                     password=os.environ.get("COPERNICUS_PASS"),
                     platform="copernicus")

    # await client.product.filter.collection("SENTINEL-1").and_.name_has("S1A").or_.name_is("S1A_EW_GRDM_1SDH_20220503T065105_20220503T065203_043043_0523C5_AC61.SAFE").top(30).get()

    # start_date = TimeConverter.to_date("2019-05-15T00:00:00.000Z")
    # end_date = TimeConverter.to_date("2019-05-16T00:00:00.000Z")

    # await client.product.filter.geographic_point(-0.5319577002158441, 28.65487836189358).and_.sensing_date(start_date, end_date).count(True).expand("Attributes").get()

    collection = await client.product.get()
    # collection = await client.product.id("fe37ae5f-153b-511c-89b9-dcc059c86489", expand="Attributes")

    print(collection.products)
    product = collection[0]
    for product in collection.products:
        pass
        # print(product.name)

    nodes = await product.nodes
    for node in nodes:
        print(node.name)

    await asyncio.sleep(900)
    await client.stop()

asyncio.run(product_tests())
