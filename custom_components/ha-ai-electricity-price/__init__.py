from typing import Any, Dict, Optional
from pyeloverblik import Eloverblik
import json
import logging
from datetime import datetime, timedelta
from homeassistant.core import HomeAssistant, Event
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_STATE_CHANGED
from homeassistant.helpers.event import async_track_time_interval, async_track_state_change_event
from .const import (
    DOMAIN,
    ENTITY_ID,
    CONF_PRICE_SENSOR,
    CONF_ELOVERBLIK_TOKEN,
    CONF_METERING_POINT,
    ATTR_TRANS_NETTARIFF,
    ATTR_SYSTEMTARIFF,
    ATTR_HOUR_NETTARIFF,
    ATTR_ELAFGIFT,
    ATTR_TODAY,
    ATTR_TOMORROW,
)
from .sensor import ElectricityPriceSensor

_LOGGER = logging.getLogger(__name__)


class ElOverblikData:
    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry):
        self._hass = hass
        self._config_entry = config_entry
        self._all_fees = {
            "today": [],
            "tomorrow": [],
            "total_today": [],
            "total_tomorrow": [],
            "state_class": None,
            "unit": None,
            "currency": None,
            "country": None,
            "region": None,
        }

    async def async_setup(self):

        # API CALL
        self._all_fees = await self.async_get_fees()
        # Add your API call code here, using self._config_entry.data[CONF_ELOVERBLIK_TOKEN],
        # self._config_entry.data[CONF_METERING_POINT], and self._config_entry.data[CONF_PRICE_SENSOR]

        added_today: list[float] = self._all_fees[ATTR_HOUR_NETTARIFF]
        added_tomorrow: list[float] = self._all_fees[ATTR_HOUR_NETTARIFF]  # Update once you can get tomorrow fees

        async def update_sensor(event: Event) -> None:
            new_state = event.data.get('new_state')
            if new_state is None:
                return
            # Update sensor.total_electricity_price here
            today = [x + y for x, y in zip(new_state.attributes.get('today'), added_today)]
            tomorrow = [x + y for x, y in zip(new_state.attributes.get('tomorrow'), added_tomorrow)]  # Maybe this won't work if 'tomrrow' is an empty list?
            total_today = [{"start": x['start'], "end": x['end'], "value": y} for x, y in zip(new_state.attributes.get('raw_today'), today)]
            total_tomorrow = [{"start": x['start'], "end": x['end'], "value": y} for x, y in zip(new_state.attributes.get('raw_tomorrow'), tomorrow)]
            attributes = {
                "today": today,
                "tomorrow": tomorrow,
                "total_today": total_today,
                "total_tomorrow": total_tomorrow,
                "state_class": new_state.attributes.get('state_class'),
                "unit": new_state.attributes.get('unit'),
                "currency": new_state.attributes.get('currency'),
                "country": new_state.attributes.get('country'),
                "region": new_state.attributes.get('region'),
            }
            now_hour = int(datetime.strftime(datetime.now(), "%H"))
            self._hass.states.async_set(ENTITY_ID, new_state.state + added_today[now_hour], attributes)

        async_track_state_change_event(self._hass, [CONF_PRICE_SENSOR], update_sensor)

        async def async_update_data() -> None:
            # API CALL
            self._all_fees = await self.async_get_fees()
            # Add your API call code here

        async_track_time_interval(self._hass, async_update_data, timedelta(days=1))

        # This sets the (initial) state of the entity to `0` with attributes being the last argument.
        self._hass.states.async_set(ENTITY_ID, 0, self._all_fees)

    async def async_get_fees(self):
        """Get fees from the eloverblik API.
        Default to using the ones in the sensor attributes if unavailable.
        TODO: Get both today and tomorrow fees.
        """

        _token = self._config_entry[CONF_ELOVERBLIK_TOKEN]
        _metering_point = self._config_entry[CONF_METERING_POINT]

        client = Eloverblik(_token)
        data = client.get_latest(_metering_point)
        if int(data.status) == 200:
            # {'transmissions_nettarif': 0.058, 'systemtarif': 0.054, 'elafgift': 0.008, 'nettarif_c_time': [0.1837, 0.1837, 0.1837, 0.1837, 0.1837, 0.1837, 0.5511, 0.5511, 0.5511, 0.5511, 0.5511, 0.5511, 0.5511, 0.5511, 0.5511, 0.5511, 0.5511, 1.6533, 1.6533, 1.6533, 1.6533, 0.5511, 0.5511, 0.5511]}
            charges = json.loads(data.charges)
            # Charges are in øre per Wh. Multiply by 1000 and divide by 100 (i.e., multiply by 10) to get DKK/kWh.
            trans_net_tariff = float(charges[ATTR_TRANS_NETTARIFF]) * 10
            system_tariff = float(charges[ATTR_SYSTEMTARIFF]) * 10
            elafgift = float(charges[ATTR_ELAFGIFT]) * 10
            hour_net_tariff = [float(i) * 10 for i in charges[ATTR_HOUR_NETTARIFF]]
        else:
            trans_net_tariff = self._hass.states.get(ENTITY_ID).attribute.get(ATTR_TRANS_NETTARIFF)
            system_tariff = self._hass.states.get(ENTITY_ID).attribute.get(ATTR_SYSTEMTARIFF)
            elafgift = self._hass.states.get(ENTITY_ID).attribute.get(ATTR_ELAFGIFT)
            hour_net_tariff = self._hass.states.get(ENTITY_ID).attribute.get(ATTR_HOUR_NETTARIFF)

            # Is this how to get?? self.hass.states.get(ENTITY_ID).attribute.get("ATTR_TARIFS")
        all_fees_today = {
            ATTR_TRANS_NETTARIFF: trans_net_tariff,
            ATTR_SYSTEMTARIFF: system_tariff,
            ATTR_ELAFGIFT: elafgift,
            ATTR_HOUR_NETTARIFF: hour_net_tariff
        }

        all_fees_tomorrow = all_fees_today  # Update once it's possible to get tomorrow tariffs from API call

        all_fees = {
            ATTR_TODAY: all_fees_today,
            ATTR_TOMORROW: all_fees_tomorrow
        }

        return all_fees


async def async_setup(hass: HomeAssistant, config: Dict[str, Any]) -> bool:
    return True


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    data = ElOverblikData(hass, config_entry)
    await data.async_setup()
    hass.data[DOMAIN] = data
    hass.async_create_task(hass.config_entries.async_forward_entry_setup(config_entry, "sensor"))
    return True

