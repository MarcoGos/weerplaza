"""Weerplaza Data Update Coordinator"""

from datetime import datetime, timedelta
import logging
from typing import Any
from zoneinfo import ZoneInfo

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.device_registry import DeviceInfo
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
    ) -> None:
        """Initialize."""
        self.api: WeerplazaApi = api
        self.platforms: list[str] = []
        self._hass = hass

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SYNC_INTERVAL),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data via api."""
        await self.api.async_get_new_images()
        return {
            "last_updated": datetime.now().replace(
                tzinfo=ZoneInfo(self._hass.config.time_zone)
            )
        }
