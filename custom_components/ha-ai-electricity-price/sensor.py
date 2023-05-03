"""Sensor platform for the electricity_price integration."""

from homeassistant.const import ENERGY_KILO_WATT_HOUR
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

SENSOR_NAME = "electricity_price"


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the electricity price sensor."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    async_add_entities(
        [
            ElectricityPriceSensor(
                coordinator,
                entry.unique_id,
                SENSOR_NAME,
                "mdi:currency-usd",
            )
        ],
        True,
    )


class ElectricityPriceSensor(CoordinatorEntity, Entity):
    """Class for the electricity price sensor."""

    def __init__(self, coordinator, unique_id, name, icon):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._unique_id = unique_id
        self._name = name
        self._icon = icon
        self._state = None
        self._unit_of_measurement = f"{ENERGY_KILO_WATT_HOUR}/kr"

    @property
    def unique_id(self):
        """Return a unique ID."""
        return self._unique_id

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return self._icon

    @property
    def state(self):
        """Return the state of the sensor."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get("total_price")

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._unit_of_measurement

    async def async_update(self):
        """Update the sensor."""
        await self.coordinator.async_request_refresh()
