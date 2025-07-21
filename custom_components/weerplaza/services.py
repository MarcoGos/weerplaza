"""Global services file."""

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall

from .coordinator import WeerPlazaDataUpdateCoordinator

from .const import (
    DOMAIN,
    SERVICE_SET_MARKER_LOCATION,

)
from .coordinator import DataUpdateCoordinator

SET_MARKER_LOCATION_SCHEMA = vol.Schema(
    {
        vol.Required("latitude"): float,
        vol.Required("longitude"): float,
    }
)

class WeerPlazaServicesSetup:
    """Class to handle Integration Services."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialise services."""
        self.hass = hass
        self.config_entry = config_entry
        self.coordinator: WeerPlazaDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]

        self.setup_services()

    def setup_services(self):
        """Initialise the services in Hass."""

        self.hass.services.async_register(
            DOMAIN,
            SERVICE_SET_MARKER_LOCATION,
            self.set_marker_location,
            schema=SET_MARKER_LOCATION_SCHEMA,
        )

    async def set_marker_location(self, call: ServiceCall) -> None:
        """Set Marker Location service"""
        latitude = call.data.get("latitude")
        longitude = call.data.get("longitude")

        if latitude is None or longitude is None:
            raise ValueError("Latitude and Longitude must be provided.")

        api = self.coordinator.api
        await api.async_set_marker_location(latitude, longitude)
