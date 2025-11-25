# Cudy router integration for Home Assistant

This is an unofficial integration of Cudy routers for Home Assistant.

Unofficial means that this is not supported by Cudy, file issues here, not for them.

As the project is in a really early stage (and who knows if it will be ever more than that),
breaking modifications, like configuration or entity ID changes may be introduced.
Please keep that in mind when using it.

## Features

This integration logs in to the standard administration UI and
scrapes the information from HTML pages.
Although Cudy routers has a JSON RPC interface, it is not open for the public.

### Network & 4G/LTE Monitoring
- 4G/LTE connection sensors (network type, cell info, signal strength)
- RSSI, RSRP, RSRQ, SINR measurements
- Band information (carrier aggregation support)
- SIM slot detection

### Device Tracking & Presence Detection
- **Binary sensors** for device presence (perfect for automations!)
- **Device trackers** for integration with Home Assistant presence
- Individual device sensors with detailed information
- Configurable presence timeout and signal checking
- Support for both MAC address and hostname tracking

### Network Usage Monitoring
- Total connected devices count
- Individual device bandwidth usage (upload/download speeds)
- Top bandwidth users detection
- Connection type detection (Wired/2.4G/5G WiFi)
- WiFi signal strength per device

### Rich Device Attributes
All device entities include detailed attributes:
- IP address, MAC address, hostname
- Connection type (Wired/WiFi band)
- Current bandwidth usage
- WiFi signal strength
- Online time
- Last seen timestamp

## Installing

[![](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=r1ek&repository=ha-cudy-router&category=integration)

The easiest way to install is via HACS (Home Assistant Community Store). Add this repository as a custom repository in HACS, then search for "Cudy Router" and install.

Alternatively, you can manually put the `custom_components/cudy_router` folder into your Home Assistant `custom_components` folder.

## Configuration

After installation:

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for "Cudy Router"
4. Enter your router credentials:
   - **Host**: Your router's IP address (e.g., 192.168.10.1)
   - **Username**: Admin username
   - **Password**: Admin password

### Device Tracking Setup

To track specific devices and create presence sensors:

1. Go to the integration in **Settings** → **Devices & Services**
2. Click **Configure** on the Cudy Router integration
3. In the **Tracked devices** field, enter MAC addresses with optional friendly names:
   - Format: `FriendlyName=MAC` or just `MAC`
   - One per line, or comma-separated
   - Example:
     ```
     Steve=B4:FB:E3:BC:F0:13
     John=38:BE:AB:59:AC:17
     Camera=DC:B4:D9:C4:3D:5C
     ```
   - When Steve changes phones, just update: `Steve=NEW_MAC_ADDRESS`
4. Configure optional settings:
   - **Scan interval**: How often to poll the router (default: 15 seconds)
   - **Presence timeout**: How long before marking device as away (default: 180 seconds)
   - **Check signal strength**: Require valid WiFi signal for presence (default: enabled)

This will create:
- Binary sensors: `binary_sensor.cudyr_<friendly_name>_connectivity` (on/off)
- Device trackers: `device_tracker.cudy_router_<friendly_name>`
- Detailed sensors for each device (speed, signal, etc.)

**Example entities with friendly names:**
- `Steve=B4:FB:E3:BC:F0:13` creates: `binary_sensor.cudyr_steve_connectivity`
- Easy to use in automations - when Steve changes phones, just update the MAC!

## Using in Automations

See [AUTOMATIONS.md](AUTOMATIONS.md) for detailed examples including:
- Presence detection automations
- Bandwidth monitoring alerts
- Device connection notifications
- Looping through all connected devices
- And many more examples!

## Contributing

It started as my personal project to satisfy my own requirements, therefore
it is far from complete.

It is only tested with my own LT18 router and with my Home Assistant installation.
There's no guarantee that it's working on other systems. Feedback and pull requests are welcome.

For major changes, please open an issue first to discuss what you
would like to change.

The project uses the code style configuration from Home Assistant Core.

## License

[GNU GPLv3](https://www.gnu.org/licenses/gpl-3.0.en.html)
