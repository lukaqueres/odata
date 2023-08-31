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
    #collection = await client.products.get("060882f4-0a34-5f14-8e25-6876e4470b0d")

    #for product in collection:
        #await product.save()

    collection = await client.products.filter.where(
        Filter.attribute.satisfies(Filter.attribute.ProductType, "in", "EW_GRDH_1S-COG")
    ).expand("Attributes").get()

    for product in collection:
        print(product.name)

    collection = await client.products.filter.where(Filter.name.starts_with("S2MSI2A")).get()

    for product in collection:
        print(f"{product.name} - {product.attributes['productType'].value}")

    workflows = await client.workflows.filter.where(Filter.name.exact("card_bs")).get()

    print(f"Workflows: {len(workflows)} ")
    for workflow in workflows:
        print(workflow.description)
        print(f"{workflow.name}: {workflow.input_product_types}")

    batch_response, batch_result = await client.http.request("get", "https://datahub.creodias.eu/odata/v1/BatchOrder")

    print(batch_result["value"])

    new = {
        "Name": " S2B_MSIL1C_20230829T065629_N0509_R063_T45XVF_20230829T091015.SAFE",
        "Priority": 0,
        "WorkflowName": "string",
        "WorkflowOptions": [
        ],
        "BatchSize": 0,
        "BatchVolume": 0,
    }

    batch_response, batch_result = await client.http.request("get", "https://datahub.creodias.eu/odata/v1/BatchOrder(2136786)")
    print(batch_result)

    await asyncio.sleep(10)
    await client.stop()
    await asyncio.sleep(10)


client.run(email=os.environ.get("email"),
           password=os.environ.get("password"),
           platform="copernicus")

