import logging
from .const import DOMAIN, ATTR_TOMORROW, SENSOR_PLATFORM, CONF_PRICE_SENSOR
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.event import async_track_state_change_event

_LOGGER = logging.getLogger(__name__)

class TestingIntegration:
    def __init__(self, hass, price_sensor):
        self._hass = hass
        self._price_sensor = price_sensor
        self.tariff_dict = {}
        self.update_fees()

    def update_fees(self):
        self.tariff_dict = {
            "transmissions_nettarif": 1,
            "systemtarif": 2,
            "elafgift": 3,
            "nettarif_c_time": [4]*24
        }

async def async_setup(hass, config):
    hass.data[DOMAIN] = {}
    return True

async def async_setup_entry(hass, entry):
    price_sensor = entry.data[CONF_PRICE_SENSOR]

    testing_integration = TestingIntegration(hass, price_sensor)
    hass.data[DOMAIN][entry.entry_id] = testing_integration

    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, SENSOR_PLATFORM)
    )

    # Listen for changes in price_sensor state
    async_track_state_change_event(hass, [price_sensor], testing_integration.update_fees)

    return True
