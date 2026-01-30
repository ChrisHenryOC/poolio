# Type stubs for message envelope functions

from typing import Any

PROTOCOL_VERSION: int
ENVELOPE_REQUIRED_FIELDS: list[str]

def validate_device_id(device_id: str) -> None: ...
def create_envelope(
    msg_type: str, device_id: str, payload: dict[str, Any], timestamp: str | None = None
) -> dict[str, Any]: ...
def parse_envelope(json_str: str) -> tuple[dict[str, Any], dict[str, Any]]: ...
