"""Constants for the Weerplaza integration."""

from enum import Enum

NAME = "Weerplaza"
DOMAIN = NAME.lower()
MANUFACTURER = NAME

DEFAULT_SYNC_INTERVAL = 300  # seconds

DEFAULT_NAME = NAME.lower()

MARKER_LATITUDE = "marker_latitude"
MARKER_LONGITUDE = "marker_longitude"
SHOW_MARKER = "show_marker"
PRECIPITATION_RADAR = "precipitation_radar"
SATELLITE = "satellite"
THUNDER = "thunder"


class ImageType(Enum):
    """Enum for image types."""

    RADAR = "radar"
    SATELLITE = "satellite"
    THUNDER = "thunder"
