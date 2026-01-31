# Adafruit IO Nonprod Feed Setup

This document describes the setup of the `poolio-nonprod` feed group in Adafruit IO for development and testing.

## Prerequisites

- Adafruit IO account ([io.adafruit.com](https://io.adafruit.com))
- Adafruit IO API key (found under "My Key" in the Adafruit IO dashboard)
- Python 3.9+ with `adafruit-io` library (for automated setup)

## Feed Structure

The nonprod environment mirrors production with a `poolio-nonprod` prefix:

| Feed | Key | Description | Publisher | Subscriber |
|------|-----|-------------|-----------|------------|
| gateway | `poolio-nonprod.gateway` | Central message bus | Pool Node | Valve, Display |
| pooltemp | `poolio-nonprod.pooltemp` | Pool water temperature | Pool Node | Display |
| outsidetemp | `poolio-nonprod.outsidetemp` | Outside air temperature | Valve Node | Display |
| insidetemp | `poolio-nonprod.insidetemp` | Inside temperature | Display Node | - |
| poolnodebattery | `poolio-nonprod.poolnodebattery` | Battery percentage | Pool Node | Display |
| poolvalveruntime | `poolio-nonprod.poolvalveruntime` | Daily valve runtime (seconds) | Valve Node | Display |
| valvestarttime | `poolio-nonprod.valvestarttime` | Fill window start (HH:MM) | Admin | Valve Node |
| config | `poolio-nonprod.config` | Device configuration JSON | Admin | All Nodes |
| events | `poolio-nonprod.events` | System events/diagnostics | All Nodes | Admin |

## Manual Setup (Web UI)

### Step 1: Create Feed Group

1. Log in to [io.adafruit.com](https://io.adafruit.com)
2. Navigate to **Feeds** in the left sidebar
3. Click **New Group**
4. Enter:
   - **Name:** `poolio-nonprod`
   - **Description:** `Poolio non-production feeds for development and testing`
5. Click **Create**

### Step 2: Create Feeds

For each feed in the table above:

1. Click on the `poolio-nonprod` group
2. Click **New Feed**
3. Enter the feed name and description
4. Click **Create**

Repeat for all 9 feeds:

| Feed Name | Description |
|-----------|-------------|
| gateway | Central message bus for poolio system messages |
| pooltemp | Pool water temperature readings (Fahrenheit) |
| outsidetemp | Outside air temperature readings (Fahrenheit) |
| insidetemp | Inside temperature readings (Fahrenheit) |
| poolnodebattery | Pool node battery percentage (0-100) |
| poolvalveruntime | Daily valve runtime in seconds |
| valvestarttime | Scheduled fill window start time (HH:MM format) |
| config | Device configuration JSON |
| events | System events and diagnostic messages |

### Step 3: Configure Feed Settings

All feeds are private by default (require API key for read/write). This is the correct setting.

For the `config` feed, consider setting history to 1 data point to only retain the latest configuration:

1. Click on the `config` feed
2. Click **Feed Info** (gear icon)
3. Under **Feed History**, set to `1`
4. Click **Save**

## Automated Setup (Python Script)

Use the provided script for automated feed creation:

```bash
# Install dependencies
pip install adafruit-io

# Run setup script
python scripts/adafruit_io_setup.py --username YOUR_USERNAME --key YOUR_AIO_KEY --environment nonprod
```

The script will:

1. Create the `poolio-nonprod` feed group (if it doesn't exist)
2. Create all 9 feeds within the group
3. Report success/failure for each feed

## Verification

### Via Web UI

1. Navigate to **Feeds** → `poolio-nonprod`
2. Verify all 9 feeds are listed
3. Click each feed to confirm it loads without error

### Via API (curl)

```bash
# Set your credentials
export AIO_USERNAME="your_username"
export AIO_KEY="your_aio_key"

# List feeds in the group
curl -H "X-AIO-Key: $AIO_KEY" \
  "https://io.adafruit.com/api/v2/$AIO_USERNAME/feeds?group_key=poolio-nonprod"

# Test publishing to gateway (should return 200)
curl -X POST \
  -H "X-AIO-Key: $AIO_KEY" \
  -H "Content-Type: application/json" \
  -d '{"value": "test"}' \
  "https://io.adafruit.com/api/v2/$AIO_USERNAME/feeds/poolio-nonprod.gateway/data"

# Fetch latest from gateway
curl -H "X-AIO-Key: $AIO_KEY" \
  "https://io.adafruit.com/api/v2/$AIO_USERNAME/feeds/poolio-nonprod.gateway/data/last"
```

### Via Python

```python
from Adafruit_IO import Client

aio = Client("your_username", "your_aio_key")

# List all feeds in group
feeds = aio.feeds(group_key="poolio-nonprod")
print(f"Found {len(feeds)} feeds:")
for feed in feeds:
    print(f"  - {feed.key}")

# Test publish
aio.send("poolio-nonprod.gateway", "test-message")
print("Published test message to gateway")

# Test receive
data = aio.receive("poolio-nonprod.gateway")
print(f"Received: {data.value}")
```

## Feed URLs Reference

### REST API Endpoints

| Operation | URL |
|-----------|-----|
| List feeds | `GET /api/v2/{username}/feeds?group_key=poolio-nonprod` |
| Get feed | `GET /api/v2/{username}/feeds/poolio-nonprod.{feed}` |
| Publish | `POST /api/v2/{username}/feeds/poolio-nonprod.{feed}/data` |
| Get latest | `GET /api/v2/{username}/feeds/poolio-nonprod.{feed}/data/last` |
| Get history | `GET /api/v2/{username}/feeds/poolio-nonprod.{feed}/data?hours=24` |

### MQTT Topics

| Operation | Topic |
|-----------|-------|
| Publish | `{username}/feeds/poolio-nonprod.{feed}` |
| Subscribe | `{username}/feeds/poolio-nonprod.{feed}` |
| Get last value | `{username}/feeds/poolio-nonprod.{feed}/get` |
| Throttle warnings | `{username}/throttle` |

## Troubleshooting

### 401 Unauthorized

- Verify your API key is correct
- Check the key hasn't expired or been regenerated

### 404 Not Found

- Verify the feed exists
- Check the feed key format: `poolio-nonprod.feedname` (with dot separator)

### 429 Too Many Requests

- Adafruit IO rate limits: 30 data points/minute (free), 60/minute (Plus)
- Wait and retry, or upgrade your account

## See Also

- [Adafruit IO API Documentation](https://io.adafruit.com/api/docs)
- [Adafruit IO Python Library](https://github.com/adafruit/Adafruit_IO_Python)
- [docs/architecture.md](../architecture.md) - Section on Adafruit IO Feed Organization
