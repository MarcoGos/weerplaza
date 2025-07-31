"""Weerplaza Data Update Coordinator"""

from datetime import timedelta
import logging

from homeassistant import config_entries
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.core import HomeAssistant

from .api import WeerplazaApi
from .const import (
    DEFAULT_SYNC_INTERVAL,
    DOMAIN,
)

_LOGGER: logging.Logger = logging.getLogger(__package__)


class WeerplazaDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: WeerplazaApi,
        config_entry: config_entries.ConfigEntry,
    ) -> None:
        """Initialize."""
        self.api: WeerplazaApi = api

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SYNC_INTERVAL),
            config_entry=config_entry,
        )

    async def _async_update_data(self) -> None:
        """Update data via api."""
        await self.api.async_get_new_images()
