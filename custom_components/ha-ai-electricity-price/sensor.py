from typing import Any, Optional
from homeassistant.helpers.entity import Entity
from homeassistant import config_entries, core
from .const import (
    DOMAIN,
    NAME,
    ENTITY_ID
)

class ElectricityPriceSensor(Entity):
    def __init__(self, hass: core.HomeAssistant, data) -> None:
        self._state: Optional[Any] = None
        self._name: str = NAME
        self._hass: core.HomeAssistant = hass
        self._data = data
        self._attrs = {}

    @property
    def unique_id(self) -> str:
        return ENTITY_ID

    @property
    def name(self) -> str:
        return self._name

    @property
    def state(self) -> Optional[Any]:
        return self._state

    @property
    def should_poll(self) -> bool:
        return False

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return self._attrs

    async def async_update(self) -> None:
        """
        TODO: Make check that entity exists, otherwise it will raise exception. Handle exception by raising error!
        :return:
        """
        entity = self._hass.states.get(ENTITY_ID)
        if entity is not None:
            self._state = entity.state
            self._attrs = entity.attributes
            self.async_write_ha_state()


async def async_setup_entry(hass, config_entry, async_add_entities):
    async_add_entities([ElectricityPriceSensor(hass, hass.data[DOMAIN])])
