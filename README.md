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

- Precipitation Radar
- Satellite
- Thunder

A latitude and longitude value can be set to show the marker on de images.

A switch is available to show/hide the marker

A service is available called "Force Update" to update the marker on the images after the latitude and/or longitude values changed.