[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
![Install Stats][stats]

![Project Maintenance][maintenance-shield]
[![Community Forum][forum-shield]][forum]

# Weerplaza

This is a custom integration for Dutch Weerplaza. It will provide animated images such as percipitation radar, satellite and thunder images.

## Installation

Via HACS:

- Add the following custom repository as an integration:
    - MarcoGos/weerplaza
- Restart Home Assistant
- Add the integration to Home Assistant

## Setup

Nothing to setup.

## What to expect

The following images (cameras) will be registered:

- Rain Radar
- Satellite
- Thunder
- Hail
- Drizzle
- Rain and Clouds

The following sensors will be registered

- Latitude Marker
- Longitude Marker

The following switch will be registered

- Show/Hide Marker
    - This will automatically update all enabled images (cameras)

The following action will be registered

- "Force Update"
    - Update the marker on the images after the latitude and/or longitude values changed.

## Examples

![RainRadar](/assets/camera_weerplaza_rain_radar_example.jpg)
![Satellite](/assets/camera_weerplaza_satellite_example.jpg)



[commits-shield]: https://img.shields.io/github/commit-activity/y/MarcoGos/weerplaza.svg?style=for-the-badge
[commits]: https://github.com/MarcoGos/weerplaza/commits/main
[forum-shield]: https://img.shields.io/badge/community-forum-brightgreen.svg?style=for-the-badge
[forum]: https://community.home-assistant.io/
[maintenance-shield]: https://img.shields.io/badge/maintainer-%40MarcoGos-blue.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/MarcoGos/weerplaza.svg?style=for-the-badge
[releases]: https://github.com/MarcoGos/weerplaza/releases
[stats]: https://img.shields.io/badge/dynamic/json?color=41BDF5&logo=home-assistant&label=integration%20usage&suffix=%20installs&cacheSeconds=15600&url=https://analytics.home-assistant.io/custom_integrations.json&query=$.weerplaza.total&style=for-the-badge
