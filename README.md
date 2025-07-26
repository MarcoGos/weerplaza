![Version](https://img.shields.io/github/v/release/MarcoGos/weerplaza?include_prereleases)

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

The following sensors will be registered

- Latitude Marker
- Longitude Marker

The following switch will be registered

- Show/Hide Marker
    - This will automatically update all enabled images (cameras)

The following action will be registed

- "Force Update"
    - Update the marker on the images after the latitude and/or longitude values changed.

## Examples

![RainRadar](/assets/camera_weerplaza_rain_radar_example.jpg)
![Satellite](/assets/camera_weerplaza_satellite_example.jpg)