"""The Weerplaza integration."""

from __future__ import annotations
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import Platform
from homeassistant.exceptions import HomeAssistantError

from .api import WeerplazaApi
from .const import DOMAIN
from .coordinator import WeerplazaDataUpdateCoordinator
from .services import WeerplazaServicesSetup

PLATFORMS: list[Platform] = [
    Platform.CAMERA,
    Platform.NUMBER,
    Platform.SENSOR,
    Platform.SWITCH,
]

_LOGGER: logging.Logger = logging.getLogger(__package__)


async def _async_run_initial_refresh(
    coordinator: WeerplazaDataUpdateCoordinator,
) -> None:
    """Run first refresh in the background after setup completes."""
    try:
        await coordinator.async_config_entry_first_refresh()
    except HomeAssistantError:
        _LOGGER.exception("Initial Weerplaza refresh failed")


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Weerplaza from a config entry."""
    if hass.data.get(DOMAIN) is None:
        hass.data.setdefault(DOMAIN, {})

    _LOGGER.debug("entry.data: %s", entry.data)

    api = WeerplazaApi(hass)

    hass.data[DOMAIN][entry.entry_id] = coordinator = WeerplazaDataUpdateCoordinator(
        hass=hass,
        api=api,
        config_entry=entry,
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    hass.async_create_task(
        _async_run_initial_refresh(coordinator),
        name=f"{DOMAIN}_{entry.entry_id}_initial_refresh",
    )

    WeerplazaServicesSetup(hass, entry)

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
