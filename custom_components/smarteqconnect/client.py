import logging
import time
from pathlib import Path
from typing import Optional

from aiohttp import ClientSession
from homeassistant.core import HomeAssistant

from .api import API
from .car import *
from .const import (
    CONF_COUNTRY_CODE,
    CONF_DEBUG_FILE_SAVE,
    CONF_EXCLUDED_CARS,
    CONF_LOCALE,
    CONF_PIN,
    DEFAULT_CACHE_PATH,
    DEFAULT_COUNTRY_CODE,
    DEFAULT_LOCALE,
    DEFAULT_TOKEN_PATH,
)
from .oauth import Oauth

LOGGER = logging.getLogger(__name__)


class Client:  # pylint: disable-too-few-public-methods
    """define the client."""

    def __init__(
        self,
        *,
        session: Optional[ClientSession] = None,
        hass: Optional[HomeAssistant] = None,
        config_entry=None,
        cache_path: Optional[str] = None,
        region: str = None,
    ) -> None:
        self._hass = hass
        self._region = region
        self._debug_save_path = self._hass.config.path(DEFAULT_CACHE_PATH)
        self._config_entry = config_entry
        self._locale: str = DEFAULT_LOCALE
        self._country_code: str = DEFAULT_COUNTRY_CODE

        if self._config_entry:
            if self._config_entry.options:
                self._country_code = self._config_entry.options.get(CONF_COUNTRY_CODE, DEFAULT_COUNTRY_CODE)
                self._locale = self._config_entry.options.get(CONF_LOCALE, DEFAULT_LOCALE)

        self.oauth: Oauth = Oauth(
            session=session,
            locale=self._locale,
            country_code=self._country_code,
            cache_path=self._hass.config.path(DEFAULT_TOKEN_PATH),
            region=self._region,
        )
        self.api: API = API(session=session, oauth=self.oauth, region=self._region)
        self.cars = []

    @property
    def pin(self) -> str:
        if self._config_entry:
            if self._config_entry.options:
                return self._config_entry.options.get(CONF_PIN, None)
        return None

    @property
    def excluded_cars(self):
        if self._config_entry:
            if self._config_entry.options:
                return self._config_entry.options.get(CONF_EXCLUDED_CARS, [])
        return []

    async def update(self):

        for car in self.cars:
            LOGGER.debug("Update - Car: %s", car.finorvin)
            car_detail = await self.api.get_car_details(car.finorvin)
            # self._write_debug_json_output(car_detail, "upd")
            # LOGGER.debug("Update - Car detail: %s", car_detail)

            car.odometer = self._get_car_values(
                car_detail,
                car.finorvin,
                Odometer() if not car.odometer else car.odometer,
                ODOMETER_OPTIONS,
                False,
                "status",
            )

            car.electric = self._get_car_values(
                car_detail,
                car.finorvin,
                Electric() if not car.electric else car.electric,
                ELECTRIC_OPTIONS,
                False,
                "precond",
            )

            car.tires = self._get_car_values(
                car_detail, car.finorvin, Tires() if not car.tires else car.tires, TIRE_OPTIONS, False, "status"
            )

        self.cars = [car if item.finorvin == car.finorvin else item for item in self.cars]
        return True

    def _get_car_values(self, car_detail, car_id, classInstance, options, update, json_attribute):
        LOGGER.debug("get_car_values %s for %s called", classInstance.name, car_id)

        for option in options:
            if car_detail is not None:

                curr = car_detail.get(json_attribute).get("data").get(option)
                # LOGGER.debug("get_car_values - option: %s - curr - %s", option,curr)
                if curr is not None:

                    value = curr.get("value", -1)
                    status = curr.get("status", 4)
                    ts = curr.get("ts", 0)
                    curr_status = CarAttribute(value, status, ts)
                    setattr(classInstance, option, curr_status)
                else:
                    # Do not set status for non existing values on partial update
                    if not update:
                        curr_status = CarAttribute(0, 4, 0)
                        setattr(classInstance, option, curr_status)
            else:
                setattr(classInstance, option, CarAttribute(-1, -1, None))

        return classInstance

    def _write_debug_json_output(self, data, datatype):

        LOGGER.debug(self._config_entry.options)
        if self._config_entry.options.get(CONF_DEBUG_FILE_SAVE, False):
            path = self._debug_save_path
            Path(path).mkdir(parents=True, exist_ok=True)

            f = open(f"{path}/{datatype}{int(round(time.time() * 1000))}.json", "w")
            f.write(f"{data}")
            f.close()

    def _get_car(self, vin: str):
        for car in self.cars:
            if car.finorvin == vin:
                return car
