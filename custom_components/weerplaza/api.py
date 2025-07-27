"""Weerplaza API client for Home Assistant."""

from typing import Any

import os
import glob
import logging
from zoneinfo import ZoneInfo
from io import BytesIO
from shutil import rmtree

from datetime import datetime, timedelta
import aiohttp
from pytz import timezone

import async_timeout
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.storage import STORAGE_DIR
from PIL import Image, ImageFile, ImageDraw, ImageFont
import imageio.v2 as imageio

from .const import (
    DOMAIN,
    MARKER_LATITUDE,
    MARKER_LONGITUDE,
    SHOW_MARKER,
    LAST_UPDATED,
    ImageType,
)
from .tools import calculate_mercator_position

TIMEOUT = 10
IMAGES_TO_KEEP = 18

IMAGE_URLS = {
    ImageType.RAIN_RADAR: "https://api.meteoplaza.com/v2/splash/10728/obs?access_token=weerplaza&usehd=1",
    ImageType.SATELLITE: "https://api.meteoplaza.com/v2/splash/10728/sat?access_token=weerplaza&usehd=1",
    ImageType.THUNDER: "https://api.meteoplaza.com/v2/splash/10728/thunder?access_token=weerplaza&usehd=1",
    ImageType.HAIL: "https://api.meteoplaza.com/v2/splash/10728/hail?access_token=weerplaza&usehd=1",
    ImageType.DRIZZLE_SNOW: "https://api.meteoplaza.com/v2/splash/10728/preciptype?access_token=weerplaza&usehd=1",
    ImageType.RADAR_SATELLITE: "https://api.meteoplaza.com/v2/splash/10728/radsat?access_token=weerplaza&usehd=1",
}

_LOGGER: logging.Logger = logging.getLogger(__package__)


class WeerplazaApi:
    """Weerplaza API client to fetch weather images."""

    _headers: dict[str, str] = {"User-Agent": "Home Assistant (Weer Plaza)"}
    _images: dict[ImageType, Any] = {}
    _storage_paths: dict[ImageType, str] = {}
    _timezone: Any = None
    _settings: dict[str, Any] = {}
    _cameras: dict[ImageType, bool] = {}

    def __init__(self, hass: HomeAssistant) -> None:
        self._hass = hass
        self._timezone = self._hass.config.time_zone
        self._session = async_get_clientsession(self._hass)
        self.set_setting(
            MARKER_LONGITUDE,
            (
                self._hass.data[DOMAIN].get(MARKER_LONGITUDE, None)
                or self._hass.config.longitude
            ),
        )
        self.set_setting(
            MARKER_LATITUDE,
            (
                self._hass.data[DOMAIN].get(MARKER_LATITUDE, None)
                or self._hass.config.latitude
            ),
        )
        self.set_setting(SHOW_MARKER, hass.data[DOMAIN].get(SHOW_MARKER, True))
        for image_type in IMAGE_URLS:
            self._images[image_type] = []
            self._cameras[image_type] = False
            self._storage_paths[image_type] = self._hass.config.path(
                STORAGE_DIR, DOMAIN, image_type.value
            )

    def set_setting(self, key: str, value: Any, store: bool = False) -> None:
        """Set a setting for the API."""
        self._settings[key] = value
        if store:
            self._hass.data[DOMAIN][key] = value
        _LOGGER.debug("Setting parameter %s to %s", key, value)

    def setting(self, key: str) -> Any:
        """Get a setting for the API."""
        return self._settings.get(key, None)

    async def async_get_new_images(self) -> None:
        """Fetch new images from the Weerplaza API."""
        for image_type, file_path in IMAGE_URLS.items():
            if not self.__is_camera_registered(image_type):
                continue
            if not file_path:
                continue
            if not self._images.get(image_type, None):
                await self.__async_build_images_list(image_type)
            data = await self.__async_get_image_data(image_type)
            if not data:
                return None
            image_data = data.get("data", [])
            if not image_data:
                return None

            for data in image_data:
                time_val = datetime.fromisoformat(data.get("dateTime"))
                if self.__image_needed(image_type, time_val):
                    filename, overlay_filename = (
                        data.get("layerNameHD").split(";") + [None]
                    )[:2]
                    _LOGGER.debug("Downloading image (%s) for %s", image_type, filename)
                    image_raw = await self.__async_download_lastest_image(filename)
                    overlay_raw = (
                        await self.__async_download_lastest_image(overlay_filename)
                        if overlay_filename
                        else None
                    )
                    if image_raw:
                        original = Image.open(BytesIO(image_raw))
                        overlay = (
                            Image.open(BytesIO(overlay_raw)) if overlay_raw else None
                        )
                        if original.width > 500:
                            await self.__async_create_image(
                                original,
                                overlay,
                                image_type,
                                time_val,
                            )
                            self.__add_filename_to_images(image_type, time_val)

            await self.__async_create_animated_gif(image_type)

        self.set_setting(
            LAST_UPDATED,
            datetime.now().replace(tzinfo=ZoneInfo(self._hass.config.time_zone)),
        )

    async def __async_get_image_data(
        self, image_type: ImageType
    ) -> dict[str, Any] | None:
        """Fetch the latest image data."""
        try:
            async with async_timeout.timeout(TIMEOUT):
                async with self._session.get(
                    IMAGE_URLS[image_type], headers=self._headers
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        _LOGGER.error("Failed to fetch image: %s", response.status)
                        return None
        except aiohttp.ClientError as e:
            _LOGGER.error("Error fetching image data: %s", e)
            return None

    async def __async_download_lastest_image(self, url) -> bytes | None:
        """Download the latest image."""
        try:
            async with async_timeout.timeout(TIMEOUT):
                async with self._session.get(url, headers=self._headers) as response:
                    if response.status == 200:
                        return await response.read()
                    else:
                        _LOGGER.error(
                            "Failed to fetch image (%s): %s", url, response.status
                        )
                        return None
        except aiohttp.ClientError as e:
            _LOGGER.error("Error fetching image: %s", e)
            return None

    def __get_background_image(self) -> Image.Image:
        with Image.open(
            f"custom_components/{DOMAIN}/images/Radar-1050-v2.jpg"
        ) as image:
            return image.convert("RGBA")

    def __get_borders_image(self) -> Image.Image:
        with Image.open(
            f"custom_components/{DOMAIN}/images/Radar-1050-borders-v2.png"
        ) as image:
            return image.convert("RGBA")

    def __get_marker_image(self) -> Image.Image:
        with Image.open(f"custom_components/{DOMAIN}/images/pointer-50.png") as image:
            return image.convert("RGBA")  # .resize((50, 50), Image.Resampling.LANCZOS)

    async def __async_create_image(
        self,
        original: ImageFile.ImageFile,
        overlay: ImageFile.ImageFile | None,
        image_type: ImageType,
        time_val: datetime,
    ) -> None:
        """Create an image with the original and overlay."""
        await self._hass.async_add_executor_job(
            self.__create_image, original, overlay, image_type, time_val
        )

    def __create_image(
        self,
        original: ImageFile.ImageFile,
        overlay: ImageFile.ImageFile | None,
        image_type: ImageType,
        time_val: datetime,
    ) -> None:
        # final image size is 1050x1148
        final = self.__get_background_image()

        # Resize original image to fit the final image
        original_image = original.resize(
            (final.width, final.height), Image.Resampling.LANCZOS
        ).convert("RGBA")
        final.paste(original_image, (0, 0), original_image)

        # If overlay is provided, paste it on top of the original image
        if overlay:
            overlay_image = overlay.resize(
                (final.width, final.height), Image.Resampling.LANCZOS
            ).convert("RGBA")
            final.paste(overlay_image, (0, 0), overlay_image)

        # Add borders
        borders = self.__get_borders_image()
        final.paste(borders, (0, 0), borders)

        # Rotate the final image -6 degrees with transparent background
        final = final.rotate(-6, expand=False, fillcolor=(0, 0, 0, 0))

        # Crop the final image to 776x700
        final = final.crop((157, 264, 157 + 776, 264 + 700))

        draw = ImageDraw.Draw(final)
        # Colors
        text_color = (254, 255, 255)
        outline_color = (0, 0, 0)

        # Font
        font = ImageFont.load_default(30)

        textx = 10
        texty = final.height - font.size - 10  # type: ignore

        # Draw time
        time_str = time_val.astimezone(timezone(self._timezone)).strftime("%H:%M")
        for adj in range(-2, 3):
            draw.text((textx + adj, texty), time_str, font=font, fill=outline_color)
            draw.text((textx, texty + adj), time_str, font=font, fill=outline_color)
        draw.text((textx, texty), time_str, font=font, fill=text_color)

        filename = self.__get_image_filename(image_type, time_val)
        final.save(filename, "PNG")
        mod_time = int(time_val.timestamp())
        os.utime(filename, (mod_time, mod_time))

    def __get_image_filename(self, image_type: ImageType, time_val: datetime) -> str:
        """Get the filename of the latest image."""
        return f"{self.__get_storage_path(image_type)}/{time_val.strftime('%Y%m%d-%H%M')}.png"

    def __image_needed(self, image_type: ImageType, time_val: datetime) -> bool:
        """Check if the image is needed based on the time."""
        if time_val.timestamp() > (datetime.now() - timedelta(hours=12)).timestamp():
            return not os.path.exists(self.__get_image_filename(image_type, time_val))
        return False

    def __add_filename_to_images(
        self, image_type: ImageType, time_val: datetime
    ) -> None:
        self._images[image_type].append(self.__get_image_filename(image_type, time_val))
        self._images[image_type].sort()
        self.__keep_last_images(image_type)

    def __keep_last_images(self, image_type: ImageType):
        """Keep only the last IMAGES_TO_KEEP images."""
        while len(self._images[image_type]) > IMAGES_TO_KEEP:
            filename = self._images[image_type].pop(0)
            if os.path.exists(filename):
                os.remove(filename)
                _LOGGER.debug("Removed old image: %s", filename)

    async def __async_create_animated_gif(self, image_type: ImageType) -> None:
        """Create an animated GIF from the images."""
        await self._hass.async_add_executor_job(self.__create_animated_gif, image_type)

    def __create_animated_gif(self, image_type: ImageType):
        if not self.__is_camera_registered(image_type):
            return
        images = []
        duration = []
        for index, image_data in enumerate(self._images[image_type]):
            if not os.path.exists(image_data):
                continue
            # Add marker location if set
            if (
                self.setting(SHOW_MARKER)
                and self.setting(MARKER_LONGITUDE)
                and self.setting(MARKER_LATITUDE)
            ):
                final = Image.open(image_data).convert("RGBA")
                marker = self.__get_marker_image()
                marker_x, marker_y = calculate_mercator_position(
                    self.setting(MARKER_LATITUDE),
                    self.setting(MARKER_LONGITUDE),
                    llon=1.556,
                    rlon=8.8,
                    tlat=54.239,
                    width=final.width,
                )
                final.paste(
                    marker,
                    (
                        marker_x - int(marker.width / 2),
                        marker_y - int(marker.height / 2),
                    ),
                    marker,
                )
                image_stream = BytesIO()
                final.save(image_stream, format="PNG")
                images.append(imageio.imread(image_stream))
            else:
                images.append(imageio.imread(image_data))

            duration.append(
                2000 if index == len(self._images[image_type]) - 1 else 200
            )  # 200 ms for all but the last frame
        if len(images) > 0:
            imageio.mimwrite(
                f"{self.__get_storage_path(image_type)}/animated.gif",
                images,
                loop=0,
                duration=duration,
            )

    async def __async_build_images_list(self, image_type: ImageType) -> None:
        """Build the list of images from the storage path."""
        await self._hass.async_add_executor_job(self.__build_images_list, image_type)

    def __build_images_list(self, image_type: ImageType) -> None:
        """Build the list of images from the storage path."""
        self._images[image_type] = []
        files = glob.glob(os.path.join(self.__get_storage_path(image_type), "*.png"))
        files.sort()
        for file in files:
            self._images[image_type].append(file)
        self.__keep_last_images(image_type)

    async def async_get_animated_image(self, image_type: ImageType) -> bytes | None:
        """Get the animated image."""
        return await self._hass.async_add_executor_job(
            self.__get_animated_image, image_type
        )

    def __get_animated_image(self, image_type: ImageType) -> bytes | None:
        """Get the animated image."""
        animated_path = f"{self.__get_storage_path(image_type)}/animated.gif"
        if os.path.exists(animated_path):
            with open(animated_path, "rb") as image_file:
                return image_file.read()
        return None

    def __get_storage_path(self, image_type: ImageType) -> str:
        """Get the storage path for the given image type."""
        return self._storage_paths.get(image_type, "")

    async def async_force_refresh(self) -> None:
        """Force refresh of the images."""
        _LOGGER.debug("Refreshing Weerplaza images")
        for image_type in IMAGE_URLS:
            if not self.__is_camera_registered(image_type):
                continue
            await self.__async_create_animated_gif(image_type)

    def __is_camera_registered(self, image_type: ImageType) -> bool:
        """Check if the image type is enabled."""
        return self._cameras.get(image_type, False)

    async def async_register_camera(self, image_type: ImageType) -> None:
        """Register a camera for the given image type."""
        await self._hass.async_add_executor_job(self.__register_camera, image_type)

    def __register_camera(self, image_type: ImageType) -> None:
        self._cameras[image_type] = True
        storage_path = self.__get_storage_path(image_type)
        if not os.path.exists(storage_path):
            os.makedirs(storage_path, exist_ok=True)

    async def async_unregister_camera(self, image_type: ImageType) -> None:
        """Unregister a camera for the given image type."""
        await self._hass.async_add_executor_job(self.__unregister_camera, image_type)

    def __unregister_camera(self, image_type: ImageType) -> None:
        self._cameras[image_type] = False
        storage_path = self.__get_storage_path(image_type)
        if os.path.exists(storage_path):
            rmtree(storage_path)
