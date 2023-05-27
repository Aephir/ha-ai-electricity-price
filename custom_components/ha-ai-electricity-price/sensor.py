from typing import Any, Optional
from homeassistant.helpers.entity import Entity
from homeassistant import config_entries, core
from .const import (
    DOMAIN,
    NAME,
    ENTITY_ID
)

class ElectricityPriceSensor(Entity):
    def __init__(self, hass: core.HomeAssistant) -> None:
        self._state: Optional[Any] = None
        self._name: str = NAME
        self._hass: core.HomeAssistant = hass

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

    async def async_update(self) -> None:
        self._state = self._hass.states.get(ENTITY_ID).state
