# Aera for Home - Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

Home Assistant custom integration for [Aera for Home](https://www.theaerastore.com/) smart fragrance diffusers.

## Features

- **Fan entity**: power on/off, intensity control with optimistic state updates
- **Schedule management**: enable/disable, start/end time, days, intensity per schedule slot
- **Session control**: start timed fragrance sessions (2, 4, or 8 hours)
- **Fragrance sensors**: current fragrance name, remaining percentage, fragrance code
- **QR code image**: generated QR code for the fragrance link (Mini devices)
- **Eject button**: remotely eject the fragrance cartridge (full-size devices)
- **Device monitoring**: connectivity status, cartridge presence, error/problem detection
- **Diagnostics**: full device state dump for troubleshooting
- **Reauth flow**: automatic re-authentication prompt when credentials expire
- Supports all Aera device types: Aera 1, 2, 3, 3.1, and Mini
- Room names from the Aera app auto-suggest Home Assistant areas
- New devices discovered automatically without reloading
- Efficient polling: device state every 60s, schedules every 5 minutes

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click the three dots menu and select "Custom repositories"
3. Add `https://github.com/zackwag/aeraforhome-ha` as an Integration
4. Search for "Aera for Home" and install
5. Restart Home Assistant

### Manual

1. Copy `custom_components/aeraforhome` to your `config/custom_components/` directory
2. Restart Home Assistant

## Configuration

1. Go to **Settings > Devices & Services > Add Integration**
2. Search for "Aera for Home"
3. Enter your Aera account email and password

## Entities

Each Aera device creates:

| Entity | Type | Description |
|--------|------|-------------|
| Diffuser | `fan` | Power on/off, intensity (mapped to percentage) |
| Connectivity | `binary_sensor` | Connected/Disconnected (online status) |
| Problem | `binary_sensor` | On when device reports an error condition |
| Fragrance | `sensor` | Current fragrance name |
| Fragrance remaining | `sensor` | Percentage remaining (0-100%) |
| Session time remaining | `sensor` | Minutes left in active session (Aera 3/3.1/Mini) |
| Session | `select` | Start/stop timed sessions: Off, 2, 4, or 8 hours (Aera 3/3.1/Mini) |
| Fragrance code | `sensor` | 3-letter fragrance code for manual entry (Mini only) |
| Fragrance QR code | `image` | Generated QR code image for the fragrance (Mini only) |
| Cartridge | `binary_sensor` | Plugged in/Unplugged (full-size only) |
| Eject cartridge | `button` | Eject the cartridge; unavailable if none inserted (full-size only) |

Each active schedule slot adds:

| Entity | Type | Description |
|--------|------|-------------|
| Schedule N | `switch` | Enable/disable the schedule |
| Schedule N start time | `time` | When the schedule starts |
| Schedule N end time | `time` | When the schedule ends |
| Schedule N days | `select` | Every day, Weekdays, or Weekends |
| Schedule N intensity | `number` | Fragrance intensity level (slider) |

## Services

### `aeraforhome.create_schedule`

Create a new fragrance schedule on a device.

| Field | Required | Description |
|-------|----------|-------------|
| `entity_id` | Yes | Any entity belonging to the target device |
| `start_time` | Yes | Start time (HH:MM:SS) |
| `end_time` | Yes | End time (HH:MM:SS) |
| `days` | No | `every_day` (default), `weekdays`, or `weekends` |
| `intensity` | No | 1-10 (default: 5) |

### `aeraforhome.delete_schedule`

Delete (deactivate) a schedule.

| Field | Required | Description |
|-------|----------|-------------|
| `entity_id` | Yes | The schedule switch entity to delete |

## Diagnostics

Go to **Settings > Devices & Services > Aera for Home > 3-dot menu > Download diagnostics** to get a full dump of device state and schedule data for troubleshooting.

## Disclaimer

This is an unofficial integration with no affiliation to Aera, Prolitec, or Ayla Networks. It may break if the upstream API changes.
