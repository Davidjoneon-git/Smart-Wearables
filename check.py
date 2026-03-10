import sys
sys.coinit_flags = 0

import asyncio
from bleak import BleakScanner

SERVICE_UUID = "12345678-1234-1234-1234-1234567890ab"

async def main():
    print("Scanning for 20 seconds...")
    devices = await BleakScanner.discover(
        timeout=20.0,
        service_uuids=[SERVICE_UUID],
    )

    print(f"Found {len(devices)} devices")
    for d in devices:
        print("Name:", d.name, "| Address:", d.address)

asyncio.run(main())