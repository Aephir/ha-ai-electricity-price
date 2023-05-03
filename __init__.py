"""The electricity_price integration."""
import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
    CONF_ELOVERBLIK_TOKEN,
    CONF_METERING_POINT,
    CONF_PRICE_SENSOR,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor"]

SCAN_INTERVAL = timedelta(minutes=1)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up electricity_price from a config entry."""
    # Store the API token and metering point in the config entry data
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        CONF_ELOVERBLIK_TOKEN: entry.data[CONF_ELOVERBLIK_TOKEN],
        CONF_METERING_POINT: entry.data[CONF_METERING_POINT],
    }

    # Set up the update coordinator
    coordinator = ElectricityPriceDataUpdateCoordinator(hass, entry)
    await coordinator.async_refresh()
    hass.data[DOMAIN][entry.entry_id]["coordinator"] = coordinator

    # Set up the entities
    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload an electricity_price config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


class ElectricityPriceDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching electricity price data from the API."""

    def __init__(self, hass, entry):
        """Initialize the coordinator."""
        self.hass = hass
        self.eloverblik_token = entry.data[CONF_ELOVERBLIK_TOKEN]
        self.metering_point = entry.data[CONF_METERING_POINT]
        self.price_sensor = entry.options.get(CONF_PRICE_SENSOR, "sensor.nordpool_kwh_dk2_dkk_3_095_0")

        # Set up the update interval
        update_interval = timedelta(days=1, minutes=10)

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=update_interval,
        )

    async def _async_update_data(self):
        """Fetch the latest data from the API."""
        # Make API call to fetch data
        # Replace the following comment with the actual code to make the API call
        _LOGGER.debug("Making API call to fetch data")
        data = {}

        if data is None:
            raise UpdateFailed("Unable to fetch data from API")

        return data


async def async_update_entity(hass, coordinator, entity):
    """Update the electricity price sensor with the latest data."""
    price_sensor_state = hass.states.get(entity.price_sensor)
    tomorrow_raw = price_sensor_state.attributes.get("tomorrow_raw")

    # Only update the sensor if we have data for tomorrow
    if tomorrow_raw:
        data = coordinator.data
        price = data.get("price")
        total_price = round(price * float(tomorrow_raw), 2)
        entity.async_write_ha_state()
        _LOGGER.debug("Total electricity price for tomorrow: %s", total_price)
    else:
        _LOGGER.debug("No data for tomorrow")


class ElectricityPriceSensor(Entity):
    """Class for the electricity price sensor."""

    def __init__(self, coordinator):
        """Initialize the sensor."""
        self.coordinator = coordinator
        self._state = None
        self._unit_of_measurement = "DKK/kWh"

    async def async_update(self):
        """Update the sensor."""
        await self.coordinator.async_request_refresh()

        price = self.coordinator.data.get("price")

        if price is not None:
            self._state = round(price, 2)

    @property
    def name(self):
        """Return the name of the sensor."""
        return "Electricity Price"

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._unit_of_measurement

    @property
    def device_info(self):
        """Return device information for the sensor."""
        return {
            "identifiers": {(DOMAIN, "electricity_price")},
            "name": "Electricity Price",
            "manufacturer": "Unknown",
        }
