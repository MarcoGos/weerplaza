![Version](https://img.shields.io/github/v/release/MarcoGos/weerplaza?include_prereleases)

# Weer Plaza

This is a custom integration for Dutch Weer Plaza. It will provide animated images such as percipitation radar, satellite and thunder images.

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

- Radar Camera
- Satellite Camera
- Thunder Camera

A latitude and longitude value can be set to show a marker on de images.

A service is available called "Force Update" to update the marker on the images after the latitude and/or longitude values changed.