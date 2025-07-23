"""Constants for the Weer Plaza integration."""

from enum import Enum

NAME = "Weer Plaza"
DOMAIN = "weerplaza"
MANUFACTURER = "weerplaza"
MODEL = "Weer Plaza"

# Platforms
WEATHER = "weather"

DEFAULT_SYNC_INTERVAL = 300  # seconds

DEFAULT_NAME = NAME

MARKER_LATITUDE = "marker_latitude"
MARKER_LONGITUDE = "marker_longitude"
PRECIPITATION_RADAR = "precipitation_radar"
SATELLITE = "satellite"
THUNDER = "thunder"


class ImageType(Enum):
    """Enum for image types."""

    RADAR = "radar"
    SATELLITE = "satellite"
    THUNDER = "thunder"
