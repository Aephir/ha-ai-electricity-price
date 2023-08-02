from homeassistant.helpers.entity import Entity
from homeassistant.core import callback
from .const import DOMAIN, ATTR_TOMORROW, CONF_PRICE_SENSOR

class TestingIntegrationSensor(Entity):
    def __init__(self, testing_integration):
        self._testing_integration = testing_integration
        self._state = None
        self._attributes = {}

    @property
    def name(self):
        return "Testing Integration Sensor"

    @property
    def state(self):
        return self._state

    @property
    def should_poll(self):
        return False

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
            self._hass.bus.async_listen(
                'state_changed',
                self._handle_update
            )
        )
