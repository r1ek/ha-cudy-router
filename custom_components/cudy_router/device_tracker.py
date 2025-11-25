"""Device tracker platform for Cudy Router."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from homeassistant.components.device_tracker import SourceType, TrackerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    MODULE_DEVICES,
    OPTIONS_DEVICELIST,
    OPTIONS_PRESENCE_TIMEOUT,
    OPTIONS_PRESENCE_SIGNAL_CHECK,
    SECTION_DETAILED,
    parse_device_entry,
)
from .coordinator import CudyRouterDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up device tracker entities from config entry."""
    coordinator: CudyRouterDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    device_list = config_entry.options.get(OPTIONS_DEVICELIST, "")
    # Support both comma and newline separated values
    device_list = device_list.replace("\n", ",")
    tracked_devices = [device.strip() for device in device_list.split(",") if device.strip()]
    entities = []
    for device_entry in tracked_devices:
        friendly_name, device_id = parse_device_entry(device_entry)
        if device_id:
            entities.append(CudyRouterDeviceTracker(coordinator, friendly_name, device_id))
    async_add_entities(entities)

class CudyRouterDeviceTracker(CoordinatorEntity, TrackerEntity):
    """Device tracker for a device connected to the Cudy Router."""

    def __init__(self, coordinator: CudyRouterDataUpdateCoordinator, friendly_name: str, device_id: str) -> None:
        super().__init__(coordinator)
        self._friendly_name = friendly_name
        self._device_id = device_id
        safe_name = friendly_name.replace(':', '').replace('-', '_').replace(' ', '_').lower()
        self._attr_unique_id = f"cudy_router_{safe_name}"
        self._attr_name = f"Cudy Device {friendly_name}"
        self._attr_source_type = SourceType.ROUTER
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.config_entry.entry_id)},
            "manufacturer": "Cudy",
            "name": "Cudy Router",
        }
        self._attr_should_poll = False  # Explicitly tell HA not to poll
        self._attr_available = True     # Mark entity as available by default

    @property
    def is_connected(self) -> bool:
        """Return true if the device is connected (uses same logic as binary sensor)."""
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

            # Wireless connections: check signal if enabled
            if signal_check:
                return signal and str(signal).strip() not in ("", "---")
            else:
                # If signal check disabled, any device within timeout is connected
                return True

        return False

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributes for the device tracker."""
        if not self.coordinator.data:
            return {}

        devices_module = self.coordinator.data.get(MODULE_DEVICES, {})
        detailed = devices_module.get(SECTION_DETAILED, {})
        device = detailed.get(self._device_id)

        if device:
            return device.copy()
        return {}

    async def async_update(self) -> None:
        """Force update of the entity state."""
        self.async_write_ha_state()
