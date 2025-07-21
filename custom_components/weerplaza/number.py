"""Sensor setup for our Integration."""

import logging

from homeassistant.components.number import (
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.components.number.const import (
    DOMAIN as NUMBER_DOMAIN,
    NumberDeviceClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import DEGREE, EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DEFAULT_NAME, DOMAIN
from .coordinator import WeerPlazaDataUpdateCoordinator

_LOGGER: logging.Logger = logging.getLogger(__package__)


def get_number_descriptions() -> list[NumberEntityDescription]:
    """Return the number descriptions for the specified model."""
    descriptions: list[NumberEntityDescription] = [
        NumberEntityDescription(
            key="latitude",
            translation_key="latitude",
            icon="mdi:latitude",
            device_class=NumberDeviceClass.WIND_DIRECTION,
            entity_category=EntityCategory.CONFIG,
            mode=NumberMode.BOX,
        ),
        NumberEntityDescription(
            key="longitude",
            translation_key="longitude",
            icon="mdi:longitude",
            native_unit_of_measurement=DEGREE,
            device_class=NumberDeviceClass.WIND_DIRECTION,
            entity_category=EntityCategory.CONFIG,
            mode=NumberMode.BOX,
        ),
    ]
    return descriptions


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Davis Vantage sensors based on a config entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    entities: list[WeerPlazaNumber] = []

    # Add all meter numebers described above.
    for description in get_number_descriptions():
        entities.append(
            WeerPlazaNumber(
                coordinator=coordinator,
                entry_id=config_entry.entry_id,
                description=description,
            )
        )

    async_add_entities(entities)


class WeerPlazaNumber(CoordinatorEntity[WeerPlazaDataUpdateCoordinator], NumberEntity):
    """Defines a Davis Vantage sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: WeerPlazaDataUpdateCoordinator,
        entry_id: str,
        description: NumberEntityDescription,
    ) -> None:
        """Initialize Davis Vantage sensor."""
        super().__init__(coordinator=coordinator)
        self.entity_description = description
        self.entity_id = f"{NUMBER_DOMAIN}.{DEFAULT_NAME} {description.key}".lower()
        self._attr_unique_id = f"{entry_id}-{DEFAULT_NAME} {description.key}"
        self._attr_device_info = coordinator.device_info

    async def async_set_native_value(self, value: float) -> None:
        _LOGGER.warning(
            "Setting value for %s to %s", self.entity_description.key, value
        )
        if self.entity_description.key == "latitude":
            await self.coordinator.api.async_set_marker_location(value, None)
        elif self.entity_description.key == "longitude":
            await self.coordinator.api.async_set_marker_location(None, value)
