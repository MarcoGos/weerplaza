from typing import Any

import os
import glob
import time
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
IMAGES_DATA_URL = (
    "https://api.meteoplaza.com/v2/splash/10728/obs?access_token=weerplaza&usehd=1"
)

ams_timezone = timezone("Europe/Amsterdam")

_LOGGER: logging.Logger = logging.getLogger(__package__)


class WeerPlazaApi:
    _headers: dict[str, str] = {"User-Agent": "Home Assistant (Weer Plaza)"}
    _images: list = []

    def __init__(self, hass: HomeAssistant) -> None:
        self._hass = hass
        self._session = async_get_clientsession(self._hass)
        self._storage_path = hass.config.path(STORAGE_DIR, DOMAIN)
        if not os.path.exists(self._storage_path):
            os.makedirs(self._storage_path, exist_ok=True)

    async def async_get_latest_image(self) -> None:
        await self._hass.async_add_executor_job(self.__delete_old_radar_files)
        if not self._images:
            await self._hass.async_add_executor_job(self.__build_images_list)
        data = await self.__async_get_image_data()
        if not data:
            return None
        image_data = data.get("data", [])
        if not image_data:
            return None
        
        for data in image_data:
            time_val = datetime.fromisoformat(data.get("dateTime"))
            if self.__image_needed(time_val):
                filename = data.get("layerNameHD")
                _LOGGER.debug("Downloading image for %s", filename)
                image_raw = await self.__async_download_lastest_image(filename)
                if image_raw:
                    original = Image.open(BytesIO(image_raw))
                    if original.width > 500:
                        # self._image = await self.__create_large_image(original, time_val)
                        await self._hass.async_add_executor_job(self.__create_large_image, original, time_val)
                        self.__add_filename_to_images(time_val)
                        await self._hass.async_add_executor_job(self.__create_animated_large_radar_gif)

    async def __async_get_image_data(self) -> dict[str, Any] | None:
        """Fetch the latest image data."""
        try:
            async with async_timeout.timeout(TIMEOUT):
                async with self._session.get(
                    IMAGES_DATA_URL, headers=self._headers
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
                        _LOGGER.error("Failed to fetch image: %s", response.status)
                        return None
        except aiohttp.ClientError as e:
            _LOGGER.error("Error fetching image: %s", e)
            return None

    def get_background_image(self) -> Image.Image:
        with Image.open(
            f"custom_components/{DOMAIN}/images/Nederland_0_55_9_49_5_large.gif"
        ) as image:
            return image.convert("RGBA")

    def __create_large_image(self, original: ImageFile.ImageFile, time_val) -> bytes:
        # Resize to width 560, keep aspect ratio
        width = 560
        aspect = original.height / original.width
        height = int(width * aspect)
        im = original.resize((width, height), Image.Resampling.LANCZOS).convert("RGBA")

        # Rotate -6 degrees with transparent background
        rotated = im.rotate(-6, expand=True, fillcolor=(0, 0, 0, 0))

        final = self.get_background_image()
        x_offset = 30
        y_offset = 95
        crop_box = (x_offset, y_offset, x_offset + 512, y_offset + 512)
        cropped = rotated.crop(crop_box)
        cropped = cropped.resize((512, 512), Image.Resampling.LANCZOS)
        final.paste(cropped, (0, 0), cropped)

        draw = ImageDraw.Draw(final)
        # Colors
        textcolor = (254, 255, 255)
        bgtextcolor = (12, 66, 156)
        # Font
        font = ImageFont.load_default()

        textx = 3
        texty = final.height - 16

        # Draw background rectangle for text
        draw.rectangle(
            [0, final.height - 16, final.width, final.height], fill=bgtextcolor
        )

        # Draw time
        time_str = time_val.astimezone(ams_timezone).strftime("%H:%M")
        draw.text((textx, texty), time_str, font=font, fill=textcolor)

        # Draw copyright
        copyright_str = f"(c) {time_val.year} WeerPlaza.NL"
        draw.text((textx + 45, texty), copyright_str, font=font, fill=textcolor)

        filename = self.__get_image_filename(time_val)
        final.save(filename, "PNG")
        mod_time = int(time_val.timestamp())
        os.utime(filename, (mod_time, mod_time))

        img_byte_arr = BytesIO()
        final.save(img_byte_arr, "PNG")

        return img_byte_arr.getvalue()

    def __delete_old_radar_files(self):
        """Delete radar files older than 12 hours."""
        bandwidth = 12 * 60 * 60  # 12 hours in seconds
        # for radar_path in ["images/radar/", "images/radar_large/", "images/radar_small/"]:
        radar_path = self._storage_path
        files = glob.glob(os.path.join(radar_path, "*.png"))
        for file in files:
            if time.time() - os.path.getmtime(file) > bandwidth:
                os.remove(file)

    def __get_image_filename(self, time_val: datetime) -> str:
        """Get the filename of the latest image."""
        return f"{self._storage_path}/large_{time_val.strftime('%Y%m%d-%H%M')}.png"
    
    def __image_needed(self, time_val: datetime) -> bool:
        """Check if the image is needed based on the time."""
        if time_val.timestamp() > (datetime.now() - timedelta(hours=12)).timestamp():
            return not os.path.exists(self.__get_image_filename(time_val))
        return False
    
    def __add_filename_to_images(self, time_val: datetime) -> None:
        self._images.append(self.__get_image_filename(time_val))
        self.__keep_last_images()

    def __keep_last_images(self):
        """Keep only the last 18 images."""
        self._images = self._images[-18:]

    def __create_animated_large_radar_gif(self):
        images = []
        duration = []
        for index, image_data in enumerate(self._images):
            images.append(imageio.imread(image_data))
            duration.append(2000 if index == len(self._images) -1 else 200)  # 200 ms for all but the last frame
        imageio.mimwrite(f"{self._storage_path}/animated_radar.gif", images, loop=0, duration=duration)

    def __build_images_list(self):
        """Build the list of images from the storage path."""
        self._images = []
        files = glob.glob(os.path.join(self._storage_path, "large_*.png"))
        files.sort()
        for file in files:
            self._images.append(file)
        self.__keep_last_images()

    def get_latest_image(self) -> bytes | None:
        """Get the latest image."""
        latest_image_path = self._images[-1]
        if os.path.exists(latest_image_path):
            with open(latest_image_path, "rb") as image_file:
                return image_file.read()
        return None
        
    def get_animated_radar(self) -> bytes | None:
        """Get the animated radar image."""
        animated_radar_path = f"{self._storage_path}/animated_radar.gif"
        if os.path.exists(animated_radar_path):
            with open(animated_radar_path, "rb") as image_file:
                return image_file.read()
        return None