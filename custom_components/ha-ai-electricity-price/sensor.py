from pyeloverblik import Eloverblik
import json
from datetime import datetime, timedelta
from typing import Any, Union, Mapping
from collections.abc import Callable
from homeassistant import config_entries
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.event import (
    async_track_state_change,
    async_track_time_change,
    async_track_state_change_event
)
from homeassistant.helpers.typing import (
    ConfigType,
    DiscoveryInfoType,
    HomeAssistantType,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.core import (
    callback,
    HomeAssistant
)
import logging
from .const import (
    DOMAIN,
    ENTITY_ID,
    CONF_NAME,
    CONF_PRICE_SENSOR,
    ATTR_TODAY,
    ATTR_TOMORROW,
    CONF_ELOVERBLIK_TOKEN,
    CONF_METERING_POINT,
    ATTR_FRIENDLY_NAME,
    ATTR_TRANS_NETTARIF,
    ATTR_SYSTEMTARIF,
    ATTR_ELAFGIFT,
    ATTR_HOUR_NETTARIF
)

_LOGGER = logging.getLogger(__name__)


class ElectricityPriceSensor(CoordinatorEntity, Entity):
    def __init__(self, coordinator, hass: HomeAssistant, config):
        # self._electricity_price = electricity_price
        super().__init__(coordinator)
        self.coordinator = coordinator
        self._state = None
        self._attributes: dict[str, Any] = {ATTR_FRIENDLY_NAME: "Total Electricity Price"}
        self.config = config
        self.price_sensor = self.config
        self._name = CONF_NAME
        self.hass = hass
        self.vat_multiplier: float = 1.25
        self._attr_unique_id = f"{self._name}_{config[CONF_METERING_POINT]}"

        if not self.config["fees"][ATTR_TODAY]:
            self.async_update_fees()

    @property
    def name(self):
        return "Electricity Price Sensor"

    @property
    def state(self):
        return self._state

    @property
    def should_poll(self):
        return False

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        return self._attributes

    @callback
    def _handle_update(self, event):
        new_state = event.data.get('new_state')
        if new_state is None:
            return

        self._state = new_state.state
        self._attributes = new_state.attributes

        self.async_write_ha_state()

    async def async_added_to_hass(self):
        self.async_on_remove(
            self.hass.bus.async_listen(
                'state_changed',
                self._handle_update
            )
        )

        async_track_state_change(
            self.hass,
            self.price_sensor,
            self.async_track_price_sensor,
            None,  # Is this how to use? I want any state change.
            None
        )

        update_time = datetime.strptime('00:00:14', '%H:%M:%M')

        async_track_time_change(
            self.hass,
            self.async_update_fees,
            0,
            0,
            4
        )

        async_track_time_change()

    async def async_track_price_sensor(self, entity_id, old_state, new_state) -> None:
        """Update on price sensor state change"""
        hour_now = datetime.strftime(datetime.now(), "%H")
        trans_net_tarif = float(self.config["fees"][ATTR_TODAY]["transmissions_nettarif"])
        system_tarif = float(self.config["fees"][ATTR_TODAY]["systemtarif"])
        elafgift = float(self.config["fees"][ATTR_TODAY]["elafgift"])
        hour_net_tarif = self.config["fees"][ATTR_TODAY]["nettarif_c_time"]

        self._state = (new_state + trans_net_tarif + system_tarif + elafgift + float(hour_net_tarif[hour_now])) * self.vat_multiplier

    async def async_update_fees(self, now=None) -> None:
        """Update fees from API endpoint"""
        self.get_fees()
        self.update_attributes()

    def get_fees(self) -> None:
        """Get fees from the eloverblik API.
        Default to using the ones in the sensor attributes if unavailable.
        TODO: Get both today and tomorrow fees. Is this possible?
        """

        _token = self.config[CONF_ELOVERBLIK_TOKEN]
        _metering_point = self.config[CONF_METERING_POINT]

        client = Eloverblik(_token)
        data = client.get_latest(_metering_point)
        if int(data.status) == 200:
            # {'transmissions_nettarif': 0.058, 'systemtarif': 0.054, 'elafgift': 0.008, 'nettarif_c_time': [0.1837, 0.1837, 0.1837, 0.1837, 0.1837, 0.1837, 0.5511, 0.5511, 0.5511, 0.5511, 0.5511, 0.5511, 0.5511, 0.5511, 0.5511, 0.5511, 0.5511, 1.6533, 1.6533, 1.6533, 1.6533, 0.5511, 0.5511, 0.5511]}
            charges = json.loads(data.charges)
            # Charges are in øre per Wh. Multiply by 1000 and divide by 100 (i.e., multiply by 10) to get DKK/kWh.
            trans_net_tarif = float(charges[ATTR_TRANS_NETTARIF]) * 10
            system_tarif = float(charges[ATTR_SYSTEMTARIF]) * 10
            elafgift = float(charges[ATTR_ELAFGIFT]) * 10
            hour_net_tarif = [float(i) * 10 for i in charges[ATTR_HOUR_NETTARIF]]
            self.config["fees"][ATTR_TODAY] = {
                'transmissions_nettarif': trans_net_tarif,
                'systemtarif': system_tarif,
                'elafgift': elafgift,
                'nettarif_c_time': hour_net_tarif
            }

        _LOGGER.debug(f"Fees today are: {self.config["fees"][ATTR_TODAY]}")

    def update_attributes(self):
        """Update all attributes"""

        trans_net_tarif = float(self.config["fees"][ATTR_TODAY]["transmissions_nettarif"])
        system_tarif = float(self.config["fees"][ATTR_TODAY]["systemtarif"])
        elafgift = float(self.config["fees"][ATTR_TODAY]["elafgift"])
        hour_net_tarif = self.config["fees"][ATTR_TODAY]["nettarif_c_time"]
        raw_today = []
        raw_tomorrow = []

        price_sensor = self.config[CONF_PRICE_SENSOR]
        state = self.hass.states.get(price_sensor)
        if state:
            raw_today = state.attributes.get(ATTR_TODAY, [])
            raw_tomorrow = state.attributes.get(ATTR_TOMORROW, [])

        fees_today = [
            self.vat_multiplier * (float(hour_net_tarif[i]) + trans_net_tarif + system_tarif + elafgift) for i in range(len(hour_net_tarif))
        ]
        total_today = [
            self.vat_multiplier * float(raw_today[i] + fees_today[i] for i in range(len(raw_today)))
        ]

        fees_tomorrow = [
            self.vat_multiplier * (float(hour_net_tarif[i]) + trans_net_tarif + system_tarif + elafgift) for i in range(len(hour_net_tarif))
        ]
        total_tomorrow = [
            self.vat_multiplier * float(raw_today[i] + fees_tomorrow[i] for i in range(len(raw_tomorrow)))
        ]

        self._attributes["fees_today"] = fees_today
        self._attributes["fees_tomorrow"] = fees_tomorrow
        self._attributes["total_today"] = total_today
        self._attributes["total_tomorrow"] = total_tomorrow


async def async_setup_entry(
        hass: HomeAssistant,
        config_entry: config_entries.ConfigEntry,
        async_add_entities
):
    """Set up the sensor platform."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    config = config_entry.data
    async_add_entities([ElectricityPriceSensor(coordinator, hass, config)])


async def async_setup_platform(
        hass: HomeAssistantType,
        config: ConfigType,
        async_add_entities: Callable,
        discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the sensor platform."""
    _LOGGER.debug("Setting up platform for Home Occupancy.")
    sensors = [ENTITY_ID]
    async_add_entities(sensors, update_before_add=True)
