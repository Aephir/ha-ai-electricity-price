import logging
from .const import (
    DOMAIN,
    ATTR_TOMORROW,
    SENSOR_PLATFORM,
    CONF_PRICE_SENSOR
)
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

    electricity_price = TestingIntegration(hass, price_sensor)
    hass.data[DOMAIN][entry.entry_id] = electricity_price

    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, SENSOR_PLATFORM)
    )

    # Listen for changes in price_sensor state
    async_track_state_change_event(hass, [price_sensor], electricity_price.update_fees)

    return True

async def async_setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the sensor platform."""
    if discovery_info is None:
        return

    electricity_price = hass.data[DOMAIN][discovery_info["entry_id"]]
    add_entities([ElectricityPriceSensor(electricity_price)])


# //{
# //  "codeowners": ["@Aephir"],
# //  "config_flow": true,
# //  "dependencies": [],
# //  "documentation": "https://github.com/Aephir/ha-ai-electricity-price",
# //  "domain": "ha-ai-electricity-price",
# //  "iot_class": "cloud_polling",
# //  "name": "Electricity Price",
# //  "integration_type": "service",
# //  "requirements": ["pyeloverblik==0.4.1"],
# //  "version": "0.0.1"
# //}