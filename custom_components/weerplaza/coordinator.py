from datetime import timedelta
from typing import Any
import logging

from homeassistant.helpers.update_coordinator import UpdateFailed, DataUpdateCoordinator
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.core import HomeAssistant

from .api import WeerPlazaApi
from .const import (
    DEFAULT_SYNC_INTERVAL,
    DOMAIN,
)

_LOGGER: logging.Logger = logging.getLogger(__package__)


class WeerPlazaDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    def __init__(
        self, hass: HomeAssistant, client: WeerPlazaApi, device_info: DeviceInfo
    ) -> None:
        """Initialize."""
        self.api: WeerPlazaApi = client
        self.platforms: list[str] = []
        self.last_updated = None
        self.device_info = device_info
        self._hass = hass

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SYNC_INTERVAL),
        )

    async def _async_update_data(self) -> None:
        """Update data via library."""
        # try:
        await self.api.async_get_latest_image()
        # except Exception as exception:
        #     _LOGGER.error(
        #         "Error WeerPlazaDataUpdateCoordinator _async_update_data: %s", exception
        #     )
        #     raise UpdateFailed() from exception
