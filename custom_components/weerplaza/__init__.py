"""The Weer Plaza integration."""

from __future__ import annotations
from typing import Any
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.const import Platform

from .api import WeerPlazaApi
from .const import DOMAIN, NAME, MANUFACTURER
from .coordinator import WeerPlazaDataUpdateCoordinator
from .services import WeerPlazaServicesSetup

PLATFORMS: list[Platform] = [Platform.CAMERA, Platform.NUMBER, Platform.SENSOR]

_LOGGER: logging.Logger = logging.getLogger(__package__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Weer Plaza from a config entry."""
    if hass.data.get(DOMAIN) is None:
        hass.data.setdefault(DOMAIN, {})

    _LOGGER.debug("entry.data: %s", entry.data)

    api = WeerPlazaApi(hass, hass.config.latitude, hass.config.longitude)

    hass.data[DOMAIN][entry.entry_id] = coordinator = WeerPlazaDataUpdateCoordinator(
        hass=hass,
        api=api,
    )

    await coordinator.async_config_entry_first_refresh()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    WeerPlazaServicesSetup(hass, entry)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unloaded := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unloaded


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
