"""Weerplaza Switch Entities"""

from typing import Any
import logging
from homeassistant.components.switch import (
    SwitchEntity,
    SwitchEntityDescription,
    SwitchDeviceClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.components.switch.const import DOMAIN as SWITCH_DOMAIN
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import WeerplazaDataUpdateCoordinator
from .const import DOMAIN, DEFAULT_NAME, SHOW_MARKER, MANUFACTURER, NAME
from .entity import WeerplazaEntity

DESCRIPTIONS: list[SwitchEntityDescription] = [
    SwitchEntityDescription(
        key=SHOW_MARKER,
        translation_key=SHOW_MARKER,
        # device_class=SwitchDeviceClass.SWITCH,
        entity_category=EntityCategory.CONFIG,
    ),
]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Weerplaza switches based on a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[WeerplazaSwitch] = []

    # Add all numbers described above.
    for description in DESCRIPTIONS:
        entities.append(
            WeerplazaSwitch(
                coordinator=coordinator,
                entry_id=entry.entry_id,
                description=description,
            )
        )

    async_add_entities(entities)


class WeerplazaSwitch(WeerplazaEntity, SwitchEntity):
    # class WeerplazaSwitch(SwitchEntity):
    """Representation of a Weerplaza switch entity."""

    # _attr_has_entity_name = True
    _attr_device_class = SwitchDeviceClass.SWITCH

    def __init__(
        self,
        coordinator: WeerplazaDataUpdateCoordinator,
        entry_id: str,
        description: SwitchEntityDescription,
    ) -> None:
        """Initialize the switch entity."""
        super().__init__(
            coordinator=coordinator,
            description=description,
            entry_id=entry_id,
        )
        self.coordinator = coordinator
        self.entity_id = f"{SWITCH_DOMAIN}.{DEFAULT_NAME}_{description.key}"

    @property
    def is_on(self) -> bool | None:
        """Return if the switch is on."""
        key = self.entity_description.key
        if key == SHOW_MARKER:
            return self.coordinator.api.get_show_marker()
        return None

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        key = self.entity_description.key
        if key == SHOW_MARKER:
            self.coordinator.api.set_show_marker(True)
            await self.coordinator.api.async_request_refresh()
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        key = self.entity_description.key
        if key == SHOW_MARKER:
            self.coordinator.api.set_show_marker(False)
            await self.coordinator.api.async_request_refresh()
            self.async_write_ha_state()
