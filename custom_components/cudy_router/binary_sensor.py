"""Binary sensor platform for Cudy Router."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    MODULE_DEVICES,
    OPTIONS_DEVICELIST,
    OPTIONS_PRESENCE_TIMEOUT,
    OPTIONS_PRESENCE_SIGNAL_CHECK,
    SECTION_DETAILED,
)
from .coordinator import CudyRouterDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up binary sensor entities from config entry."""
    coordinator: CudyRouterDataUpdateCoordinator = hass.data[DOMAIN][
        config_entry.entry_id
    ]

    # Get device list from options (supports both comma and newline separated)
    device_list = config_entry.options.get(OPTIONS_DEVICELIST, "")
    # Replace newlines with commas, then split
    device_list = device_list.replace("\n", ",")
    tracked_devices = [device.strip() for device in device_list.split(",") if device.strip()]

    entities = []

    # Create a binary sensor for each tracked device
    for device_id in tracked_devices:
        entities.append(CudyRouterDevicePresenceBinarySensor(coordinator, device_id))

    # Add a binary sensor for "any device connected"
    entities.append(CudyRouterAnyDeviceConnectedSensor(coordinator))

    async_add_entities(entities)


class CudyRouterDevicePresenceBinarySensor(
    CoordinatorEntity[CudyRouterDataUpdateCoordinator], BinarySensorEntity
):
    """Binary sensor for device presence on Cudy Router."""

    _attr_has_entity_name = True
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    def __init__(
        self, coordinator: CudyRouterDataUpdateCoordinator, device_id: str
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._attr_name = f"{device_id} connectivity"
        self._attr_unique_id = (
            f"{coordinator.config_entry.entry_id}_presence_{device_id.replace(':', '').replace('-', '_').lower()}"
        )
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.config_entry.entry_id)},
            manufacturer="Cudy",
            name=f"Cudy Router {coordinator.host}",
        )

    @property
    def is_on(self) -> bool:
        """Return true if device is connected."""
        if not self.coordinator.data:
            return False

        devices_module = self.coordinator.data.get(MODULE_DEVICES, {})
        detailed = devices_module.get(SECTION_DETAILED, {})
        device = detailed.get(self._device_id)

        if not device:
            return False

        # Get configuration options
        config_entry = self.coordinator.config_entry
        timeout = int(config_entry.options.get(OPTIONS_PRESENCE_TIMEOUT, 180))
        signal_check = config_entry.options.get(OPTIONS_PRESENCE_SIGNAL_CHECK, True)
        if isinstance(signal_check, str):
            signal_check = signal_check.lower() == "true"

        # Check last seen timestamp
        last_seen = device.get("last_seen")
        now_ts = datetime.now().timestamp()

        if last_seen and (now_ts - last_seen) <= timeout:
            connection = (device.get("connection") or "").lower()
            signal = device.get("signal")

            # Wired connections are always considered connected
            if "wired" in connection:
                return True

            # For wireless, check signal if enabled
            if signal_check:
                if signal and str(signal).strip() not in ("", "---", "None"):
                    return True
            else:
                # If signal check disabled, just rely on timeout
                return True

        return False

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        if not self.coordinator.data:
            return {}

        devices_module = self.coordinator.data.get(MODULE_DEVICES, {})
        detailed = devices_module.get(SECTION_DETAILED, {})
        device = detailed.get(self._device_id)

        if not device:
            return {"status": "not_found"}

        last_seen = device.get("last_seen")
        now_ts = datetime.now().timestamp()
        seconds_since_seen = int(now_ts - last_seen) if last_seen else None

        return {
            "device_id": self._device_id,
            "hostname": device.get("hostname", "Unknown"),
            "ip_address": device.get("ip", "Unknown"),
            "mac_address": device.get("mac", "Unknown"),
            "signal_strength": device.get("signal", "---"),
            "connection_type": device.get("connection", "Unknown"),
            "upload_speed_mbps": device.get("up_speed", 0),
            "download_speed_mbps": device.get("down_speed", 0),
            "online_time": device.get("online", "---"),
            "last_seen_seconds_ago": seconds_since_seen,
            "presence_timeout": int(
                self.coordinator.config_entry.options.get(OPTIONS_PRESENCE_TIMEOUT, 180)
            ),
        }

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success

    @property
    def icon(self) -> str:
        """Return the icon to use in the frontend."""
        if self.is_on:
            connection = self.extra_state_attributes.get("connection_type", "").lower()
            if "wired" in connection:
                return "mdi:lan-connect"
            elif "wifi" in connection or "2.4g" in connection or "5g" in connection:
                return "mdi:wifi"
            return "mdi:check-network"
        return "mdi:close-network"


class CudyRouterAnyDeviceConnectedSensor(
    CoordinatorEntity[CudyRouterDataUpdateCoordinator], BinarySensorEntity
):
    """Binary sensor that shows if any devices are connected to the router."""

    _attr_has_entity_name = True
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    def __init__(self, coordinator: CudyRouterDataUpdateCoordinator) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._attr_name = "any device connected"
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_any_device_connected"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.config_entry.entry_id)},
            manufacturer="Cudy",
            name=f"Cudy Router {coordinator.host}",
        )

    @property
    def is_on(self) -> bool:
        """Return true if any device is connected."""
        if not self.coordinator.data:
            return False

        devices_module = self.coordinator.data.get(MODULE_DEVICES, {})
        connected_devices_data = devices_module.get("connected_devices", {})
        device_count = connected_devices_data.get("value", 0)

        return device_count > 0

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        if not self.coordinator.data:
            return {}

        devices_module = self.coordinator.data.get(MODULE_DEVICES, {})
        connected_devices_data = devices_module.get("connected_devices", {})
        device_count = connected_devices_data.get("value", 0)

        attributes = connected_devices_data.get("attributes", {})
        devices = attributes.get("devices", [])

        return {
            "total_devices": device_count,
            "wired_devices": sum(
                1
                for d in devices
                if "wired" in (d.get("connection") or "").lower()
            ),
            "wireless_devices": sum(
                1
                for d in devices
                if "wifi" in (d.get("connection") or "").lower()
                or "2.4g" in (d.get("connection") or "").lower()
                or "5g" in (d.get("connection") or "").lower()
            ),
            "devices": devices,
        }

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success

    @property
    def icon(self) -> str:
        """Return the icon to use in the frontend."""
        if self.is_on:
            return "mdi:devices"
        return "mdi:devices-off"
