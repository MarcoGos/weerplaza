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
LAST_UPDATED = "last_updated"
RAIN_RADAR = "rain_radar"
SATELLITE = "satellite"
THUNDER = "thunder"
HAIL = "hail"
DRIZZLE_SNOW = "drizzle_snow"
RADAR_SATELLITE = "radar_satellite"
RAIN_LIGHTNING = "rain_lightning"


class ImageType(Enum):
    """Enum for image types."""

    RAIN_RADAR = RAIN_RADAR
    SATELLITE = SATELLITE
    THUNDER = THUNDER
    HAIL = HAIL
    DRIZZLE_SNOW = DRIZZLE_SNOW
    RADAR_SATELLITE = RADAR_SATELLITE
    RAIN_LIGHTNING = RAIN_LIGHTNING
