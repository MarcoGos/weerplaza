"""Weerplaza Number Entities"""

from homeassistant.components.number import NumberEntity, NumberEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.components.number.const import DOMAIN as NUMBER_DOMAIN, NumberMode
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import WeerplazaDataUpdateCoordinator
from .const import DOMAIN, DEFAULT_NAME, MARKER_LATITUDE, MARKER_LONGITUDE
from .entity import WeerplazaEntity

DESCRIPTIONS: list[NumberEntityDescription] = [
    NumberEntityDescription(
        key=MARKER_LATITUDE,
        translation_key=MARKER_LATITUDE,
        entity_category=EntityCategory.CONFIG,
        icon="mdi:latitude",
        native_min_value=-180,
        native_max_value=180,
        mode=NumberMode.BOX,
    ),
    NumberEntityDescription(
        key=MARKER_LONGITUDE,
        translation_key=MARKER_LONGITUDE,
        entity_category=EntityCategory.CONFIG,
        icon="mdi:longitude",
        native_min_value=-90,
        native_max_value=90,
        mode=NumberMode.BOX,
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Weerplaza numbers based on a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[WeerplazaNumber] = []

    # Add all numbers described above.
    for description in DESCRIPTIONS:
        entities.append(
            WeerplazaNumber(
                coordinator=coordinator,
                entry_id=entry.entry_id,
                description=description,
            )
        )

    async_add_entities(entities)


class WeerplazaNumber(WeerplazaEntity, NumberEntity):
    """Representation of a Weerplaza number entity."""

    def __init__(
        self,
        coordinator: WeerplazaDataUpdateCoordinator,
        entry_id: str,
        description: NumberEntityDescription,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(
            coordinator=coordinator, description=description, entry_id=entry_id
        )
        self.entity_id = f"{NUMBER_DOMAIN}.{DEFAULT_NAME}_{description.key}"

    @property
    def native_value(self) -> float | None:
        """Return the current value of the number."""
        latitude, longitude = self.coordinator.api.async_get_marker_location()
        key = self.entity_description.key
        if key == MARKER_LATITUDE:
            return latitude
        elif key == MARKER_LONGITUDE:
            return longitude
        return None

    async def async_set_native_value(self, value: float) -> None:
        """Set the number value."""
        latitude, longitude = self.coordinator.api.async_get_marker_location()
        key = self.entity_description.key
        if key == MARKER_LATITUDE:
            latitude = value
        elif key == MARKER_LONGITUDE:
            longitude = value
        await self.coordinator.api.async_set_marker_location(latitude, longitude)
        self.async_write_ha_state()
