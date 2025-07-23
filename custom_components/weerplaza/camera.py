from dataclasses import dataclass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.components.camera import Camera, CameraEntityDescription
from homeassistant.components.camera.const import DOMAIN as CAMERA_DOMAIN
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DEFAULT_NAME, DOMAIN
from .coordinator import WeerPlazaDataUpdateCoordinator


@dataclass(frozen=True)
class WeerPlazaCameraEntityDescription(CameraEntityDescription):
    """Describes Weer Plaza camera entity."""

    key: str | None = None
    translation_key: str | None = None
    icon: str | None = None
    image_type: str | None = None  # Default type, can be overridden


DESCRIPTIONS: list[WeerPlazaCameraEntityDescription] = [
    WeerPlazaCameraEntityDescription(
        key="animated_radar",
        translation_key="animated_radar",
        icon="mdi:radar",
        image_type="radar",
    ),
    WeerPlazaCameraEntityDescription(
        key="animated_satellite",
        translation_key="animated_satellite",
        icon="mdi:satellite",
        image_type="satellite",
    ),
    WeerPlazaCameraEntityDescription(
        key="animated_thunder",
        translation_key="animated_thunder",
        icon="mdi:lightning-bolt-outline",
        image_type="thunder",
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Weer Plaza cameras based on a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[WeerPlazaCamera] = []

    # Add all images described above.
    for description in DESCRIPTIONS:
        entities.append(
            WeerPlazaCamera(
                coordinator=coordinator,
                entry_id=entry.entry_id,
                description=description,
                hass=hass,
            )
        )

    async_add_entities(entities)


class WeerPlazaCamera(CoordinatorEntity[WeerPlazaDataUpdateCoordinator], Camera):
    """Defines the radar weer plaza camera."""

    _attr_has_entity_name = True
    _attr_content_type = "image/gif"
    entity_description: WeerPlazaCameraEntityDescription

    def __init__(
        self,
        coordinator: WeerPlazaDataUpdateCoordinator,
        entry_id: str,
        description: WeerPlazaCameraEntityDescription,
        hass: HomeAssistant,
    ) -> None:
        """Initialize Weer Plaza camera."""
        Camera.__init__(self)
        super().__init__(coordinator=coordinator)

        self.entity_description = description
        self.entity_id = f"{CAMERA_DOMAIN}.{DEFAULT_NAME}_{description.key}".lower()
        self._attr_unique_id = f"{entry_id}-{DEFAULT_NAME} {description.key}"
        self._hass = hass
        self._attr_device_info = coordinator.device_info

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        """Return bytes of camera image or None."""
        image_type = self.entity_description.image_type or "radar"
        image = await self.coordinator.api.async_get_animated_image(image_type)
        return image
