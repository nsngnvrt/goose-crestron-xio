# Goose Crestron XiO Extension

A Goose extension for managing Crestron devices through the XiO Cloud service.

## Prerequisites

- Python 3.8 or higher
- Goose Desktop installed
- Crestron XiO Cloud account with API access
- API Token and Account ID from Crestron

## Features

- Device claiming (single and bulk)
- Device status monitoring
- Network information retrieval
- Multi-device operations
- Rate limiting and caching support

## Installation

### Option 1: Install from ZIP file (No GitHub account required)
1. Download `goose-crestron-xio.zip`
2. Extract the zip file
3. Open a terminal/command prompt
4. Run the following command:
   ```bash
   goose extension install /path/to/extracted/goose-crestron-xio
   ```
   Replace `/path/to/extracted/` with the actual path where you extracted the zip file

### Option 2: Install from GitHub (requires GitHub access)
```bash
goose extension install github:nsngnvrt/goose-crestron-xio
```

## Configuration

After installation, configure the extension through Goose Desktop:

1. Open Goose Desktop
2. Click the menu (⋮) in the top right
3. Select "Settings"
4. Under "Extensions", find "goose-crestron-xio"
5. Configure your credentials:
   ```yaml
   token: "your-xio-cloud-api-token"
   account_id: "your-xio-cloud-account-id"
   ```

Alternatively, you can configure manually in `~/.config/goose/config.yaml`:
```yaml
extensions:
  goose-crestron-xio:
    # Required settings
    token: "your-xio-cloud-api-token"
    account_id: "your-xio-cloud-account-id"
    
    # Optional settings
    base_url: "https://api.crestron.io/api"
    cache_duration_minutes: 5
    max_retries: 3
    timeout_seconds: 30
```

### Getting Your Credentials
1. Log in to your Crestron XiO Cloud account
2. Navigate to Account Settings
3. Generate an API token
4. Copy your Account ID from the account details

## Usage

### Claim a Single Device

```python
result = await goose.tools.claim_device(
    mac_address="00.10.7f.b1.e3.00",
    serial_number="1829JBH01829"
)
```

### Bulk Claim Devices

```python
result = await goose.tools.bulk_claim_devices(
    file_path="devices.csv"
)
```

CSV Format:
```csv
MAC Address,Serial Number,Device Name
00.10.7f.b1.e3.00,1829JBH01829,Mercury01
```

### Get Device Status

```python
status = await goose.tools.get_device_status(
    device_id="device-id"
)
```

### Get Network Information

```python
network_info = await goose.tools.get_device_network_info(
    device_id="device-id"
)
```

### Get Multiple Device Status

```python
statuses = await goose.tools.get_multi_device_status(
    device_ids=["device-id-1", "device-id-2"]
)
```

### Get Multiple Device Network Information

```python
network_infos = await goose.tools.get_multi_device_network_info(
    device_ids=["device-id-1", "device-id-2"]
)
```

## Troubleshooting

Common issues and their solutions:
- **API Rate Limiting**: The extension includes automatic rate limiting, but you may need to adjust `cache_duration_minutes`
- **Connection Timeout**: Adjust `timeout_seconds` if you experience timeout issues
- **Authentication Errors**: Verify your XiO Cloud token and account_id are correct
- **MAC Address Format**: Ensure MAC addresses are in the format "00.10.7f.b1.e3.00"
- **Installation Issues**: Make sure you're using the full path to the extension directory when installing

## License

MIT License