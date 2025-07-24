"""Weerplaza Sensor Entities"""

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.components.sensor.const import (
    DOMAIN as SENSOR_DOMAIN,
    SensorDeviceClass,
)
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from .const import DOMAIN, DEFAULT_NAME
from .coordinator import WeerplazaDataUpdateCoordinator
from .entity import WeerplazaEntity

DESCRIPTIONS: list[SensorEntityDescription] = [
    SensorEntityDescription(
        key="last_updated",
        translation_key="last_updated",
        icon="mdi:clock-outline",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
    )
]


async def async_setup_entry(
    hass,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Weerplaza sensors based on a config entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    entities: list[WeerplazaSensor] = []

    # Add all sensors described above.
    for description in DESCRIPTIONS:
        entities.append(
            WeerplazaSensor(
                coordinator=coordinator,
                entry_id=config_entry.entry_id,
                description=description,
            )
        )

    async_add_entities(entities)


class WeerplazaSensor(WeerplazaEntity, SensorEntity):
    """Defines a Weerplaza sensor."""

    def __init__(
        self,
        coordinator: WeerplazaDataUpdateCoordinator,
        entry_id: str,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize Weerplaza sensor."""
        super().__init__(
            coordinator=coordinator,
            description=description,
            entry_id=entry_id,
        )
        self.entity_id = f"{SENSOR_DOMAIN}.{DEFAULT_NAME} {description.key}"

    @property
    def native_value(self) -> StateType:  # type: ignore
        """Return the state of the sensor."""
        return self.coordinator.data.get(self.entity_description.key, None)
