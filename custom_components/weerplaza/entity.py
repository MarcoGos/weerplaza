"""WeerPlaza Entity Base Class"""

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DEFAULT_NAME, DOMAIN, MANUFACTURER, NAME
from .coordinator import WeerPlazaDataUpdateCoordinator


class WeerPlazaEntity(CoordinatorEntity[WeerPlazaDataUpdateCoordinator]):
    """Base class for Weer Plaza entities."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: WeerPlazaDataUpdateCoordinator,
        entity_description: EntityDescription,
        entry_id: str,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self.entity_description = entity_description
        self.device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            manufacturer=MANUFACTURER,
            name=NAME,
        )
        self._attr_unique_id = f"{entry_id}-{DEFAULT_NAME} {entity_description.key}"
