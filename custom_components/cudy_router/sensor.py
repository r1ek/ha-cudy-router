"""Support for Cudy Router Sensor Platform."""
from __future__ import annotations
from dataclasses import dataclass

import re
from datetime import datetime
from typing import Any

from .const import (
    DOMAIN,
    MODULE_DEVICES,
    MODULE_MODEM,
    OPTIONS_DEVICELIST,
    SECTION_DETAILED,
    OPTIONS_PRESENCE_TIMEOUT,
    OPTIONS_PRESENCE_SIGNAL_CHECK,
)
from .coordinator import CudyRouterDataUpdateCoordinator

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_HOST,
    CONF_NAME,
    SIGNAL_STRENGTH_DECIBELS,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    UnitOfDataRate,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity


@dataclass
class CudyRouterSensorEntityDescriptionMixin:
    """Mixin for required keys."""

    module: str
    name_suffix: str


@dataclass
class CudyRouterSensorEntityDescription(
    SensorEntityDescription, CudyRouterSensorEntityDescriptionMixin
):
    """Describe Cudy sensor sensor entity."""


SIGNAL_SENSOR = CudyRouterSensorEntityDescription(
    key="signal",
    module="modem",
    name_suffix="signal strength",
    icon="mdi:network-strength-outline",
    state_class=SensorStateClass.MEASUREMENT,
)
NETWORK_SENSOR = CudyRouterSensorEntityDescription(
    key="network",
    module="modem",
    name_suffix="network",
    icon="mdi:network-strength-outline",
)

SENSOR_TYPES = {
    ("modem", "sim"): CudyRouterSensorEntityDescription(
        key="sim",
        device_class=SensorDeviceClass.ENUM,
        options=["Sim 1", "Sim 2"],
        module="modem",
        name_suffix="SIM slot",
        icon="mdi:sim",
    ),
    ("modem", "connected_time"): CudyRouterSensorEntityDescription(
        key="connected_time",
        module="modem",
        name_suffix="connected time",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        device_class=SensorDeviceClass.DURATION,
        icon="mdi:timer",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    ("modem", "cell"): CudyRouterSensorEntityDescription(
        key="cell",
        module="modem",
        name_suffix="cell information",
        icon="mdi:antenna",
    ),
    ("modem", "rsrp"): CudyRouterSensorEntityDescription(
        key="rsrp",
        module="modem",
        name_suffix="RSRP",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        icon="mdi:signal",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    ("modem", "rsrq"): CudyRouterSensorEntityDescription(
        key="rsrq",
        module="modem",
        name_suffix="RSRQ",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS,
        icon="mdi:signal",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    ("modem", "sinr"): CudyRouterSensorEntityDescription(
        key="sinr",
        module="modem",
        name_suffix="SINR",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS,
        icon="mdi:signal",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    ("modem", "rssi"): CudyRouterSensorEntityDescription(
        key="rssi",
        module="modem",
        name_suffix="RSSI",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        icon="mdi:signal",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    ("modem", "band"): CudyRouterSensorEntityDescription(
        key="band",
        module="modem",
        name_suffix="band",
        icon="mdi:alpha-b-box",
    ),
    ("devices", "device_count"): CudyRouterSensorEntityDescription(
        key="device_count",
        module="devices",
        name_suffix="device count",
        icon="mdi:devices",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    ("devices", "top_downloader_speed"): CudyRouterSensorEntityDescription(
        key="top_downloader_speed",
        module="devices",
        name_suffix="top downloader speed",
        device_class=SensorDeviceClass.DATA_RATE,
        native_unit_of_measurement=UnitOfDataRate.MEGABITS_PER_SECOND,
        icon="mdi:download",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    ("devices", "top_downloader_mac"): CudyRouterSensorEntityDescription(
        key="top_downloader_mac",
        module="devices",
        name_suffix="top downloader MAC",
        icon="mdi:download-network-outline",
    ),
    ("devices", "top_downloader_hostname"): CudyRouterSensorEntityDescription(
        key="top_downloader_hostname",
        module="devices",
        name_suffix="top downloader hostname",
        icon="mdi:download-network-outline",
    ),
    ("devices", "top_uploader_speed"): CudyRouterSensorEntityDescription(
        key="top_uploader_speed",
        module="devices",
        name_suffix="top uploader speed",
        device_class=SensorDeviceClass.DATA_RATE,
        native_unit_of_measurement=UnitOfDataRate.MEGABITS_PER_SECOND,
        icon="mdi:upload",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    ("devices", "top_uploader_mac"): CudyRouterSensorEntityDescription(
        key="top_uploader_mac",
        module="devices",
        name_suffix="top uploader MAC",
        icon="mdi:upload-network-outline",
    ),
    ("devices", "top_uploader_hostname"): CudyRouterSensorEntityDescription(
        key="top_uploader_hostname",
        module="devices",
        name_suffix="top uploader hostname",
        icon="mdi:upload-network-outline",
    ),
    ("devices", "total_down_speed"): CudyRouterSensorEntityDescription(
        key="total_down_speed",
        module="devices",
        name_suffix="total download speed",
        device_class=SensorDeviceClass.DATA_RATE,
        native_unit_of_measurement=UnitOfDataRate.MEGABITS_PER_SECOND,
        icon="mdi:upload",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    ("devices", "total_up_speed"): CudyRouterSensorEntityDescription(
        key="total_up_speed",
        module="devices",
        name_suffix="total upload speed",
        device_class=SensorDeviceClass.DATA_RATE,
        native_unit_of_measurement=UnitOfDataRate.MEGABITS_PER_SECOND,
        icon="mdi:upload",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    ("devices", "connected_devices"): CudyRouterSensorEntityDescription(
        key="connected_devices",
        module="devices",
        name_suffix="connected devices",
        icon="mdi:devices",
    ),
}


DEVICE_MAC_SENSOR = CudyRouterSensorEntityDescription(
    key="mac",
    module="devices",
    name_suffix="mac",
    icon="mdi:network-outline",
)

DEVICE_HOSTNAME_SENSOR = CudyRouterSensorEntityDescription(
    key="hostname",
    module="devices",
    name_suffix="hostname",
    icon="mdi:network-outline",
)

DEVICE_UPLOAD_SENSOR = CudyRouterSensorEntityDescription(
    key="up_speed",
    module="devices",
    name_suffix="upload speed",
    device_class=SensorDeviceClass.DATA_RATE,
    native_unit_of_measurement=UnitOfDataRate.MEGABITS_PER_SECOND,
    icon="mdi:upload",
    state_class=SensorStateClass.MEASUREMENT,
)

DEVICE_DOWNLOAD_SENSOR = CudyRouterSensorEntityDescription(
    key="down_speed",
    module="devices",
    name_suffix="download speed",
    device_class=SensorDeviceClass.DATA_RATE,
    native_unit_of_measurement=UnitOfDataRate.MEGABITS_PER_SECOND,
    icon="mdi:download",
    state_class=SensorStateClass.MEASUREMENT,
)

DEVICE_ONLINE_SENSOR = CudyRouterSensorEntityDescription(
    key="online",
    module="devices",
    name_suffix="online",
    icon="mdi:lan-connect",
)

DEVICE_SIGNAL_SENSOR = CudyRouterSensorEntityDescription(
    key="signal",
    module="devices",
    name_suffix="signal",
    icon="mdi:wifi",
)

DEVICE_PRESENCE_SENSOR = CudyRouterSensorEntityDescription(
    key="presence",
    module="devices",
    name_suffix="presence",
    icon="mdi:account-check",
)


def as_name(input_str: str) -> str:
    """Replaces any non-alphanumeric characters with underscore"""

    if not input_str:
        return "null"
    return re.sub("[^0-9a-zA-Z]", "_", input_str)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Cudy Router sensors."""

    coordinator: CudyRouterDataUpdateCoordinator = hass.data[DOMAIN][
        config_entry.entry_id
    ]
    name = as_name(config_entry.data.get(CONF_NAME) or config_entry.data.get(CONF_HOST))
    entities = []

    for module, sensors in coordinator.data.items():
        for sensor_label in sensors:
            sensor_description = SENSOR_TYPES.get((module, sensor_label))
            if sensor_description:
                entities.append(
                    CudyRouterSensor(
                        coordinator,
                        name,
                        sensor_label,
                        sensor_description,
                    )
                )
    entities.append(CudyRouterSignalSensor(coordinator, name, "signal", SIGNAL_SENSOR))
    entities.append(
        CudyRouterSignalSensor(coordinator, name, "network", NETWORK_SENSOR)
    )
    
    # Add the connected devices sensor
    connected_devices_description = SENSOR_TYPES.get(("devices", "connected_devices"))
    if connected_devices_description:
        entities.append(
            CudyRouterConnectedDevicesSensor(
                coordinator,
                name,
                "connected_devices",
                connected_devices_description,
            )
        )
    options = config_entry.options
    # Support both comma and newline separated values
    device_list_str = (options and options.get(OPTIONS_DEVICELIST)) or ""
    device_list_str = device_list_str.replace("\n", ",")
    device_list = [
        x.strip()
        for x in device_list_str.split(",")
    ]

    for device_id in device_list:
        if not device_id:
            continue
        entities.append(
            CudyRouterDeviceSensor(coordinator, name, device_id, DEVICE_MAC_SENSOR)
        )
        entities.append(
            CudyRouterDeviceSensor(coordinator, name, device_id, DEVICE_HOSTNAME_SENSOR)
        )
        entities.append(
            CudyRouterDeviceSensor(coordinator, name, device_id, DEVICE_UPLOAD_SENSOR)
        )
        entities.append(
            CudyRouterDeviceSensor(coordinator, name, device_id, DEVICE_DOWNLOAD_SENSOR)
        )
        entities.append(
            CudyRouterDeviceSensor(coordinator, name, device_id, DEVICE_ONLINE_SENSOR)
        )
        entities.append(
            CudyRouterDeviceSensor(coordinator, name, device_id, DEVICE_SIGNAL_SENSOR)
        )
        # Use the new presence sensor class for presence
        entities.append(
            CudyRouterPresenceSensor(coordinator, name, device_id, DEVICE_PRESENCE_SENSOR)
        )

    async_add_entities(entities)


class CudyRouterDeviceSensor(
    CoordinatorEntity[CudyRouterDataUpdateCoordinator], SensorEntity
):
    """Implementation of a Cudy Router device sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: CudyRouterDataUpdateCoordinator,
        name: str | None,
        device_id: str,
        descriptionTemplate: CudyRouterSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        description = CudyRouterSensorEntityDescription(
            module=descriptionTemplate.module,
            key=descriptionTemplate.key,
            icon=descriptionTemplate.icon,
            state_class=descriptionTemplate.state_class,
            entity_category=descriptionTemplate.entity_category,
            native_unit_of_measurement=descriptionTemplate.native_unit_of_measurement,
            name_suffix=descriptionTemplate.name_suffix,
        )
        self.entity_description = description
        self.device_key = device_id
        self._sensor_name_prefix = as_name(device_id)
        self._attrs: dict[str, Any] = {}
        self._attr_name = f"{device_id} {description.name_suffix}".strip()
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.config_entry.entry_id)},
            manufacturer="Cudy",
            name=name,
        )
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}-{self._sensor_name_prefix}-{description.key}"

    @property
    def native_value(self) -> StateType:
        """Return the state of the resources."""
        if not self.coordinator.data:
            return None
        device = (
            self.coordinator.data[MODULE_DEVICES]
            .get(SECTION_DETAILED)
            .get(self.device_key)
        )
        if not device:
            return None
        # For signal sensor, always return as string
        if self.entity_description.key == "signal":
            val = device.get("signal")
            return str(val) if val is not None else None
        return device.get(self.entity_description.key)

    @property
    def icon(self) -> str | None:
        # Only dynamic for presence, which is now a separate class
        return self.entity_description.icon


class CudyRouterSensor(
    CoordinatorEntity[CudyRouterDataUpdateCoordinator], SensorEntity
):
    """Implementation of a Cudy Router sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: CudyRouterDataUpdateCoordinator,
        name: str | None,
        sensor_name_prefix: str,
        description: CudyRouterSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._sensor_name_prefix = sensor_name_prefix
        self.entity_description = description
        self._attrs: dict[str, Any] = {}
        self._attr_name = f"{description.name_suffix}".strip()
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.config_entry.entry_id)},
            manufacturer="Cudy",
            name=name,
        )
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}-{sensor_name_prefix}-{description.key}"

    @property
    def native_value(self) -> StateType:
        """Return the state of the resources."""
        if not self.coordinator.data:
            return None
        module_data = self.coordinator.data.get(self.entity_description.module)
        if not module_data:
            return None
        data_entry = module_data.get(self.entity_description.key)
        return data_entry["value"] if data_entry and "value" in data_entry else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        if self.coordinator.data:
            module_data = self.coordinator.data.get(self.entity_description.module)
            if module_data:
                data_entry = module_data.get(self.entity_description.key)
                if data_entry:
                    attributes = data_entry.get("attributes")
                    if attributes:
                        self._attrs.update(attributes)
        return self._attrs


class CudyRouterSignalSensor(CudyRouterSensor):
    """Implementation of a Cudy Router sensor with dynamic icon."""

    @callback
    def async_write_ha_state(self) -> None:
        data = self.coordinator.data
        modem_data = data.get(MODULE_MODEM) if data and MODULE_MODEM in data else None
        value = None
        if modem_data and isinstance(modem_data, dict):
            signal_data = modem_data.get("signal")
            if signal_data and isinstance(signal_data, dict):
                value = signal_data.get("value")
        icon = "mdi:network-strength-outline"
        if not value:
            icon = "mdi:network-strength-off-outline"
        elif value == 1:
            icon = "mdi:network-strength-1"
        elif value == 2:
            icon = "mdi:network-strength-2"
        elif value == 3:
            icon = "mdi:network-strength-3"
        elif value == 4:
            icon = "mdi:network-strength-4"
        self._attr_icon = icon

        super().async_write_ha_state()


class CudyRouterPresenceSensor(CudyRouterDeviceSensor):
    """Presence sensor for a device connected to the Cudy Router."""
    @property
    def native_value(self) -> StateType:
        if not self.coordinator.data:
            return None
        device = (
            self.coordinator.data[MODULE_DEVICES]
            .get(SECTION_DETAILED)
            .get(self.device_key)
        )
        if not device:
            return None
        config_entry = getattr(self.coordinator, 'config_entry', None)
        timeout = 180
        signal_check = True
        if config_entry and hasattr(config_entry, 'options'):
            timeout = int(config_entry.options.get(OPTIONS_PRESENCE_TIMEOUT, 180))
            signal_check = config_entry.options.get(OPTIONS_PRESENCE_SIGNAL_CHECK, True)
            if isinstance(signal_check, str):
                signal_check = signal_check.lower() == "true"
        last_seen = device.get("last_seen")
        now_ts = datetime.now().timestamp()
        if last_seen and (now_ts - last_seen) <= timeout:
            connection = (device.get("connection") or "").lower()
            signal = device.get("signal")
            if connection == "wired":
                return "home"
            if signal_check:
                if signal and str(signal).strip() != "" and str(signal).strip() != "---":
                    return "home"
        return "not_home"

    @property
    def icon(self) -> str | None:
        state = self.native_value
        if state == "home":
            return "mdi:account-check"
        if state == "not_home":
            return "mdi:account-off"
        return self.entity_description.icon


class CudyRouterConnectedDevicesSensor(CudyRouterSensor):
    """Sensor that provides a list of all connected devices with their details."""

    @property
    def native_value(self) -> StateType:
        """Return the count of connected devices."""
        if not self.coordinator.data:
            return 0
        
        devices_data = self.coordinator.data.get(MODULE_DEVICES, {})
        connected_devices_data = devices_data.get("connected_devices", {})
        return connected_devices_data.get("value", 0)
