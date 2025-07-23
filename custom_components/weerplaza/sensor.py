from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.components.sensor.const import (
    DOMAIN as SENSOR_DOMAIN,
    SensorDeviceClass,
)
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN, DEFAULT_NAME
from .coordinator import WeerPlazaDataUpdateCoordinator

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
    """Set up Weer Plaza sensors based on a config entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    entities: list[WeerPlazaSensor] = []

    # Add all sensors described above.
    for description in DESCRIPTIONS:
        entities.append(
            WeerPlazaSensor(
                coordinator=coordinator,
                entry_id=config_entry.entry_id,
                description=description,
            )
        )

    async_add_entities(entities)


class WeerPlazaSensor(CoordinatorEntity[WeerPlazaDataUpdateCoordinator], SensorEntity):
    """Defines a Weer Plaza sensor."""

    def __init__(
        self,
        coordinator: WeerPlazaDataUpdateCoordinator,
        entry_id: str,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize Weer Plaza sensor."""
        super().__init__(coordinator=coordinator)
        self._attr_device_info = coordinator.device_info
        self._attr_has_entity_name = True
        self._attr_unique_id = f"{entry_id}-{DEFAULT_NAME} {description.key}"
        self.entity_description = description
        self.entity_id = f"{SENSOR_DOMAIN}.{DEFAULT_NAME} {description.key}"

    @property
    def native_value(self) -> StateType:  # type: ignore
        """Return the state of the sensor."""
        return self.coordinator.data.get(self.entity_description.key, None)
