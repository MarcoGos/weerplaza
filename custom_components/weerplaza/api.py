from typing import Any

import os
import glob
import logging
from io import BytesIO

from datetime import datetime, timedelta
import aiohttp
from pytz import timezone

import async_timeout
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.storage import STORAGE_DIR
from PIL import Image, ImageFile, ImageDraw, ImageFont
import imageio.v2 as imageio

from .const import DOMAIN

TIMEOUT = 10
IMAGES_TO_KEEP = 18

IMAGE_URLS = {
    "radar": "https://api.meteoplaza.com/v2/splash/10728/obs?access_token=weerplaza&usehd=1",
    "satellite": "https://api.meteoplaza.com/v2/splash/10728/sat?access_token=weerplaza&usehd=1",
    "thunder": "https://api.meteoplaza.com/v2/splash/10728/thunder?access_token=weerplaza&usehd=1",
}

_LOGGER: logging.Logger = logging.getLogger(__package__)


class WeerPlazaApi:
    _headers: dict[str, str] = {"User-Agent": "Home Assistant (Weer Plaza)"}
    _images: dict[str, Any] = {}
    _storage_paths: dict[str, str] = {}
    _timezone: Any = None

    def __init__(self, hass: HomeAssistant) -> None:
        self._hass = hass
        self._timezone = self._hass.config.time_zone
        self._latitude = hass.config.latitude
        self._longitude = hass.config.longitude
        self._session = async_get_clientsession(self._hass)
        self.__create_storage_paths()

    async def async_get_new_images(self) -> None:
        for image_type, file_path in IMAGE_URLS.items():
            if not file_path:
                continue
            if not self._images.get(image_type, None):
                await self._hass.async_add_executor_job(
                    self.__build_images_list, image_type
                )
            data = await self.__async_get_image_data(image_type)
            if not data:
                return None
            image_data = data.get("data", [])
            if not image_data:
                return None

            for data in image_data:
                time_val = datetime.fromisoformat(data.get("dateTime"))
                if self.__image_needed(image_type, time_val):
                    filename = data.get("layerNameHD")
                    _LOGGER.debug("Downloading image (%s) for %s", image_type, filename)
                    image_raw = await self.__async_download_lastest_image(filename)
                    if image_raw:
                        original = Image.open(BytesIO(image_raw))
                        if original.width > 500:
                            await self._hass.async_add_executor_job(
                                self.__create_image,
                                original,
                                image_type,
                                time_val,
                            )
                            self.__add_filename_to_images(image_type, time_val)

            await self.async_create_animated_gif(image_type)

    async def __async_get_image_data(self, image_type: str) -> dict[str, Any] | None:
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
        with Image.open(
            f"custom_components/{DOMAIN}/images/pointer-50.png"
        ) as image:
            return image.convert("RGBA") #.resize((50, 50), Image.Resampling.LANCZOS)

    def __create_image(
        self, original: ImageFile.ImageFile, image_type: str, time_val: datetime
    ) -> bytes:
        # final image size is 1050x1148
        final = self.__get_background_image()
        # Resize original image to fit the final image
        orig = original.resize(
            (final.width, final.height), Image.Resampling.LANCZOS
        ).convert("RGBA")
        final.paste(orig, (0, 0), orig)
        # Add borders
        borders = self.__get_borders_image()
        final.paste(borders, (0, 0), borders)

        # Rotate the final image -6 degrees with transparent background
        final = final.rotate(-6, expand=False, fillcolor=(0, 0, 0, 0))

        # Crop the final image to 776x700
        final = final.crop((157, 264, 157 + 776, 264 + 700))

        draw = ImageDraw.Draw(final)
        # Colors
        textcolor = (254, 255, 255)
        bgtextcolor = (12, 66, 156)
        # Font
        font = ImageFont.load_default(20)

        textx = 3
        texty = final.height - 30

        # Draw background rectangle for text
        draw.rectangle(
            [0, final.height - 32, final.width, final.height], fill=bgtextcolor
        )

        # Draw time
        time_str = time_val.astimezone(timezone(self._timezone)).strftime("%H:%M")
        draw.text((textx, texty), time_str, font=font, fill=textcolor)

        # Draw copyright
        copyright_str = f"(c) {time_val.year} WeerPlaza.NL"
        draw.text((textx + 62, texty), copyright_str, font=font, fill=textcolor)

        filename = self.__get_image_filename(image_type, time_val)
        final.save(filename, "PNG")
        mod_time = int(time_val.timestamp())
        os.utime(filename, (mod_time, mod_time))

        img_byte_arr = BytesIO()
        final.save(img_byte_arr, "PNG")

        return img_byte_arr.getvalue()

    def __get_image_filename(self, image_type: str, time_val: datetime) -> str:
        """Get the filename of the latest image."""
        return f"{self.get_storage_path(image_type)}/{time_val.strftime('%Y%m%d-%H%M')}.png"

    def __image_needed(self, image_type: str, time_val: datetime) -> bool:
        """Check if the image is needed based on the time."""
        if time_val.timestamp() > (datetime.now() - timedelta(hours=12)).timestamp():
            return not os.path.exists(self.__get_image_filename(image_type, time_val))
        return False

    def __add_filename_to_images(self, image_type: str, time_val: datetime) -> None:
        self._images[image_type].append(self.__get_image_filename(image_type, time_val))
        self.__keep_last_images(image_type)

    def __keep_last_images(self, image_type: str):
        """Keep only the last IMAGES_TO_KEEP images."""
        while len(self._images[image_type]) > IMAGES_TO_KEEP:
            filename = self._images[image_type].pop(0)
            if os.path.exists(filename):
                os.remove(filename)

    async def async_create_animated_gif(self, image_type: str) -> None:
        """Create an animated GIF from the images."""
        await self._hass.async_add_executor_job(self.__create_animated_gif, image_type)

    def __create_animated_gif(self, image_type: str):
        images = []
        duration = []
        for index, image_data in enumerate(self._images[image_type]):
            # Add marker location if set
            if self._latitude and self._longitude:
                final = Image.open(image_data).convert("RGBA")
                marker = self.__get_marker_image()
                # marker_x = int((self._longitude + 180) * (final.width / 360))
                # marker_y = int((90 - self._latitude) * (final.height / 180))
                marker_x = int(final.width / 2)
                marker_y = int(final.height / 2)
                final.paste(marker, (marker_x - int(marker.width / 2), marker_y - int(marker.height / 2)), marker)
                image_stream = BytesIO()
                final.save(image_stream, format="PNG")
                images.append(imageio.imread(image_stream))
            else:
                images.append(imageio.imread(image_data))
                
            duration.append(
                2000 if index == len(self._images[image_type]) - 1 else 200
            )  # 200 ms for all but the last frame
        imageio.mimwrite(
            f"{self.get_storage_path(image_type)}/animated.gif",
            images,
            loop=0,
            duration=duration,
        )

    def __build_images_list(self, image_type):
        """Build the list of images from the storage path."""
        self._images[image_type] = []
        files = glob.glob(os.path.join(self.get_storage_path(image_type), "*.png"))
        files.sort()
        for file in files:
            self._images[image_type].append(file)
        self.__keep_last_images(image_type)

    async def async_get_animated_image(self, image_type: str) -> bytes | None:
        """Get the animated image."""
        return await self._hass.async_add_executor_job(
            self.get_animated_image, image_type
        )

    def get_animated_image(self, image_type) -> bytes | None:
        """Get the animated image."""
        animated_path = f"{self.get_storage_path(image_type)}/animated.gif"
        if os.path.exists(animated_path):
            with open(animated_path, "rb") as image_file:
                return image_file.read()
        return None

    def get_storage_path(self, image_type: str) -> str:
        """Get the storage path for the given image type."""
        return self._storage_paths.get(image_type, "")

    def __create_storage_paths(self):
        for image_type in IMAGE_URLS:
            self._storage_paths[image_type] = self._hass.config.path(
                STORAGE_DIR, DOMAIN, image_type
            )
            if not os.path.exists(self.get_storage_path(image_type)):
                os.makedirs(self.get_storage_path(image_type), exist_ok=True)

    async def async_set_marker_location(self, latitude: float, longitude: float) -> None:
        """Set the marker location."""
        self._latitude = latitude
        self._longitude = longitude
        _LOGGER.debug("Setting marker location to (%s, %s)", latitude, longitude)
