"""Constants for the GOK SmartBox integration."""
from datetime import timedelta
import re

DOMAIN = "gok_smartbox"

API_BASE_URL = "https://smartboxazurefunction.azurewebsites.net/api"
# Shared Azure Functions key hard-coded in the official app (see specs/GOK_query.md).
API_KEY = "slgep8fCk-LSQ1JvWIVP82lW_Xafx7g8b7j-5qqPrd3RAzFuo8uSOA=="

CONF_DEVICE_ID = "device_id"
CONF_INTERVAL = "interval"

# Values double as selector option keys and must match [a-z0-9-_]+ for hassfest.
INTERVAL_HOURLY = "hourly"
INTERVAL_DAILY = "daily"
INTERVALS: dict[str, timedelta] = {
    INTERVAL_HOURLY: timedelta(hours=1),
    INTERVAL_DAILY: timedelta(days=1),
}
DEFAULT_INTERVAL = INTERVAL_DAILY

# QR string is the MAC (12 hex chars) followed by a model suffix, e.g. AA11BB22CC33GOK-010
DEVICE_ID_RE = re.compile(r"^([0-9A-Fa-f]{12})")


def parse_device_id(raw: str) -> str | None:
    """Return the 12 char uppercase device ID from a scanned QR string."""
    match = DEVICE_ID_RE.match(raw.strip())
    return match.group(1).upper() if match else None
