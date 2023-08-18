import asyncio
import os

import odata


def ask_code() -> str:
    print("Please enter 2FA Code:")
    return input()


client = odata.Client(source="codede", ssl_verify=False)


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


async def codede_tests():
    await client.run(email=os.environ.get("COPERNICUS"),
                     password=os.environ.get("COPERNICUS_PASS"),
                     platform="copernicus")

    await client.wait_until_ready()

    products = await client.products("ContentDate/End lt 2019-05-15T00:05:00.000Z",
                                     "",
                                     top=1)

    for product in products:
        nodes = await product.nodes
        print(f"Nodes of {product.name}:")
        if nodes:
            for node in nodes:
                print(node.name)

    await asyncio.sleep(900)
    await client.stop()


asyncio.run(codede_tests())
