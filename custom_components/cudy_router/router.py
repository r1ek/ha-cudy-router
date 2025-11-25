"""Provides the backend for a Cudy router"""
import hashlib
import time
from datetime import timedelta
from typing import Any
import requests
import logging
import urllib.parse
from http.cookies import SimpleCookie

from bs4 import BeautifulSoup

from .const import MODULE_DEVICES, MODULE_MODEM, OPTIONS_DEVICELIST
from .parser import parse_devices, parse_modem_info

from homeassistant.core import HomeAssistant
import homeassistant.util.dt as dt_util

_LOGGER = logging.getLogger(__name__)

MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=15)
SCAN_INTERVAL = timedelta(seconds=30)
RETRY_INTERVAL = timedelta(seconds=300)


class CudyRouter:
    """Represents a router and provides functions for communication."""

    def __init__(
        self, hass: HomeAssistant, host: str, username: str, password: str
    ) -> None:
        """Initialize."""
        self.host = host
        self.auth_cookie = None
        self.hass = hass
        self.username = username
        self.password = password

    def get_cookie_header(self, force_auth: bool) -> str:
        """Returns a cookie header that should be used for authentication."""

        if not force_auth and self.auth_cookie:
            return f"sysauth={self.auth_cookie}"
        if self.authenticate():
            return f"sysauth={self.auth_cookie}"
        else:
            return ""

    def authenticate(self) -> bool:
        """Test if we can authenticate with the host."""

        login_url = f"http://{self.host}/cgi-bin/luci"
        try:
            resp = requests.get(login_url, timeout=10)
            html = resp.text
            soup = BeautifulSoup(html, "html.parser")

            def extract(name):
                tag = soup.find("input", {"name": name})
                return tag["value"] if tag and tag.has_attr("value") else ""

            _csrf = extract("_csrf")
            token = extract("token")
            salt = extract("salt")
        except Exception as e:
            _LOGGER.error("Error retrieving login page: %s", e)
            return False


        zonename = str(dt_util.DEFAULT_TIME_ZONE)
        timeclock = str(int(time.time()))
        luci_language = "en"
        luci_username = self.username
        plain_password = self.password

        if salt:
            hashed = hashlib.sha256((plain_password + salt).encode()).hexdigest()
            if token:
                hashed = hashlib.sha256((hashed + token).encode()).hexdigest()
            luci_password = hashed
        else:
            luci_password = plain_password

        body = {
            "_csrf": _csrf,
            "token": token,
            "salt": salt,
            "zonename": zonename,
            "timeclock": timeclock,
            "luci_language": luci_language,
            "luci_username": luci_username,
            "luci_password": luci_password,
        }
        body = {k: v for k, v in body.items() if v}


        data_url = f"http://{self.host}/cgi-bin/luci"
        headers = {"Content-Type": "application/x-www-form-urlencoded", "Cookie": ""}

        try:
            response = requests.post(
                data_url, timeout=30, headers=headers, data=body, allow_redirects=False
            )
            if response.ok:
                cookie = SimpleCookie()
                cookie.load(response.headers.get("set-cookie"))
                self.auth_cookie = cookie.get("sysauth").value
                return True
        except requests.exceptions.ConnectionError:
            _LOGGER.debug("Connection error?")
        return False

    def get(self, url: str) -> str:
        """Retrieves data from the given URL using an authenticated session."""

        retries = 2
        while retries > 0:
            retries -= 1

            data_url = f"http://{self.host}/cgi-bin/luci/{url}"
            headers = {"Cookie": f"{self.get_cookie_header(False)}"}

            try:
                response = requests.get(
                    data_url, timeout=30, headers=headers, allow_redirects=False
                )
                if response.status_code == 403:
                    if self.authenticate():
                        continue
                    else:
                        _LOGGER.error("Error during authentication to %s", url)
                        break
                if response.ok:
                    return response.text
                else:
                    break
            except Exception:  # pylint: disable=broad-except
                pass

        _LOGGER.error("Error retrieving data from %s", url)
        return ""

    async def get_data(
        self, hass: HomeAssistant, options: dict[str, Any], previous_data: dict[str, Any] = None
    ) -> dict[str, Any]:
        """Retrieves data from the router"""

        data: dict[str, Any] = {}

        # data[MODULE_MODEM] = parse_modem_info(
        #     f"{await hass.async_add_executor_job(self.get, 'admin/network/gcom/status')}{await hass.async_add_executor_job(self.get, 'admin/network/gcom/status?detail=1')}"
        # )
        previous_devices = previous_data.get(MODULE_DEVICES) if previous_data else None
        data[MODULE_DEVICES] = parse_devices(
            await hass.async_add_executor_job(
                self.get, "admin/network/devices/devlist?detail=1"
            ),
            options and options.get(OPTIONS_DEVICELIST),
            previous_devices,
        )

        return data
