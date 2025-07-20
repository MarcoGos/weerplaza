from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.components.image import (
    ImageEntity,
    ImageEntityDescription,
)
from homeassistant.components.image.const import DOMAIN as IMAGE_DOMAIN
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DEFAULT_NAME, DOMAIN
from .coordinator import WeerPlazaDataUpdateCoordinator

DESCRIPTIONS: list[ImageEntityDescription] = [
    ImageEntityDescription(key="radar", translation_key="radar", icon="mdi:radar")
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Weer Plaza images based on a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[WeerPlazaImage] = []

    # Add all images described above.
    for description in DESCRIPTIONS:
        entities.append(
            WeerPlazaImage(
                coordinator=coordinator,
                entry_id=entry.entry_id,
                description=description,
                hass=hass,
            )
        )

    async_add_entities(entities)


class WeerPlazaImage(CoordinatorEntity[WeerPlazaDataUpdateCoordinator], ImageEntity):
    """Defines the radar weer plaza image."""

    _attr_has_entity_name = True
    _attr_content_type = "image/gif"

    def __init__(
        self,
        coordinator: WeerPlazaDataUpdateCoordinator,
        entry_id: str,
        description: ImageEntityDescription,
        hass: HomeAssistant,
    ) -> None:
        """Initialize Weer Plaza image."""
        ImageEntity.__init__(self, hass)
        super().__init__(coordinator=coordinator)

        self.entity_description = description
        self.entity_id = f"{IMAGE_DOMAIN}.{DEFAULT_NAME}_{description.key}".lower()
        self._attr_unique_id = f"{entry_id}-{DEFAULT_NAME} {description.key}"

    def image(self) -> bytes | None:
        """Return bytes of image or None."""
        if image := self.coordinator.get_latest_image():
            return image

        return None
