import asyncio
import os

import odata
from odata import Collections, Filter, Attributes

import datetime  # TODO: TMP


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

    query = client.product.filter.where(Collections.is_in(Collections.SENTINEL_1, Collections.SENTINEL_2),
                                        Filter.or_where(
                                            Filter.Name.has("S1A"),
                                            Filter.Name.exact("S1A_EW_GRDM_1SDH_20220503T065105_20220503T065203_043043_0523C5_AC61.SAFE")
                                        ),
                                        Filter.Publication.span(
                                            datetime.datetime.now() - datetime.timedelta(days=120),
                                            datetime.datetime.now()),
                                        Filter.Geographic.point(odata.types.Coordinates(-0.53195770021, 28.6548783618)),
                                        Attributes.satisfies(Attributes.OrbitNumber, "!=", 987)
                                        ).get()


    return
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
