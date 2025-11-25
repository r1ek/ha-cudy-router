"""Constants for the Cudy Router integration."""

DOMAIN = "cudy_router"

MODULE_MODEM = "modem"
MODULE_DEVICES = "devices"

SECTION_DETAILED = "detailed"

OPTIONS_DEVICELIST = "device_list"
OPTIONS_PRESENCE_TIMEOUT = "presence_timeout"
OPTIONS_PRESENCE_SIGNAL_CHECK = "presence_signal_check"


def parse_device_entry(entry: str) -> tuple[str, str]:
    """Parse device entry: FriendlyName=MAC or just MAC.

    Examples:
        "Steve=B4:FB:E3:BC:F0:13" -> ("Steve", "B4:FB:E3:BC:F0:13")
        "B4:FB:E3:BC:F0:13" -> ("B4:FB:E3:BC:F0:13", "B4:FB:E3:BC:F0:13")

    Returns:
        Tuple of (friendly_name, mac_address)
    """
    entry = entry.strip()
    if not entry:
        return ("", "")

    if "=" in entry:
        parts = entry.split("=", 1)
        return (parts[0].strip(), parts[1].strip())

    return (entry, entry)
