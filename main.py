import asyncio
import os

import odata
from odata import Filter


def ask_code() -> str:
    print("Please enter 2FA Code:")
    return input()


client = odata.Client(source="creodias")


async def on_ready():
    print(f"Logged in as {client.email} with some ms latency")


"""Filter.or_where(
    Filter.name.has("CARD-COH12"),
    Filter.name.has("CARD-COH6"),
    Filter.name.has("CARD-BS"),
),"""


@client.ready
async def main():
    collection = await client.products.filter.where(
        Filter.attribute.satisfies(Filter.attribute.ProductType, "in", ["CARD-COH12", "CARD-BS", "CARD-COH6"])
    ).expand("Attributes").get()

    for product in collection:
        print(f"{product.name} - {product.attributes['productType'].value}")

    workflows = await client.workflows.get()

    print(f"Workflows: {len(workflows)} ")
    for workflow in workflows:
        print(f"{workflow.name}: {workflow.input_product_types}")

    batch_response, batch_result = await client.http.request("get", "https://datahub.creodias.eu/odata/v1/BatchOrder")

    print(batch_result["value"])

    await asyncio.sleep(10)
    await client.stop()
    await asyncio.sleep(10)


client.run(email=os.environ.get("email"),
           password=os.environ.get("password"),
           platform="copernicus")

