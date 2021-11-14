"""Define an object to interact with the REST API."""
import asyncio
import json
import logging
import uuid

from typing import Optional

from aiohttp import ClientSession, ClientTimeout
from aiohttp.client_exceptions import ClientError

from .const import (
    REST_API_BASE,
    DEVICE_USER_AGENT,
    LOGIN_APP_ID_EU,
    VERIFY_SSL,
    SYSTEM_PROXY
)
from .errors import RequestError
from .oauth import Oauth

LOGGER = logging.getLogger(__name__)

DEFAULT_LIMIT: int = 288
DEFAULT_TIMEOUT: int = 30


class API:
    """Define the API object."""

    def __init__(
        self,
        oauth: Oauth,
        session: Optional[ClientSession] = None,
        region: str = None
    ) -> None:
        """Initialize."""
        self._session: ClientSession = session
        self._oauth: Oauth = oauth
        self._region = region
        self._guid = str(uuid.uuid4())

    async def _request(self, method: str, endpoint: str, **kwargs) -> list:
        """Make a request against the API."""

        url = REST_API_BASE + endpoint

        kwargs.setdefault("headers", {})

        token = await self._oauth.async_get_cached_token()

        kwargs["headers"] = {
            "Accept": "*/*",
            "Authorization": "Bearer " + token["access_token"],
            "Guid": self._guid,
            "X-ApplicationName": LOGIN_APP_ID_EU,
            "User-Agent": DEVICE_USER_AGENT,
        }

        #use_running_session = self._session and not self._session.closed

        use_running_session = False
        LOGGER.debug("API - Request - Running Session : %s", use_running_session)

        if use_running_session:
            LOGGER.debug("API - Request - Running Session - URL: %s", url)
            session = self._session
        else:
            LOGGER.debug("API - Request - New Session - URL: %s", url)
            session = ClientSession(timeout=ClientTimeout(total=DEFAULT_TIMEOUT))

        try:
            async with session.request(method, url, proxy=SYSTEM_PROXY, verify_ssl=VERIFY_SSL, **kwargs) as resp:
                return await resp.json()
        except ClientError as err:
            raise RequestError(f"Error requesting data from {url}: {err}")
        finally:
            if not use_running_session:
                await session.close()

    async def get_user_info(self) -> list:
        """Get all devices associated with an API key."""
        return await self._request("get", "/seqc/v0/users/current")

    async def get_car_details_init(self, vin:str) -> list:
        """Get all devices infos associated with an fin."""
        return await self._request("get", f"/seqc/v0/vehicles/{ vin }/init-data?requestedData=BOTH&countryCode=DE&locale=de-DE")

    async def get_car_details(self, vin:str) -> list:
        """Get all devices infos associated with an fin."""
        return await self._request("get", f"/seqc/v0/vehicles/{ vin }/refresh-data")


    async def get_car_capabilities_commands(self, vin:str) -> list:
        return await self._request("get", f"/v1/vehicle/{vin}/capabilities/commands")
