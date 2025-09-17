"""Stromer module for Home Assistant Core."""

__version__ = "0.2.0"

import asyncio
import json
import logging
import re
from typing import Any
from urllib.parse import urlencode

import aiodns
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

        LOGGER.debug("Initializing Stromer with API version %s", self._api_version)

        self._timeout: int = timeout
        self._username: str = username
        self._password: str = password
        self._client_id: str = client_id
        self._client_secret: str = client_secret

        self._code: str | None = None
        self._token: str | None = None

        self.full_data: dict = {}
        self.bike_id: str | None = None
        self.bike_name: str | None = None
        self.bike_model: str | None = None

    async def stromer_connect(self) -> bool:
        """Connect to stromer API."""
        LOGGER.debug("Creating aiohttp session")
        aio_timeout = aiohttp.ClientTimeout(total=self._timeout)
        self._websession = aiohttp.ClientSession(timeout=aio_timeout)

        # Retrieve authorization token
        await self.stromer_get_code()

        # Retrieve access token
        await self.stromer_get_access_token()

        LOGGER.debug("Stromer connected!")

        return True

    async def stromer_disconnect(self) -> None:
        """Close API web session."""
        LOGGER.debug("Closing aiohttp session")
        await self._websession.close()

    async def stromer_detect(self) -> dict:
        """Get full data (to determine bike(s))."""
        try:
            self.full_data = await self.stromer_call_api(endpoint="bike/", full=True)
        except Exception as e:
            log = f"Stromer unable to fetch full data: {e}"
            LOGGER.error(log)
            raise ApiError from e

        log = f"Stromer full_data : {self.full_data}"
        LOGGER.debug(log)
        return self.full_data

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

    async def stromer_api_debouncer(self, url: str, timeout: int = 10, retries: int = 10, delay: int = 10) -> aiohttp.ClientResponse:
        """Debounce API-request to leverage DNS issues."""
        for attempt in range(retries):
            try:
                log = f"Attempt {attempt + 1}/{retries} to interface with Stromer on {url}"
                LOGGER.debug(log)
                res = await self._websession.get(url, timeout=timeout)
                res.raise_for_status()
                return res
            except (aiodns.error.DNSError, aiohttp.ClientError, TimeoutError) as e:
                log = f"Error getting Stromer API (attempt {attempt + 1}/{retries}): {e}"
                LOGGER.warning(log)
                if attempt < retries - 1:
                    log = f"Retrying in {delay} seconds..."
                    LOGGER.warning(log)
                    await asyncio.sleep(delay)
                else:
                    log = f"Failed to get to Stromer API after {retries} attempts."
                    LOGGER.error(log)
                    raise  # Re-raise the last exception if all retries fail

    async def stromer_get_code(self) -> None:
        """Retrieve authorization code from API."""
        url = f"{self.base_url}/mobile/v4/login/"
        if self._api_version == "v3":
            url = f"{self.base_url}/users/login/"
        res = await self.stromer_api_debouncer(url)
        try:
            cookie = res.headers.get("Set-Cookie")
            pattern = "=(.*?);"
            csrftoken = re.search(pattern, cookie).group(1)  # type: ignore[union-attr, arg-type]
        except Exception as e:
            log = f"Stromer error: api call failed: {e} with content {res}"
            LOGGER.error(log)
            raise ApiError from e

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
        LOGGER.error("DEBUG location result %s", await res.text())
        LOGGER.error("DEBUG determined next location: %s", next_loc)

        next_url = f"{self.base_url}{next_loc}"
        LOGGER.error("DEBUG next url: %s", next_url)

        res = await self._websession.get(next_url, allow_redirects=False)
        self._code = res.headers.get("Location")
        LOGGER.error("DEBUG code result %s", await res.text())
        LOGGER.error("DEBUG code determined: %s", self._code)
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
        log = f"API call lock status: {res.status}"
        LOGGER.debug(log)
        log = f"API call lock returns: {ret}"
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
        log = f"API call light status: {res.status}"
        LOGGER.debug(log)
        log = f"API call light returns: {ret}"
        LOGGER.debug(log)

    async def stromer_reset_trip_data(self) -> None:
        """Reset the trip data through the API."""
        endpoint = f"bike/id/{self.bike_id}/trip_data/"
        url = f"{self.base_url}/rapi/mobile/v4.1/{endpoint}"
        if self._api_version == "v3":
            url = f"{self.base_url}/rapi/mobile/v2/{endpoint}"

        headers = {"Authorization": f"Bearer {self._token}"}
        res = await self._websession.delete(url, headers=headers)
        if res.status != 204:
            raise ApiError

    async def stromer_call_api(self, endpoint: str, full=False) -> Any:
        """Retrieve data from the API."""
        url = f"{self.base_url}/rapi/mobile/v4.1/{endpoint}"
        if self._api_version == "v3":
            url = f"{self.base_url}/rapi/mobile/v2/{endpoint}"

        headers = {"Authorization": f"Bearer {self._token}"}
        res = await self._websession.get(url, headers=headers, data={})
        ret = json.loads(await res.text())
        log = f"API call status: {res.status}"
        LOGGER.debug(log)
        log = f"API call returns: {ret}"
        LOGGER.debug(log)
        if full:
          return ret["data"]
        return ret["data"][0]


class ApiError(Exception):
    """Error to indicate something wrong with the API."""
