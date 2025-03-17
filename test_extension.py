import asyncio
from goose_mcp.tools.device_tools import get_devices, claim_device

async def test_extension():
    # Configuration
    config = {
        "token": "3dff1523fe0340d59a8476904da9dc7e",
        "account_id": "e275a588-40a4-461c-9d04-0a30e984564d",
        "base_url": "https://api.crestron.io/api",
        "cache_duration_minutes": 5,
        "max_retries": 3,
        "timeout_seconds": 30
    }
    
    try:
        # Test get_devices
        print("Testing get_devices...")
        devices = await get_devices(config)
        print(f"Found {len(devices)} devices")
        
        # Test claim_device
        print("\nTesting claim_device...")
        result = await claim_device(
            config,
            mac_address="00.0d.5d.24.c0.0e",
            serial_number="1YB2500276"
        )
        print(f"Claim result: {result}")
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_extension())