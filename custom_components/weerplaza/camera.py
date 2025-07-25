"""Weerplaza Camera Component for Home Assistant."""

from dataclasses import dataclass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.components.camera import Camera, CameraEntityDescription
from homeassistant.components.camera.const import DOMAIN as CAMERA_DOMAIN
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DEFAULT_NAME,
    DOMAIN,
    RAIN_RADAR,
    SATELLITE,
    THUNDER,
    HAIL,
    DRIZZLE_SNOW,
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
    entity_registry_enabled_default: bool = True
    entity_registry_visible_default: bool = True


DESCRIPTIONS: list[WeerplazaCameraEntityDescription] = [
    WeerplazaCameraEntityDescription(
        key=RAIN_RADAR,
        translation_key=RAIN_RADAR,
        icon="mdi:radar",
        image_type=ImageType.RAIN_RADAR,
    ),
    WeerplazaCameraEntityDescription(
        key=SATELLITE,
        translation_key=SATELLITE,
        icon="mdi:satellite",
        image_type=ImageType.SATELLITE,
        entity_registry_enabled_default=False,
        entity_registry_visible_default=False,
    ),
    WeerplazaCameraEntityDescription(
        key=THUNDER,
        translation_key=THUNDER,
        icon="mdi:lightning-bolt-outline",
        image_type=ImageType.THUNDER,
        entity_registry_enabled_default=False,
        entity_registry_visible_default=False,
    ),
    WeerplazaCameraEntityDescription(
        key=HAIL,
        translation_key=HAIL,
        icon="mdi:weather-hail",
        image_type=ImageType.HAIL,
        entity_registry_enabled_default=False,
        entity_registry_visible_default=False,
    ),
    WeerplazaCameraEntityDescription(
        key=DRIZZLE_SNOW,
        translation_key=DRIZZLE_SNOW,
        icon="mdi:weather-rainy",
        image_type=ImageType.DRIZZLE_SNOW,
        entity_registry_enabled_default=False,
        entity_registry_visible_default=False,
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
        image_type = self.entity_description.image_type or ImageType.RAIN_RADAR  # type: ignore
        image = await self.coordinator.api.async_get_animated_image(image_type)
        return image

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        await super().async_added_to_hass()
        self.coordinator.api.register_camera(self.entity_description.image_type)

    async def async_will_remove_from_hass(self) -> None:
        """Run when entity will be removed from hass."""
        await super().async_will_remove_from_hass()
        self.coordinator.api.unregister_camera(self.entity_description.image_type)
