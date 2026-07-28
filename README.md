# Aera for Home - Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

Home Assistant custom integration for [Aera for Home](https://www.theaerastore.com/) smart fragrance diffusers.

## Features

- **Fan entity** per device: power on/off, intensity control via speed percentage
- **Fragrance sensor**: shows the current fragrance name
- **Remaining sensor**: shows fragrance remaining percentage
- Supports all Aera device types: Aera 1, 2, 3, 3.1, and Mini
- User-assigned room names from the Aera app are used as device names
- Fragrance names resolved from the Aera catalog (including Mini short codes)

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
| Fan | `fan` | Power on/off, intensity (1-10 or 1-5 mapped to percentage) |
| Fragrance | `sensor` | Current fragrance name |
| Fragrance remaining | `sensor` | Percentage remaining (0-100%) |

## Disclaimer

This is an unofficial integration with no affiliation to Aera, Prolitec, or Ayla Networks. It may break if the upstream API changes.
