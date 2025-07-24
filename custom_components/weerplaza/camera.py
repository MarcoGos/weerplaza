from dataclasses import dataclass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.components.camera import Camera, CameraEntityDescription
from homeassistant.components.camera.const import DOMAIN as CAMERA_DOMAIN
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DEFAULT_NAME,
    DOMAIN,
    PRECIPITATION_RADAR,
    SATELLITE,
    THUNDER,
    ImageType,
)
from .coordinator import WeerplazaDataUpdateCoordinator
from .entity import WeerplazaEntity


@dataclass(frozen=True, kw_only=True)
class WeerplazaCameraEntityDescription(CameraEntityDescription):
    """Describes Weerplaza camera entity."""

    key: str | None = None
    translation_key: str | None = None
    icon: str | None = None
    image_type: ImageType


DESCRIPTIONS: list[WeerplazaCameraEntityDescription] = [
    WeerplazaCameraEntityDescription(
        key=PRECIPITATION_RADAR,
        translation_key=PRECIPITATION_RADAR,
        icon="mdi:radar",
        image_type=ImageType.RADAR,
    ),
    WeerplazaCameraEntityDescription(
        key=SATELLITE,
        translation_key=SATELLITE,
        icon="mdi:satellite",
        image_type=ImageType.SATELLITE,
    ),
    WeerplazaCameraEntityDescription(
        key=THUNDER,
        translation_key=THUNDER,
        icon="mdi:lightning-bolt-outline",
        image_type=ImageType.THUNDER,
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Weerplaza cameras based on a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[WeerplazaCamera] = []

    # Add all images described above.
    for description in DESCRIPTIONS:
        entities.append(
            WeerplazaCamera(
                coordinator=coordinator,
                entry_id=entry.entry_id,
                description=description,
            )
        )

    async_add_entities(entities)


class WeerplazaCamera(WeerplazaEntity, Camera):
    """Defines the radar weer plaza camera."""

    def __init__(
        self,
        coordinator: WeerplazaDataUpdateCoordinator,
        entry_id: str,
        description: WeerplazaCameraEntityDescription,
    ) -> None:
        """Initialize Weerplaza camera."""
        Camera.__init__(self)
        super().__init__(
            coordinator=coordinator, description=description, entry_id=entry_id
        )

        self._attr_content_type = "image/gif"
        self.entity_id = f"{CAMERA_DOMAIN}.{DEFAULT_NAME}_{description.key}"

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        """Return bytes of camera image or None."""
        image_type = self.entity_description.image_type or ImageType.RADAR  # type: ignore
        image = await self.coordinator.api.async_get_animated_image(image_type)
        return image
