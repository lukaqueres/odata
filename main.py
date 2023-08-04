import asyncio
import os

import odata


def ask_code() -> str:
    print("Please enter 2FA Code:")
    return input()


client = odata.Client()


@client.ready
async def on_ready():
    print(f"Logged in as {client.email} with {await client.latency()} ms latency")


async def main():
    # await client.run(email=os.environ.get("LOGIN"), password=os.environ.get("PASSWORD"), totp_code=ask_code)
    await client.run(email=os.environ.get("COPERNICUS"),
                     password=os.environ.get("COPERNICUS_PASS"),
                     platform="copernicus")

    await client.wait_until_ready()

    # orders = await client.production.orders()
    # order = await client.production.order(7)
    order = await client.production.order(10)
    cancelled = await order.production_order.cancel()
    print(bool(order))
    await asyncio.sleep(900)
    await client.stop()


asyncio.run(main())
