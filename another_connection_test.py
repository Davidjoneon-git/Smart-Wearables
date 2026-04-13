import asyncio
from bleak import BleakScanner, BleakClient

DEVICE_NAME = "XIAO-ESP32S3"

async def main():
    print("Scanning...")
    devices = await BleakScanner.discover(timeout=10.0)

    target = None
    for d in devices:
        print(f"Name={repr(d.name)} Address={d.address}")

        if d.name and DEVICE_NAME in d.name:
            target = d
            break

    if target is None:
        print("Device not found")
        return

    print("Connecting to", target.name, target.address)

    async with BleakClient(target.address) as client:
        print("Connected")

asyncio.run(main())