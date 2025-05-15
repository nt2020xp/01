import logging
import json
import urllib.parse
from typing import Optional
from .base import BaseChannel
from live.util.http import get_json
import cloudscraper
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import base64

logger = logging.getLogger(__name__)


class G4TV(BaseChannel):
    def __init__(self):
        self.key = b"ilyB29ZdruuQjC45JhBBR7o2Z8WJ26Vg"
        self.iv = b"JUMxvVMmszqUTeKn"
        self.scraper = cloudscraper.create_scraper()

    async def get_channel(self, channel_id):
        logger.info(f"Fetching channel data for channel ID: {channel_id}")
        response = self.scraper.get(f"https://api2.4gtv.tv/Channel/GetChannel/{channel_id}")
        channel_data = json.loads(response.text)["Data"]
        logger.debug(f"Received channel data: {channel_data}")
        return channel_data

    async def get_channel_url(self, data):
        logger.info("Fetching channel URL with encrypted data")
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        try:
            response = self.scraper.post("https://api2.4gtv.tv/Channel/GetChannelUrl3", data=data, headers=headers)
            response.raise_for_status()  # Raise an exception for HTTP errors (status codes 4xx or 5xx)
            channel_url_data = json.loads(response.text)["Data"]
            logger.debug(f"Received channel URL data: {channel_url_data}")
            return channel_url_data
        except Exception as e:
            logger.error(f"Error fetching channel URL: {e}")
            return None

    async def get_play_url(self, video_id: str) -> Optional[str]:
        logger.info(f"Processing request for video ID: {video_id}")

        channel_data = await self.get_channel(video_id)
        if not channel_data:
            logger.warning(f"Failed to fetch channel data for video ID: {video_id}")
            return None

        cno = channel_data["fnID"]
        cid = channel_data["fs4GTV_ID"]

        jarray = {
            "fnCHANNEL_ID": cno,
            "fsASSET_ID": cid,
            "fsDEVICE_TYPE": "mobile",
            "clsIDENTITY_VALIDATE_ARUS": {"fsVALUE": ""},
        }
        abc = json.dumps(jarray)

        enc = self.encrypt_data(abc)
        data = "value=" + urllib.parse.quote_plus(enc.decode())

        channel_url_data = await self.get_channel_url(data)
        if not channel_url_data:
            logger.warning(f"Failed to fetch channel URL data for video ID: {video_id}")
            return None

        decrypted_data = self.decrypt_data(channel_url_data)
        playlist = json.loads(decrypted_data)["flstURLs"][0]
        logger.info(f"Returning playlist URL for video ID {video_id}: {playlist}")
        return playlist

    def encrypt_data(self, data):
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        padded_data = pad(data.encode(), AES.block_size)
        return base64.b64encode(cipher.encrypt(padded_data))

    def decrypt_data(self, encrypted_data):
        decipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        decrypted_data = unpad(decipher.decrypt(base64.b64decode(encrypted_data)), AES.block_size)
        return decrypted_data.decode()


site = G4TV()
