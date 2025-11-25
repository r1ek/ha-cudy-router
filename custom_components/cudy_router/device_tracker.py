"""Device tracker platform for Cudy Router."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.device_tracker import SourceType, TrackerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MODULE_DEVICES, OPTIONS_DEVICELIST, parse_device_entry
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
        """Return true if the device is connected: Wired or has a valid signal."""
        devices = self.coordinator.data.get(MODULE_DEVICES, [])
        _LOGGER.warning("[CudyRouterDeviceTracker] Devices in coordinator: %s", devices)
        _LOGGER.warning("[CudyRouterDeviceTracker] Looking for device: %s", self._device_id)
        for dev in devices:
            _LOGGER.warning("[CudyRouterDeviceTracker] Checking device: %s", dev)
            if isinstance(dev, dict) and dev.get("mac") and dev["mac"].lower() == self._device_id.lower():
                connection = dev.get("connection", "").lower()
                signal = dev.get("signal")
                _LOGGER.warning("[CudyRouterDeviceTracker] Found device with MAC %s: connection=%s, signal=%s", self._device_id, connection, signal)
                # Connected if Wired, or signal is present and not empty or '---'
                if connection == "wired":
                    return True
                if signal and str(signal).strip() != "" and str(signal).strip() != "---":
                    return True
                return False
        _LOGGER.warning("[CudyRouterDeviceTracker] Device with MAC %s not found in devices list", self._device_id)
        return False

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributes for the device tracker."""
        devices = self.coordinator.data.get(MODULE_DEVICES, [])
        for dev in devices:
            if isinstance(dev, dict) and dev.get("mac") and dev["mac"].lower() == self._device_id.lower():
                return dev.copy()
        return {}

    async def async_update(self) -> None:
        """Force update of the entity state and log call."""
        _LOGGER.warning("[CudyRouterDeviceTracker] async_update called for device: %s", self._device_id)
        self.async_write_ha_state()
