import logging

from homeassistant.helpers.restore_state import RestoreEntity

from . import SmartEQEntity
from .const import DOMAIN, SENSORS

LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Setup the sensor platform."""

    data = hass.data[DOMAIN]

    if not data.client.cars:
        LOGGER.info("No Cars found.")
        return

    sensor_list = []
    for car in data.client.cars:

        for key, value in sorted(SENSORS.items()):
            if value[5] is None or getattr(car.features, value[5], False) is True:
                device = SmartEQSensor(hass=hass, data=data, internal_name=key, sensor_config=value, vin=car.finorvin)
                if device.device_retrieval_status() in [0, "VALID", "NOT_RECEIVED"]:
                    sensor_list.append(device)
                    LOGGER.debug("Sensor added: %s", key)

    async_add_entities(sensor_list, True)


class SmartEQSensor(SmartEQEntity, RestoreEntity):
    """Representation of a Sensor."""

    @property
    def state(self):
        """Return the state of the sensor."""

        if self.device_retrieval_status == "NOT_RECEIVED":
            return "NOT_RECEIVED"

        return self._state

    async def async_added_to_hass(self) -> None:
        """Call when entity about to be added to Home Assistant."""
        await super().async_added_to_hass()
        # __init__ will set self._state to self._initial, only override
        # if needed.
        state = await self.async_get_last_state()
        if state is not None:
            self._state = state.state
