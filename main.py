import asyncio
import os

import odata
from odata import Collections, Filter, Attributes

import datetime  # TODO: TMP


def ask_code() -> str:
    print("Please enter 2FA Code:")
    return input()


client = odata.Client(source="creodias")


async def on_ready():
    print(f"Logged in as {client.email} with some ms latency")


@client.ready
async def main():
    collection = await client.product.filter.where(
        Collections.is_in(Collections.SENTINEL_1, Collections.SENTINEL_2),
        Filter.or_where(
            Filter.Name.has("S1A")
        ),
        Filter.Sensing.span(
            datetime.datetime.now() - datetime.timedelta(days=120),
            datetime.datetime.now())
    ).get()

    for product in collection:
        print(product.name)

    await asyncio.sleep(10)
    await client.stop()
    await asyncio.sleep(10)


client.run(email=os.environ.get("email"),
           password=os.environ.get("password"),
           platform="copernicus")

