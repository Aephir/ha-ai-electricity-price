import voluptuous as vol
from homeassistant import config_entries
from .const import DOMAIN, CONF_PRICE_SENSOR, CONF_STRING_ONE, CONF_STRING_TWO

@config_entries.HANDLERS.register(DOMAIN)
class FlowHandler(config_entries.ConfigFlow):
    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(
                title=user_input[CONF_PRICE_SENSOR],
                data=user_input,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_PRICE_SENSOR): str,
                }
            ),
        )

    async def async_step_price_sensor(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(
                title=user_input[CONF_STRING_ONE],
                data=user_input,
            )

        return self.async_show_form(
            step_id="price_sensor",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_STRING_ONE): str,
                    vol.Required(CONF_STRING_TWO): str,
                }
            ),
        )
