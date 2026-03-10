import asyncio
from bleak import BleakScanner

async def main():
    print("Scanning for 10 seconds...")
    devices = await BleakScanner.discover(timeout=10.0)

    if not devices:
        print("No BLE devices found at all.")
        return

    for d in devices:
        print("Name:", d.name, "| Address:", d.address)

asyncio.run(main())