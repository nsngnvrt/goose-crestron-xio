from typing import Dict, Any, List, Optional, Union
import httpx
import asyncio
import json
from datetime import datetime, timedelta
import csv
from io import StringIO
from pathlib import Path

class CrestronError(Exception):
    def __init__(self, message: str, status_code: int, response_text: Optional[str] = None):
        self.message = message
        self.status_code = status_code
        self.response_text = response_text
        super().__init__(self.message)

class Cache:
    def __init__(self, duration: timedelta):
        self.duration = duration
        self.cache = {}
        self.timestamps = {}

    def get(self, key: str) -> Optional[Any]:
        if key in self.cache:
            if datetime.now() - self.timestamps[key] < self.duration:
                return self.cache[key]
            else:
                del self.cache[key]
                del self.timestamps[key]
        return None

    def set(self, key: str, value: Any):
        self.cache[key] = value
        self.timestamps[key] = datetime.now()

def format_mac_address(mac_address: str) -> str:
    """Format MAC address to xx.xx.xx.xx.xx.xx format"""
    mac_clean = mac_address.replace(":", "").replace("-", "").replace(".", "").replace(" ", "")
    mac_clean = mac_clean.lower()
    
    if len(mac_clean) != 12:
        raise ValueError(f"Invalid MAC address length: {mac_address}")
    
    if not all(c in '0123456789abcdef' for c in mac_clean):
        raise ValueError(f"Invalid MAC address characters: {mac_address}")
    
    return ".".join(mac_clean[i:i+2] for i in range(0, 12, 2))

class CrestronClient:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.cache = Cache(timedelta(minutes=config.get('cache_duration_minutes', 5)))
        
        self.client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {config['token']}",
                "XiO-subscription-key": config['token'],
                "Content-Type": "application/json"
            },
            timeout=config.get('timeout_seconds', 30)
        )

    async def _handle_rate_limit(self, response) -> bool:
        if response.status_code == 429:
            try:
                message = response.json().get('message', '')
                if 'Try again in' in message:
                    seconds = int(''.join(filter(str.isdigit, message)))
                    await asyncio.sleep(seconds + 1)
                    return True
            except Exception:
                await asyncio.sleep(60)
                return True
        return False

    async def claim_device(self, mac_address: str, serial_number: str) -> Dict[str, str]:
        """Claim a device to XiO Cloud service"""
        url = f"{self.config['base_url']}/v2/deviceclaim/accountid/{self.config['account_id']}/macaddress/{mac_address}/serialnumber/{serial_number}"
        
        async with self.client as client:
            response = await client.post(url)
            if response.status_code == 200:
                return {
                    "status": "success",
                    "message": f"{mac_address}: Device claimed successfully"
                }
            elif response.status_code == 429:
                if await self._handle_rate_limit(response):
                    return await self.claim_device(mac_address, serial_number)
            
            raise CrestronError(
                f"Device claim failed: {response.status_code}",
                response.status_code,
                response.text
            )

    async def bulk_claim_devices(self, file_path: str) -> Dict[str, Any]:
        """Claim multiple devices using a CSV file"""
        # Read CSV file
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)
            devices = list(reader)

        if len(devices) > 200:
            raise ValueError("CSV file contains more than 200 devices")

        successful_claims = []
        failed_claims = {}

        for device in devices:
            try:
                mac_address = format_mac_address(device['MAC Address'])
                result = await self.claim_device(mac_address, device['Serial Number'])
                if result['status'] == 'success':
                    successful_claims.append(mac_address)
                else:
                    failed_claims[mac_address] = result['message']
            except Exception as e:
                failed_claims[device['MAC Address']] = str(e)
            await asyncio.sleep(1)  # Rate limiting

        return {
            "status": "success",
            "message": f"Processed {len(devices)} devices. {len(successful_claims)} successful, {len(failed_claims)} failed.",
            "successful_claims": successful_claims,
            "failed_claims": failed_claims
        }

    async def get_devices(self) -> List[Dict[str, Any]]:
        """Get list of all devices"""
        url = f"{self.config['base_url']}/v1/device/accountid/{self.config['account_id']}/devices"
        
        async with self.client as client:
            response = await client.get(url)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                if await self._handle_rate_limit(response):
                    return await self.get_devices()
            
            raise CrestronError(
                f"Failed to get devices: {response.status_code}",
                response.status_code,
                response.text
            )

    async def get_device_status(self, device_id: str) -> Dict[str, Any]:
        """Get status of a specific device"""
        cache_key = f"device_status_{device_id}"
        cached_data = self.cache.get(cache_key)
        if cached_data:
            return cached_data

        url = f"{self.config['base_url']}/v1/device/accountid/{self.config['account_id']}/devicecid/{device_id}/status"
        
        async with self.client as client:
            response = await client.get(url)
            if response.status_code == 200:
                data = response.json()
                self.cache.set(cache_key, data)
                return data
            elif response.status_code == 429:
                if await self._handle_rate_limit(response):
                    return await self.get_device_status(device_id)
            
            raise CrestronError(
                f"Failed to get device status: {response.status_code}",
                response.status_code,
                response.text
            )

    async def get_device_network_info(self, device_id: str) -> Dict[str, Optional[str]]:
        """Get network information for a specific device"""
        status = await self.get_device_status(device_id)
        
        if "network" not in status:
            return {
                "ip_address": None,
                "mac_address": None,
                "hostname": None
            }
            
        network = status["network"]
        return {
            "ip_address": network.get("nic-1-ip-address"),
            "mac_address": network.get("nic-1-mac-address"),
            "hostname": network.get("status-host-name")
        }

    async def get_multi_device_status(
        self,
        device_ids: List[str],
        properties: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Get status for multiple devices in parallel"""
        tasks = [self.get_device_status(device_id) for device_id in device_ids]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        results = {}
        errors = {}
        
        for device_id, response in zip(device_ids, responses):
            if isinstance(response, Exception):
                errors[device_id] = str(response)
            else:
                results[device_id] = response
        
        return {
            "results": results,
            "errors": errors
        }

    async def get_multi_device_network_info(
        self,
        device_ids: List[str]
    ) -> Dict[str, Any]:
        """Get network information for multiple devices in parallel"""
        tasks = [self.get_device_network_info(device_id) for device_id in device_ids]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        results = {}
        errors = {}
        
        for device_id, response in zip(device_ids, responses):
            if isinstance(response, Exception):
                errors[device_id] = str(response)
            else:
                results[device_id] = response
        
        return {
            "results": results,
            "errors": errors
        }

# Tool functions that will be exposed to Goose
async def claim_device(config: Dict[str, Any], mac_address: str, serial_number: str) -> Dict[str, str]:
    """Claim a device to XiO Cloud service"""
    client = CrestronClient(config)
    return await client.claim_device(mac_address, serial_number)

async def bulk_claim_devices(config: Dict[str, Any], file_path: str) -> Dict[str, Any]:
    """Claim multiple devices using a CSV file"""
    client = CrestronClient(config)
    return await client.bulk_claim_devices(file_path)

async def get_devices(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get list of all devices"""
    client = CrestronClient(config)
    return await client.get_devices()

async def get_device_status(config: Dict[str, Any], device_id: str) -> Dict[str, Any]:
    """Get status of a specific device"""
    client = CrestronClient(config)
    return await client.get_device_status(device_id)

async def get_device_network_info(config: Dict[str, Any], device_id: str) -> Dict[str, Optional[str]]:
    """Get network information for a specific device"""
    client = CrestronClient(config)
    return await client.get_device_network_info(device_id)

async def get_multi_device_status(
    config: Dict[str, Any],
    device_ids: List[str],
    properties: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """Get status for multiple devices in parallel"""
    client = CrestronClient(config)
    return await client.get_multi_device_status(device_ids, properties)

async def get_multi_device_network_info(
    config: Dict[str, Any],
    device_ids: List[str]
) -> Dict[str, Any]:
    """Get network information for multiple devices in parallel"""
    client = CrestronClient(config)
    return await client.get_multi_device_network_info(device_ids)