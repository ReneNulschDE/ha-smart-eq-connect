"""Define an object to interact with the REST API."""
import base64
import hashlib
import json
import logging
import time
import uuid
from os import urandom
from typing import Optional
from urllib.parse import parse_qs, urlparse

from aiohttp import ClientSession, ClientTimeout
from aiohttp.client_exceptions import ClientError

from .const import (
    DEVICE_USER_AGENT,
    LOGIN_APP_ID_EU,
    LOGIN_BASE_URI,
    REGION_EUROPE,
    REST_API_BASE,
    VERIFY_SSL,
)
from .errors import RequestError

_LOGGER = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 10
SYSTEM_PROXY = None
PROXIES = {}

# SYSTEM_PROXY = "http://localhost:8080"
# PROXIES = {
#  'https': SYSTEM_PROXY,
# }


class Oauth:  # pylint: disable-too-few-public-methods
    """define the client."""

    def __init__(
        self,
        *,
        session: Optional[ClientSession] = None,
        locale: Optional[str] = "DE",
        country_code: Optional[str] = "de-DE",
        cache_path: Optional[str] = None,
        region: str = None,
    ) -> None:
        self.token = None
        self._locale = locale
        self._country_code = country_code
        self._session: ClientSession = session
        self._region: str = region
        self.cache_path = cache_path
        self.code_verifier = self._random_string(64)
        self.code_challenge = self._generate_code_challenge(self.code_verifier)
        self.resume_url = ""

    async def request_pin(self, email: str):
        _LOGGER.info("start request pin %s", email)

        # Step 1: Result is a redirect
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "de-DE,de;q=0.9",
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148",
            "Referer": "https://id.mercedes-benz.com/ciam/auth/login",
            "Accept-Encoding": "gzip, deflate",
        }

        # we allow the redirect
        # we need the cockies and the resume url
        async with self._session.request(
            "GET",
            f"{ LOGIN_BASE_URI }/as/authorization.oauth2?client_id={ LOGIN_APP_ID_EU }&response_type=code&scope=openid+profile+email+phone+ciam-uid+offline_access&redirect_uri=https://oneapp.microservice.smart.mercedes-benz.com&code_challenge={ self.code_challenge }&code_challenge_method=S256",
            headers=headers,
            proxy=SYSTEM_PROXY,
            verify_ssl=VERIFY_SSL,
        ) as resp:
            response_text = await resp.text()
            parsed_url = urlparse(str(resp.url))
            self.resume_url = parse_qs(parsed_url.query)["resume"][0]

        _LOGGER.debug("Request pin - Step 1 - resume_url: %s", self.resume_url)

        # Step 2: We switch to OTP mode
        headers["Accept"] = "application/json, text/plain, */*"
        headers["Content-Type"] = "application/json"
        headers["Origin"] = LOGIN_BASE_URI

        async with self._session.request(
            "POST",
            f"{ LOGIN_BASE_URI }/ciam/auth/login/user",
            data=f'{{"username":"{ email }"}}',
            headers=headers,
            proxy=SYSTEM_PROXY,
            verify_ssl=VERIFY_SSL,
        ) as resp:
            response_text = await resp.text()

        _LOGGER.debug("Request pin - Step 2 - result: %s", response_text)

        # Step 3: We request the OTP
        async with self._session.request(
            "PUT",
            f"{ LOGIN_BASE_URI }/ciam/auth/login/otp",
            data=f'{{"username":"{ email }"}}',
            proxy=SYSTEM_PROXY,
            headers=headers,
            verify_ssl=VERIFY_SSL,
        ) as resp:
            return await resp.json()

    async def async_refresh_access_token(self, refresh_token: str):
        _LOGGER.info("start async refresh_access_token with refresh_token")

        # url = f"{LOGIN_BASE_URI if self._region == 'Europe' else LOGIN_BASE_URI_NA}/auth/realms/Daimler/protocol/openid-connect/token"
        # data = (
        #     f"client_id=app&grant_type=refresh_token&refresh_token={refresh_token}"
        # )

        url = f"{LOGIN_BASE_URI}/as/token.oauth2"
        data = f"client_id=70d89501-938c-4bec-82d0-6abb550b0825&grant_type=refresh_token&refresh_token={refresh_token}"

        headers = self._get_header()
        headers["Content-Type"] = "application/x-www-form-urlencoded"
        headers["Stage"] = "prod"
        headers["X-AuthMode"] = "CIAMNG"
        headers["device-uuid"] = str(uuid.uuid4())

        token_info = await self._async_request(method="post", url=url, data=data, headers=headers)

        if token_info is not None:
            if "refresh_token" not in token_info:
                token_info["refresh_token"] = refresh_token
            token_info = self._add_custom_values_to_token_info(token_info)
            self._save_token_info(token_info)
            self.token = token_info

        return token_info

    async def request_access_token(self, email: str, pin: str):

        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "de-DE,de;q=0.9",
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148",
            "Referer": "https://id.mercedes-benz.com/ciam/auth/login",
            "Accept-Encoding": "gzip, deflate",
        }

        _LOGGER.debug("Request token - Pre Step 4 - resume_url: %s", self.resume_url)
        # Step 4: We submit the OTP
        # Result: JSON, we need the token value
        headers["Accept"] = "application/json, text/plain, */*"
        headers["Content-Type"] = "application/json"
        headers["Origin"] = LOGIN_BASE_URI

        async with self._session.request(
            "POST",
            f"{ LOGIN_BASE_URI }/ciam/auth/login/otp",
            data=f'{{"username":"{ email }", "password":"{ pin }","rememberMe":true}}',
            headers=headers,
            proxy=SYSTEM_PROXY,
            verify_ssl=VERIFY_SSL,
        ) as resp:
            response_json = await resp.json()
            token = response_json.get("token")

        _LOGGER.debug("Request token - Step 4 - token: %s", token)

        # Step 2: We post the token
        # Result is a redirect, we do not want the redirect, just the code out of the Location URL is needed
        headers["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        headers["Content-Type"] = "application/x-www-form-urlencoded"

        async with self._session.request(
            "POST",
            f"{ LOGIN_BASE_URI }{ self.resume_url }",
            data="token=" + token,
            headers=headers,
            proxy=SYSTEM_PROXY,
            allow_redirects=False,
            verify_ssl=VERIFY_SSL,
        ) as resp:
            response_text = await resp.text()
            parsed_url = urlparse(str(resp.headers.get("Location")))
            token = parse_qs(parsed_url.query)["code"][0]

        # Step 3: Holen des Bearer Tokens
        async with self._session.request(
            "POST",
            f"{ LOGIN_BASE_URI }/as/token.oauth2",
            data="grant_type=authorization_code&code="
            + token
            + "&redirect_uri=https%3A%2F%2Foneapp.microservice.smart.mercedes-benz.com&code_verifier="
            + self.code_verifier
            + "&client_id=70d89501-938c-4bec-82d0-6abb550b0825",
            headers=headers,
            proxy=SYSTEM_PROXY,
            allow_redirects=False,
            verify_ssl=VERIFY_SSL,
        ) as resp:
            token_info = await resp.json()

        if token_info is not None:
            token_info = self._add_custom_values_to_token_info(token_info)
            self._save_token_info(token_info)
            self.token = token_info
            return token_info

        return None

    async def async_get_cached_token(self):
        """Gets a cached auth token"""
        _LOGGER.debug("start: async_get_cached_token")
        token_info = None
        if self.cache_path:
            try:
                token_file = open(self.cache_path)
                token_info_string = token_file.read()
                token_file.close()
                token_info = json.loads(token_info_string)

                if self.is_token_expired(token_info):
                    _LOGGER.debug("%s - token expired - start refresh", __name__)
                    if "refresh_token" not in token_info:
                        _LOGGER.warn("Refresh Token is missing - reauth required")
                        return None

                    token_info = await self.async_refresh_access_token(token_info["refresh_token"])

            except IOError:
                pass
        self.token = token_info
        return token_info

    def is_token_expired(self, token_info):
        if token_info is not None:
            now = int(time.time())
            return token_info["expires_at"] - now < 60

        return True

    def _save_token_info(self, token_info):
        _LOGGER.debug("start: _save_token_info to %s", self.cache_path)
        if self.cache_path:
            try:
                token_file = open(self.cache_path, "w")
                token_file.write(json.dumps(token_info))
                token_file.close()
            except IOError:
                _LOGGER.warning("couldn't write token cache to %s", self.cache_path)

    def _add_custom_values_to_token_info(self, token_info):
        """
        Store some values that aren't directly provided by a Web API
        response.
        """
        token_info["expires_at"] = int(time.time()) + token_info["expires_in"]
        # token_info["scope"] = self.OAUTH_SCOPE
        return token_info

    def _get_header(self) -> list:

        header = {
            "X-SessionId": str(uuid.uuid4()),  # "bc667b25-1964-4ff8-98f0-aef3a7f35208",
            "X-TrackingId": str(uuid.uuid4()),  # "abbc223e-bdb8-4808-b299-8ff800b58816",
            "X-Locale": self._locale,
            "User-Agent": DEVICE_USER_AGENT,
            "Content-Type": "application/json; charset=UTF-8",
        }

        header = self._get_region_header(header)

        return header

    def _get_region_header(self, header) -> list:

        if self._region == REGION_EUROPE:
            header["X-ApplicationName"] = LOGIN_APP_ID_EU

        return header

    def _random_string(self, length=64):
        """Generate a random string of fixed length"""

        return str(base64.urlsafe_b64encode(urandom(length)), "utf-8").rstrip("=")

    def _generate_code_challenge(self, code):
        """Generate a hash of the given string"""
        code_challenge = hashlib.sha256()
        code_challenge.update(code.encode("utf-8"))

        return str(base64.urlsafe_b64encode(code_challenge.digest()), "utf-8").rstrip("=")

    async def _async_request(self, method: str, url: str, data: str = "", **kwargs) -> list:
        """Make a request against the API."""

        kwargs.setdefault("headers", {})
        kwargs.setdefault("proxy", SYSTEM_PROXY)
        kwargs.setdefault("verify_ssl", VERIFY_SSL)

        use_running_session = self._session and not self._session.closed

        if use_running_session:
            session = self._session
        else:
            session = ClientSession(timeout=ClientTimeout(total=DEFAULT_TIMEOUT))

        try:
            async with session.request(method, url, data=data, **kwargs) as resp:
                resp.raise_for_status()
                return await resp.json(content_type=None)
        except ClientError as err:
            _LOGGER.error(f"Error requesting data from {url}: {err}")
        except Exception as e:
            _LOGGER.error(f"Error requesting data from {url}: {e}")
        finally:
            if not use_running_session:
                await session.close()
