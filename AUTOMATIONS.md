# Automation Examples for Cudy Router Integration

This document provides examples of how to use the Cudy Router integration entities in your Home Assistant automations.

## Available Entities

After configuring the integration and adding devices to track, you'll have:

### 1. Binary Sensors (NEW!)
- `binary_sensor.<device_id>_connectivity` - Individual device presence (on/off)
- `binary_sensor.cudyr_any_device_connected` - True if any device is connected

### 2. Device Trackers
- `device_tracker.cudy_device_<mac>` - Classic Home Assistant device tracker (home/not_home)

### 3. Sensors
- `sensor.cudyr_connected_devices` - Total count with all devices in attributes
- `sensor.cudyr_device_count` - Simple device count
- `sensor.<device>_presence` - Individual device presence sensor
- `sensor.<device>_upload_speed` - Upload speed in Mbps
- `sensor.<device>_download_speed` - Download speed in Mbps
- `sensor.<device>_signal` - WiFi signal strength
- And more...

## Example Automations

### 1. Notify When Specific Device Connects

Using the new **binary sensor** (recommended):

```yaml
automation:
  - alias: "Notify when phone connects to WiFi"
    trigger:
      - platform: state
        entity_id: binary_sensor.b4_fb_e3_bc_f0_13_connectivity
        to: "on"
    action:
      - service: notify.mobile_app
        data:
          title: "Phone Connected"
          message: "Your phone connected to WiFi at {{ now().strftime('%H:%M') }}"
```

### 2. Turn Off Lights When Everyone Leaves

```yaml
automation:
  - alias: "Turn off lights when no devices connected"
    trigger:
      - platform: state
        entity_id: binary_sensor.cudyr_any_device_connected
        to: "off"
        for:
          minutes: 5
    action:
      - service: light.turn_off
        target:
          entity_id: all
```

### 3. Alert on High Bandwidth Usage

```yaml
automation:
  - alias: "Alert on high download speed"
    trigger:
      - platform: numeric_state
        entity_id: sensor.camera_download_speed
        above: 10  # Mbps
        for:
          minutes: 2
    action:
      - service: notify.persistent_notification
        data:
          title: "High Bandwidth Alert"
          message: >
            Camera is using {{ states('sensor.camera_download_speed') }} Mbps download speed
```

### 4. Track Device Connection Time

Using attributes from binary sensor:

```yaml
automation:
  - alias: "Log device connection"
    trigger:
      - platform: state
        entity_id: binary_sensor.camera_connectivity
        to: "on"
    action:
      - service: logbook.log
        data:
          name: "Device Connected"
          message: >
            Camera connected via {{ state_attr('binary_sensor.camera_connectivity', 'connection_type') }}
            IP: {{ state_attr('binary_sensor.camera_connectivity', 'ip_address') }}
            Signal: {{ state_attr('binary_sensor.camera_connectivity', 'signal_strength') }}
```

### 5. Presence Detection for Multiple Devices

Check if any family member's device is home:

```yaml
template:
  - binary_sensor:
      - name: "Anyone Home"
        state: >
          {{
            is_state('binary_sensor.phone1_connectivity', 'on') or
            is_state('binary_sensor.phone2_connectivity', 'on') or
            is_state('binary_sensor.tablet_connectivity', 'on')
          }}
```

### 6. Loop Through All Connected Devices

Using the `sensor.cudyr_connected_devices` attributes:

```yaml
automation:
  - alias: "List all connected devices"
    trigger:
      - platform: time
        at: "09:00:00"
    action:
      - service: notify.persistent_notification
        data:
          title: "Connected Devices Report"
          message: >
            {% set devices = state_attr('sensor.cudyr_connected_devices', 'devices') %}
            {% if devices %}
              Total devices: {{ devices | length }}
              {% for device in devices %}
              - {{ device.hostname }} ({{ device.mac }})
                IP: {{ device.ip }}
                Connection: {{ device.connection }}
                Signal: {{ device.signal }}
              {% endfor %}
            {% else %}
              No devices connected
            {% endif %}
```

### 7. Find Devices by MAC Address in Attributes

Template to check if a specific MAC is connected:

```yaml
template:
  - binary_sensor:
      - name: "My Phone Connected"
        state: >
          {% set devices = state_attr('sensor.cudyr_connected_devices', 'devices') %}
          {% set my_mac = 'B4:FB:E3:BC:F0:13' %}
          {{ devices | selectattr('mac', 'eq', my_mac) | list | length > 0 }}
```

### 8. Alert on Weak Signal

```yaml
automation:
  - alias: "Alert on weak WiFi signal"
    trigger:
      - platform: template
        value_template: >
          {% set signal = state_attr('binary_sensor.camera_connectivity', 'signal_strength') %}
          {% if signal != '---' and 'dB' in signal %}
            {{ signal.replace('dB', '') | int < 25 }}
          {% else %}
            false
          {% endif %}
    condition:
      - condition: state
        entity_id: binary_sensor.camera_connectivity
        state: "on"
    action:
      - service: notify.mobile_app
        data:
          title: "Weak WiFi Signal"
          message: >
            Camera has weak signal: {{ state_attr('binary_sensor.camera_connectivity', 'signal_strength') }}
```

### 9. Guest Network Monitoring

Track when new/unknown devices connect:

```yaml
automation:
  - alias: "Unknown device connected"
    trigger:
      - platform: state
        entity_id: sensor.cudyr_device_count
    condition:
      - condition: template
        value_template: >
          {% set devices = state_attr('sensor.cudyr_connected_devices', 'devices') %}
          {% set known_macs = ['B4:FB:E3:BC:F0:13', '38:BE:AB:59:AC:17'] %}
          {% set unknown = devices | rejectattr('mac', 'in', known_macs) | list %}
          {{ unknown | length > 0 }}
    action:
      - service: notify.mobile_app
        data:
          title: "Unknown Device Alert"
          message: "A new device connected to your network"
```

### 10. Conditional Actions Based on Connection Type

```yaml
automation:
  - alias: "Device reconnected notification"
    trigger:
      - platform: state
        entity_id: binary_sensor.phone_connectivity
        from: "off"
        to: "on"
    action:
      - choose:
          - conditions:
              - condition: template
                value_template: >
                  {{ 'wired' in state_attr('binary_sensor.phone_connectivity', 'connection_type') | lower }}
            sequence:
              - service: notify.mobile_app
                data:
                  message: "Phone connected via Ethernet"
          - conditions:
              - condition: template
                value_template: >
                  {{ '5g' in state_attr('binary_sensor.phone_connectivity', 'connection_type') | lower }}
            sequence:
              - service: notify.mobile_app
                data:
                  message: "Phone connected via 5G WiFi"
        default:
          - service: notify.mobile_app
            data:
              message: "Phone connected via 2.4G WiFi"
```

## Tips for Automations

1. **Use Binary Sensors for Presence**: The new binary sensors are cleaner for automations than checking "home"/"not_home" strings.

2. **Access Rich Attributes**: Binary sensors include detailed info (IP, MAC, signal, speed) in their attributes.

3. **Loop Through Devices**: Use `sensor.cudyr_connected_devices` attributes when you need to check all devices.

4. **Adjust Timeout**: Configure the presence timeout in integration options to control how quickly devices are marked as away.

5. **Signal Check Option**: Disable signal checking for faster presence detection (useful for automations that need quick response).

## Helpers and Templates

### Create a Helper to Count Wireless Devices

```yaml
template:
  - sensor:
      - name: "WiFi Device Count"
        state: >
          {% set devices = state_attr('sensor.cudyr_connected_devices', 'devices') %}
          {{ devices | selectattr('connection', 'search', 'WiFi|2.4G|5G', ignorecase=true) | list | length }}
```

### Track Specific Device Last Seen

```yaml
template:
  - sensor:
      - name: "Phone Last Seen"
        state: >
          {% set last_seen = state_attr('binary_sensor.phone_connectivity', 'last_seen_seconds_ago') %}
          {% if last_seen is not none %}
            {{ (last_seen / 60) | round(0) }} minutes ago
          {% else %}
            Never
          {% endif %}
```

## Need Help?

- Check the [main README](README.md) for configuration instructions
- Report issues at: https://github.com/r1ek/ha-cudy-router/issues
