from typing import Any

# import os
import logging
from io import BytesIO

# import json
from datetime import datetime, timedelta
import aiohttp
from pytz import timezone

import requests
import async_timeout
from PIL import Image, ImageFile, ImageDraw, ImageFont
from .const import DOMAIN

TIMEOUT = 10
IMAGES_DATA_URL = (
    "https://api.meteoplaza.com/v2/splash/10728/obs?access_token=weerplaza&usehd=1"
)

ams_timezone = timezone("Europe/Amsterdam")

_LOGGER: logging.Logger = logging.getLogger(__package__)


class WeerPlazaApi:
    _headers: dict[str, str] = {"User-Agent": "Home Assistant (Weer Plaza)"}
    _image: bytes | None

    def __init__(self, session: aiohttp.ClientSession) -> None:
        self._session = session

    async def async_get_latest_image(self) -> bytes | None:
        data = await self.__async_get_image_data()
        if data:
            image_data = data.get("data", [])
            if image_data:
                last_image_data = image_data[-1]
                time_val = datetime.fromisoformat(last_image_data.get("dateTime"))
                if (
                    time_val.timestamp()
                    > (datetime.now() - timedelta(days=1)).timestamp()
                ):
                    image_raw = await self.__async_download_lastest_image(
                        last_image_data.get("layerNameHD")
                    )
                    if image_raw:
                        original = Image.open(BytesIO(image_raw))
                        _LOGGER.warning(
                            "Image found: %d x %d", original.width, original.height
                        )
                        if original.width > 500:
                            self._image = self.__create_large_image(
                                original,
                                time_val,
                            )
        return self._image

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
            _LOGGER.warning("background image found")
            return image.convert("RGBA")

    def __create_large_image(self, original: ImageFile.ImageFile, time_val) -> bytes:
        # Resize to width 560, keep aspect ratio
        width = 560
        aspect = original.height / original.width
        height = int(width * aspect)
        im = original.resize((width, height), Image.Resampling.LANCZOS).convert("RGBA")

        # Rotate -6 degrees with transparent background
        rotated = im.rotate(-6, expand=True, fillcolor=(0, 0, 0, 0))

        # final = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
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

        img_byte_arr = BytesIO()
        final.save(img_byte_arr, "PNG")

        return img_byte_arr.getvalue()
