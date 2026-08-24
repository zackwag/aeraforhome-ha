# Aera for Home - Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

Home Assistant custom integration for [Aera for Home](https://www.theaerastore.com/) smart fragrance diffusers.

## Features

- **Fan entity**: power on/off, intensity control with optimistic state updates
- **Schedule management**: enable/disable, start/end time, days, intensity per schedule slot
- **Session control**: start timed fragrance sessions (2, 4, or 8 hours)
- **Fragrance sensors**: current fragrance name, remaining percentage, fragrance code
- **QR code image**: generated QR code for the fragrance link (Mini devices)
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
| Intensity | `sensor` | Current intensity level (1-10 or 1-5 for Mini) |
| Session time remaining | `sensor` | Time left in active session; unit configurable (Aera 3/3.1/Mini) |
| Session | `select` | Start/stop timed sessions: Off, 2, 4, or 8 hours (Aera 3/3.1/Mini) |
| Session active | `binary_sensor` | Whether a timed session is currently running (Aera 3/3.1/Mini) |
| Fragrance code | `sensor` | 3-letter fragrance code for manual entry (Mini only) |
| Fragrance QR code | `image` | Generated QR code image for the fragrance (Mini only) |
| Cartridge | `binary_sensor` | Plugged in/Unplugged (full-size only) |

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

## Blueprints

### Aera Fragrance Schedule

A ready-made blueprint that replicates Aera app schedules in Home Assistant. Pick your diffuser, intensity, start/end time, and days — it creates a complete automation.

[![Import Blueprint](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fzackwag%2Faeraforhome-ha%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Faera_schedule.yaml)

Or manually: **Settings > Automations & Scenes > Blueprints > Import Blueprint** and paste:

```
https://github.com/zackwag/aeraforhome-ha/blob/main/blueprints/automation/aera_schedule.yaml
```

## Automation Examples

### Notify when fragrance is running low

```yaml
automation:
  - alias: "Aera fragrance low"
    trigger:
      - platform: numeric_state
        entity_id: sensor.living_room_aera_fragrance_remaining
        below: 20
    condition:
      - condition: not
        conditions:
          - condition: state
            entity_id: sensor.living_room_aera_fragrance_remaining
            state: "unknown"
    action:
      - action: notify.mobile_app
        data:
          title: "Aera Low Fragrance"
          message: "{{ state_attr('sensor.living_room_aera_fragrance_remaining', 'friendly_name') }} is at {{ states('sensor.living_room_aera_fragrance_remaining') }}%"
```

### Recreate a schedule in Home Assistant

You can replicate Aera app schedules using HA automations for more flexibility (presence-based, conditional, etc.). This example runs the diffuser from 8 PM to 10 PM on weekdays at intensity 9:

```yaml
automation:
  - alias: "Aera weekday evening on"
    trigger:
      - platform: time
        at: "20:00:00"
    condition:
      - condition: time
        weekday:
          - mon
          - tue
          - wed
          - thu
          - fri
    action:
      - action: fan.turn_on
        target:
          entity_id: fan.living_room_aera
        data:
          percentage: 90
  
  - alias: "Aera weekday evening off"
    trigger:
      - platform: time
        at: "22:00:00"
    condition:
      - condition: time
        weekday:
          - mon
          - tue
          - wed
          - thu
          - fri
    action:
      - action: fan.turn_off
        target:
          entity_id: fan.living_room_aera
```

### Run a session when you get home

Use presence detection to start a fragrance session only when someone is home:

```yaml
automation:
  - alias: "Aera welcome home"
    trigger:
      - platform: state
        entity_id: person.you
        to: "home"
    condition:
      - condition: state
        entity_id: fan.living_room_aera
        state: "off"
    action:
      - action: select.select_option
        target:
          entity_id: select.living_room_aera_session
        data:
          option: "2 hours"
```

### Turn off all diffusers at bedtime

```yaml
automation:
  - alias: "Aera bedtime off"
    trigger:
      - platform: time
        at: "22:30:00"
    action:
      - action: fan.turn_off
        target:
          entity_id:
            - fan.living_room_aera
            - fan.bedroom_aera
```

### Notify when cartridge is removed

```yaml
automation:
  - alias: "Aera cartridge removed"
    trigger:
      - platform: state
        entity_id: binary_sensor.living_room_aera_cartridge
        to: "off"
    action:
      - action: notify.mobile_app
        data:
          title: "Aera Cartridge Removed"
          message: "The fragrance cartridge was removed from {{ trigger.to_state.attributes.friendly_name }}"
```

## Diagnostics

Go to **Settings > Devices & Services > Aera for Home > 3-dot menu > Download diagnostics** to get a full dump of device state and schedule data for troubleshooting.

## Disclaimer

This is an unofficial integration with no affiliation to Aera, Prolitec, or Ayla Networks. It may break if the upstream API changes.
