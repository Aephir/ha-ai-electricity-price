"""Config flow for Electricity Price integration."""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_API_KEY, CONF_URL
from .const import DOMAIN, CONF_ELOVERBLIK_TOKEN, CONF_METERING_POINT, CONF_PRICE_SENSOR

class ElectricityPriceConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Electricity Price config flow."""

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        errors = {}

        # Set defaults for API URL and price sensor
        api_url = user_input.get(CONF_URL, "https://api.eloverblik.dk/CustomerApi/")
        price_sensor = user_input.get(CONF_PRICE_SENSOR, "sensor.nordpool_kwh_dk2_dkk_3_095_0")

        if user_input is not None:
            # Validate user input
            eloverblik_token = user_input[CONF_ELOVERBLIK_TOKEN]
            metering_point = user_input[CONF_METERING_POINT]

            # Create a unique identifier for this integration using the metering_point value
            unique_id = f"{metering_point}_{price_sensor}"

            # Create an entry in the registry for this integration
            self._async_abort_entries_match({CONF_METERING_POINT: metering_point})
            return self.async_create_entry(
                title=unique_id,
                data={
                    CONF_ELOVERBLIK_TOKEN: eloverblik_token,
                    CONF_METERING_POINT: metering_point,
                    CONF_PRICE_SENSOR: price_sensor,
                    CONF_URL: api_url,
                },
            )

        # Render form for user input
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ELOVERBLIK_TOKEN): str,
                    vol.Required(CONF_METERING_POINT): str,
                    vol.Optional(CONF_URL, default=api_url): str,
                    vol.Optional(CONF_PRICE_SENSOR, default=price_sensor): str,
                }
            ),
            errors=errors,
        )
