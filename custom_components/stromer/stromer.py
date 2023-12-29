"""Stromer module for Home Assistant Core."""

__version__ = "0.1.0"

import json
import logging
import re
from typing import Any
from urllib.parse import urlencode

import aiohttp

LOGGER = logging.getLogger(__name__)


class Stromer:
    """Set up Stromer."""

    def __init__(self, username: str, password: str, client_id: str, client_secret: str, timeout: int = 60) -> None:
        """Initialize stromer module."""
        self.bike: dict = {}
        self.status: dict = {}
        self.position: dict = {}

        self._api_version: str = "v4"
        if client_secret:
            self._api_version = "v3"
        self.base_url: str = "https://api3.stromer-portal.ch"

        self._timeout: int = timeout
        self._username: str = username
        self._password: str = password
        self._client_id: str = client_id
        self._client_secret: str = client_secret

        self._code: str | None = None
        self._token: str | None = None

        self.bike_id: str | None = None
        self.bike_name: str | None = None
        self.bike_model: str | None = None

    async def stromer_connect(self) -> dict:
        """Connect to stromer API."""
        aio_timeout = aiohttp.ClientTimeout(total=self._timeout)
        self._websession = aiohttp.ClientSession(timeout=aio_timeout)

        # Retrieve authorization token
        await self.stromer_get_code()

        # Retrieve access token
        await self.stromer_get_access_token()

        try:
            await self.stromer_update()
        except Exception as e:
            log = f"Stromer unable to update: {e}"
            LOGGER.error(log)

        LOGGER.debug("Stromer connected!")

        return self.status

    async def stromer_update(self) -> None:
        """Update stromer data through API."""
        attempts = 0
        while attempts < 10:
            if attempts == 5:
                LOGGER.info("Reconnecting to Stromer API")
                await self.stromer_connect()
            attempts += 1
            try:
                log = f"Stromer attempt: {attempts}/10"
                LOGGER.debug(log)
                self.bike = await self.stromer_call_api(endpoint="bike/")
                log = f"Stromer bike: {self.bike}"
                LOGGER.debug(log)

                self.bike_id = self.bike["bikeid"]
                self.bike_name = self.bike["nickname"]
                self.bike_model = self.bike["biketype"]

                endpoint = f"bike/{self.bike_id}/state/"
                self.status = await self.stromer_call_api(endpoint=endpoint)
                log = f"Stromer status: {self.status}"
                LOGGER.debug(log)

                endpoint = f"bike/{self.bike_id}/position/"
                self.position = await self.stromer_call_api(endpoint=endpoint)
                log = f"Stromer position: {self.position}"
                LOGGER.debug(log)
                return

            except Exception as e:
                log = f"Stromer error: api call failed: {e}"
                LOGGER.error(log)
                log = f"Stromer retry: {attempts}/10"
                LOGGER.debug(log)

        LOGGER.error("Stromer error: api call failed 10 times, cowardly failing")
        raise ApiError

    async def stromer_get_code(self) -> None:
        """Retrieve authorization code from API."""
        url = f"{self.base_url}/mobile/v4/login/"
        if self._api_version == "v3":
            url = f"{self.base_url}/users/login/"
        res = await self._websession.get(url)
        try:
            cookie = res.headers.get("Set-Cookie")
            pattern = "=(.*?);"
            csrftoken = re.search(pattern, cookie).group(1)  # type: ignore[union-attr, arg-type]
        except Exception as e:
            log = f"Stromer error: api call failed: {e} with content {res}"
            LOGGER.error(log)
            raise ApiError

        qs = urlencode(
            {
                "client_id": self._client_id,
                "response_type": "code",
                "redirect_url": "stromerauth://auth",
                "scope": "bikeposition bikestatus bikeconfiguration bikelock biketheft bikedata bikepin bikeblink userprofile",
            }
        )

        data = {
            "password": self._password,
            "username": self._username,
            "csrfmiddlewaretoken": csrftoken,
            "next": "/mobile/v4/o/authorize/?" + qs,
        }

        if self._api_version == "v3":
            data["next"] = "/o/authorize/?" + qs

        res = await self._websession.post(
            url, data=data, headers={"Referer": url}, allow_redirects=False
        )
        next_loc = res.headers.get("Location")
        next_url = f"{self.base_url}{next_loc}"
        res = await self._websession.get(next_url, allow_redirects=False)
        self._code = res.headers.get("Location")
        self._code = self._code.split("=")[1]  # type: ignore[union-attr]

    async def stromer_get_access_token(self) -> None:
        """Retrieve access token from API."""
        url = f"{self.base_url}/mobile/v4/o/token/"
        data = {
            "grant_type": "authorization_code",
            "client_id": self._client_id,
            "code": self._code,
            "redirect_uri": "stromer://auth",
        }

        if self._api_version == "v3":
            url = f"{self.base_url}/o/token/"
            data["client_secret"] = self._client_secret
            data["redirect_uri"] = "stromerauth://auth"

        res = await self._websession.post(url, data=data)
        token = json.loads(await res.text())
        self._token = token["access_token"]

    async def stromer_call_lock(self, state: bool) -> None:
        """Lock or unlock the bike through the API."""
        endpoint = f"bike/{self.bike_id}/settings/"
        url = f"{self.base_url}/rapi/mobile/v4.1/{endpoint}"
        if self._api_version == "v3":
            url = f"{self.base_url}/rapi/mobile/v2/{endpoint}"

        data = {"lock": state}
        headers = {"Authorization": f"Bearer {self._token}"}
        res = await self._websession.post(url, headers=headers, json=data)
        ret = json.loads(await res.text())
        log = "API call lock status: %s" % res.status
        LOGGER.debug(log)
        log = "API call lock returns: %s" % ret
        LOGGER.debug(log)

    async def stromer_call_light(self, state: str) -> None:
        """Switch the bike light through the API."""
        endpoint = f"bike/{self.bike_id}/light/"
        url = f"{self.base_url}/rapi/mobile/v4.1/{endpoint}"
        if self._api_version == "v3":
            url = f"{self.base_url}/rapi/mobile/v2/{endpoint}"

        data = {"mode": state}
        headers = {"Authorization": f"Bearer {self._token}"}
        res = await self._websession.post(url, headers=headers, json=data)
        ret = json.loads(await res.text())
        log = "API call light status: %s" % res.status
        LOGGER.debug(log)
        log = "API call light returns: %s" % ret
        LOGGER.debug(log)

    async def stromer_call_api(self, endpoint: str) -> Any:
        """Retrieve data from the API."""
        url = f"{self.base_url}/rapi/mobile/v4.1/{endpoint}"
        if self._api_version == "v3":
            url = f"{self.base_url}/rapi/mobile/v2/{endpoint}"

        headers = {"Authorization": f"Bearer {self._token}"}
        res = await self._websession.get(url, headers=headers, data={})
        ret = json.loads(await res.text())
        log = "API call status: %s" % res.status
        LOGGER.debug(log)
        log = "API call returns: %s" % ret
        LOGGER.debug(log)
        return ret["data"][0]


class ApiError(Exception):
    """Error to indicate something wrong with the API."""
