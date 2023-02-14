"""The Smart EQ connect 2021 integration."""
import asyncio
from datetime import datetime, timedelta
import time
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import SOURCE_REAUTH, ConfigEntry
from homeassistant.const import LENGTH_KILOMETERS, LENGTH_MILES
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import aiohttp_client
import homeassistant.helpers.device_registry as dr
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.util import slugify
from homeassistant.util.unit_system import US_CUSTOMARY_SYSTEM

from .car import Car, Features
from .client import Client
from .const import (
    ATTR_MB_MANUFACTURER,
    CONF_REGION,
    CONF_VIN,
    DOMAIN,
    LOGGER,
    SERVICE_PREHEAT_START,
    SERVICE_VIN_SCHEMA,
    SMARTEQ_COMPONENTS,
    Sensor_Config_Fields as scf,
)
from .errors import WebsocketError

CONFIG_SCHEMA = vol.Schema({DOMAIN: vol.Schema({})}, extra=vol.ALLOW_EXTRA)
DEBUG_ADD_FAKE_VIN = False


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Smart EQ connect 2021 component."""

    if DOMAIN not in config:
        return True


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    """Set up Smart EQ connect 2021 from a config entry."""

    try:

        # Todo: Find the right way to migrate old configs
        region = config_entry.data.get(CONF_REGION, None)
        if region is None:
            region = "Europe"

        smarteq = SmartEQContext(hass, config_entry, region=region)

        token_info = await smarteq.client.oauth.async_get_cached_token()

        if token_info is None:
            LOGGER.error("Authentication failed. Please reauthenticate.")
            hass.async_create_task(
                hass.config_entries.flow.async_init(
                    DOMAIN,
                    context={"source": SOURCE_REAUTH},
                    data=config_entry,
                )
            )
            return False

        masterdata = await smarteq.client.api.get_user_info()
        smarteq.client._write_debug_json_output(masterdata, "md")

        for car in masterdata.get("authorizations"):

            # Car is excluded, we do not add this
            if car.get("fin") in config_entry.options.get("excluded_cars", ""):
                continue

            car_details = await smarteq.client.api.get_car_details_init(car.get("fin"))
            smarteq.client._write_debug_json_output(car_details, "cd")

            dev_reg = dr.async_get(hass)
            dev_reg.async_get_or_create(
                config_entry_id=config_entry.entry_id,
                connections=set(),
                identifiers={(DOMAIN, car.get("fin"))},
                manufacturer=ATTR_MB_MANUFACTURER,
                model=car_details.get("vehicleData")
                .get("salesRelatedInformation")
                .get("baumuster")
                .get("baumusterDescription"),
                name=car.get("licensePlate", car.get("fin")),
            )

            current_car = Car()
            current_car.finorvin = car.get("fin")
            current_car.licenseplate = car.get("licensePlate", car.get("fin"))
            current_car._last_message_received = int(round(time.time() * 1000))

            smarteq.client.cars.append(current_car)
            LOGGER.debug("Init - car added - %s", current_car.finorvin)

        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN] = smarteq

        async def async_update_data():
            """Fetch data from API endpoint.

            This is the place to pre-process the data to lookup tables
            so entities can quickly look up their data.
            """
            return await smarteq.client.update()

        async def preheat_start(call) -> None:
            await smarteq.client.api.start_preheating(call.data.get(CONF_VIN))

        hass.services.async_register(DOMAIN, SERVICE_PREHEAT_START, preheat_start, schema=SERVICE_VIN_SCHEMA)

        await smarteq.on_dataload_complete()

    except WebsocketError as err:
        LOGGER.error("Config entry failed: %s", err)
        raise ConfigEntryNotReady from err

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[hass.config_entries.async_forward_entry_unload(entry, component) for component in SMARTEQ_COMPONENTS]
        )
    )
    if unload_ok:
        if hass.data[DOMAIN]:
            del hass.data[DOMAIN]

    return unload_ok


class SmartEQContext:
    def __init__(self, hass, config_entry, region):
        self._config_entry = config_entry
        self._entry_setup_complete: bool = False
        self._hass = hass
        self._region = region
        self.client = Client(
            hass=hass,
            session=aiohttp_client.async_get_clientsession(hass),
            config_entry=config_entry,
            region=self._region,
        )

    async def update_all(self, *_: Any):
        LOGGER.debug("SmartEQ - Cars update all")
        await self.client.update()

    async def on_dataload_complete(self, *_: Any):
        LOGGER.info("Car Load complete - start sensor creation")

        await self.client.update()

        if not self._entry_setup_complete:
            for component in SMARTEQ_COMPONENTS:
                self._hass.async_create_task(
                    self._hass.config_entries.async_forward_entry_setup(self._config_entry, component)
                )

        async_track_time_interval(self._hass, self.update_all, timedelta(seconds=30))

        self._entry_setup_complete = True


class SmartEQEntity(Entity):
    """Entity class for SmartEQ devices."""

    def __init__(self, hass, data, internal_name, sensor_config, vin):
        """Initialize the SmartEQ entity."""
        self._hass = hass
        self._data = data
        self._vin = vin
        self._internal_name = internal_name
        self._sensor_config = sensor_config

        self._state = None
        self._sensor_name = sensor_config[scf.DISPLAY_NAME.value]
        self._internal_unit = sensor_config[scf.UNIT_OF_MEASUREMENT.value]
        self._unit = sensor_config[scf.UNIT_OF_MEASUREMENT.value]
        self._feature_name = sensor_config[scf.OBJECT_NAME.value]
        self._object_name = sensor_config[scf.ATTRIBUTE_NAME.value]
        self._attrib_name = sensor_config[scf.VALUE_FIELD_NAME.value]
        self._extended_attributes = sensor_config[scf.EXTENDED_ATTRIBUTE_LIST.value]
        self._unique_id = slugify(f"{self._vin}_{self._internal_name}")
        self._car = next(car for car in self._data.client.cars if car.finorvin == self._vin)

        self._licenseplate = self._car.licenseplate
        self._name = f"{self._licenseplate} {self._sensor_name}"

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def unique_id(self) -> str:
        """Return the name of the sensor."""
        return self._unique_id

    def device_retrieval_status(self):
        if self._sensor_name == "Car":
            return "VALID"

        return self._get_car_value(self._feature_name, self._object_name, "retrievalstatus", "error")

    @property
    def device_info(self):
        """Return the device info."""

        return {"identifiers": {(DOMAIN, self._vin)}}

    @property
    def device_class(self):
        return self._sensor_config[scf.DEVICE_CLASS.value]

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""

        state = {
            "car": self._licenseplate,
            "vin": self._vin,
        }

        for item in ["retrievalstatus", "timestamp"]:
            value = self._get_car_value(self._feature_name, self._object_name, item, None)
            if value:
                state[item] = value if item != "timestamp" else datetime.fromtimestamp(int(value))

        if self._extended_attributes is not None:
            for attrib in self._extended_attributes:

                retrievalstatus = self._get_car_value(self._feature_name, attrib, "retrievalstatus", "error")

                if retrievalstatus == "VALID" or retrievalstatus == 0:
                    state[attrib] = self._get_car_value(self._feature_name, attrib, "value", "error")

                if retrievalstatus == "NOT_RECEIVED":
                    state[attrib] = "NOT_RECEIVED"
        return state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        if self._unit == LENGTH_KILOMETERS and not self._hass.config.units is US_CUSTOMARY_SYSTEM:
            return LENGTH_MILES
        else:
            return self._unit

    @property
    def icon(self):
        """Return the icon."""
        return self._sensor_config[scf.ICON.value]

    @property
    def should_poll(self):
        return True

    def update(self):
        """Get the latest data and updates the states."""

        self._state = self._get_car_value(self._feature_name, self._object_name, self._attrib_name, "error")

    def _get_car_value(self, feature, object_name, attrib_name, default_value):
        value = None

        if object_name:
            if not feature:
                value = getattr(
                    getattr(self._car, object_name, default_value),
                    attrib_name,
                    default_value,
                )
            else:
                value = getattr(
                    getattr(
                        getattr(self._car, feature, default_value),
                        object_name,
                        default_value,
                    ),
                    attrib_name,
                    default_value,
                )

        else:
            value = getattr(self._car, attrib_name, default_value)

        return value

    def update_callback(self):
        """Schedule a state update."""
        self.schedule_update_ha_state(True)

    async def async_added_to_hass(self):
        """Add callback after being added to hass.

        Show latest data after startup.
        """
        self._car.add_update_listener(self.update_callback)
        self.async_schedule_update_ha_state(True)

    async def async_will_remove_from_hass(self):
        """Entity being removed from hass."""
        self._car.remove_update_callback(self.update_callback)
