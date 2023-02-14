import collections
from datetime import datetime

ODOMETER_OPTIONS = [
    "odo",
    "ecoscoretotal",
    "ecoScoreFluentDriving",
    "ecoScoreSpeed",
    "serviceintervaldays",
    "serviceintervaldistance",
]

LOCATION_OPTIONS = []

TIRE_OPTIONS = ["tirewarningsrdk"]

WINDOW_OPTIONS = []

DOOR_OPTIONS = []

ELECTRIC_OPTIONS = [
    "rangeelectric",
    "electricconsumptionstart",
    "soc",
    "chargingactive",
    "chargingstatus",
    "precondNow",
]

BINARY_SENSOR_OPTIONS = []

AUX_HEAT_OPTIONS = []

PRE_COND_OPTIONS = []

REMOTE_START_OPTIONS = []

CAR_ALARM_OPTIONS = []


class Car(object):
    def __init__(self):
        self.licenseplate = None
        self.finorvin = None
        self._messages_received = collections.Counter(f=0, p=0)
        self._last_message_received = 0
        self._last_command_type = ""
        self._last_command_state = ""
        self._last_command_error_code = ""
        self._last_command_error_message = ""
        self._last_command_time_stamp = 0

        self.binarysensors = None
        self.tires = None
        self.odometer = None
        self.doors = None
        self.location = None
        self.windows = None
        self.features = None
        self.auxheat = None
        self.precond = None
        self.electric = None
        self.car_alarm = None
        self._entry_setup_complete = False
        self._update_listeners = set()

    @property
    def full_update_messages_received(self):
        return CarAttribute(self._messages_received["f"], "VALID", None)

    @property
    def partital_update_messages_received(self):
        return CarAttribute(self._messages_received["p"], "VALID", None)

    @property
    def last_message_received(self):
        if self._last_message_received > 0:
            return CarAttribute(datetime.fromtimestamp(int(round(self._last_message_received / 1000))), "VALID", None)

        return CarAttribute(None, "NOT_RECEIVED", None)

    @property
    def last_command_type(self):
        return CarAttribute(self._last_command_type, "VALID", self._last_command_time_stamp)

    @property
    def last_command_state(self):
        return CarAttribute(self._last_command_state, "VALID", self._last_command_time_stamp)

    @property
    def last_command_error_code(self):
        return CarAttribute(self._last_command_error_code, "VALID", self._last_command_time_stamp)

    @property
    def last_command_error_message(self):
        return CarAttribute(self._last_command_error_message, "VALID", self._last_command_time_stamp)

    def add_update_listener(self, listener):
        """Add a listener for update notifications."""
        self._update_listeners.add(listener)

    def remove_update_callback(self, listener):
        """Remove a listener for update notifications."""
        self._update_listeners.discard(listener)

    def publish_updates(self):
        """Schedule call all registered callbacks."""
        for callback in self._update_listeners:
            callback()


class Tires(object):
    def __init__(self):
        self.name = "Tires"


class Odometer(object):
    def __init__(self):
        self.name = "Odometer"


class Features(object):
    def __init__(self):
        self.name = "Features"


class Windows(object):
    def __init__(self):
        self.name = "Windows"


class Doors(object):
    def __init__(self):
        self.name = "Doors"


class Electric(object):
    def __init__(self):
        self.name = "Electric"


class Auxheat(object):
    def __init__(self):
        self.name = "Auxheat"


class Precond(object):
    def __init__(self):
        self.name = "Precond"


class Binary_Sensors(object):
    def __init__(self):
        self.name = "Binary_Sensors"


class Remote_Start(object):
    def __init__(self):
        self.name = "Remote_Start"


class Car_Alarm(object):
    def __init__(self):
        self.name = "Car_Alarm"


class Location(object):
    def __init__(self, latitude=None, longitude=None, heading=None):
        self.name = "Location"
        self.latitude = None
        self.longitude = None
        self.heading = None
        if latitude is not None:
            self.latitude = latitude
        if longitude is not None:
            self.longitude = longitude
        if heading is not None:
            self.heading = heading


class CarAttribute(object):
    def __init__(self, value, retrievalstatus, timestamp, distance_unit=None, display_value=None, unit=None):
        self.value = value
        self.retrievalstatus = retrievalstatus
        self.timestamp = timestamp
        self.distance_unit = distance_unit
        self.display_value = display_value
        self.unit = unit
