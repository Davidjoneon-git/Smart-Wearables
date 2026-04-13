import asyncio
from bleak import BleakScanner

async def main():
    print("Scanning...")
    devices = await BleakScanner.discover(timeout=10.0)
    print(f"Found {len(devices)} devices")
    for d in devices:
        print(f"Name={repr(d.name)} Address={d.address}")

asyncio.run(main())