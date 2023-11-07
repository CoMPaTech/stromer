"""Stromer module for Home Assistant Core."""

__version__ = "0.0.7"

import json
import logging
import re
from urllib.parse import urlencode

import aiohttp

LOGGER = logging.getLogger(__name__)


class Stromer:
    """Set up Stromer."""

    def __init__(self, username, password, client_id, client_secret, timeout=60):
        self.bike = {}
        self.status = {}
        self.position = {}

        self._api_version = "v4"
        if client_secret:
            self._api_version = "v3"
        self.base_url = "https://api3.stromer-portal.ch"

        self._timeout = timeout
        self._username = username
        self._password = password
        self._client_id = client_id
        self._client_secret = client_secret

        self._code = None
        self._token = None

        self.bike_id = None
        self.bike_name = None
        self.bike_model = None

    async def stromer_connect(self):
        aio_timeout = aiohttp.ClientTimeout(total=self._timeout)
        self._websession = aiohttp.ClientSession(timeout=aio_timeout)

        # Retrieve authorization token
        await self.stromer_get_code()

        # Retrieve access token
        await self.stromer_get_access_token()

        try:
            await self.stromer_update()
        except Exception as e:
            LOGGER.error(f"Stromer unable to update: {e}")

        LOGGER.debug("Stromer connected!")

        return self.status

    async def stromer_update(self):
        attempts = 0
        while attempts < 10:
            if attempts == 5:
                LOGGER.info("Reconnecting to Stromer API")
                await self.stromer_connect()
            attempts += 1
            try:
                LOGGER.debug(f"Stromer attempt: {attempts}/10")
                self.bike = await self.stromer_call_api(endpoint="bike/")
                LOGGER.debug(f"Stromer bike: {self.bike}")

                self.bike_id = self.bike["bikeid"]
                self.bike_name = self.bike["nickname"]
                self.bike_model = self.bike["biketype"]

                endpoint = f"bike/{self.bike_id}/state/"
                data = {"cached": "false"}
                self.status = await self.stromer_call_api(endpoint=endpoint)
                LOGGER.debug(f"Stromer status: {self.status}")

                endpoint = f"bike/{self.bike_id}/position/"
                self.position = await self.stromer_call_api(endpoint=endpoint)
                LOGGER.debug(f"Stromer position: {self.position}")
                return

            except Exception as e:
                LOGGER.error(f"Stromer error: api call failed: {e}")
                LOGGER.debug(f"Stromer retry: {attempts}/10")

        LOGGER.error("Stromer error: api call failed 10 times, cowardly failing")
        raise ApiError

    async def stromer_get_code(self):
        url = f"{self.base_url}/mobile/v4/login/"
        if self._api_version == "v3":
            url = f"{self.base_url}/users/login/"
        res = await self._websession.get(url)
        try:
            cookie = res.headers.get("Set-Cookie")
            pattern = "=(.*?);"
            csrftoken = re.search(pattern, cookie).group(1)
        except Exception as e:
            LOGGER.error(f"Stromer error: api call failed: {e} with content {res}")
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
            url, data=data, headers=dict(Referer=url), allow_redirects=False
        )
        next_loc = res.headers.get("Location")
        next_url = f"{self.base_url}{next_loc}"
        res = await self._websession.get(next_url, allow_redirects=False)
        self._code = res.headers.get("Location")
        self._code = self._code.split("=")[1]

    async def stromer_get_access_token(self):
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

    async def stromer_call_api(self, endpoint):
        url = f"{self.base_url}/rapi/mobile/v4.1/{endpoint}"
        if self._api_version == "v3":
            url = f"{self.base_url}/rapi/mobile/v2/{endpoint}"

        headers = {"Authorization": f"Bearer {self._token}"}
        res = await self._websession.get(url, headers=headers, data={})
        ret = json.loads(await res.text())
        LOGGER.debug("API call status: %s" % res.status)
        LOGGER.debug("API call returns: %s" % ret)
        return ret["data"][0]


class ApiError(Exception):
    """Error to indicate something wrong with the API."""
