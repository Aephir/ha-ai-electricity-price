from typing import Any, Dict, Optional
import voluptuous as vol
from homeassistant import config_entries
from .const import (
    DOMAIN,
    CONF_ELOVERBLIK_TOKEN,
    CONF_METERING_POINT,
    CONF_PRICE_SENSOR,
)

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        errors: Dict[str, str] = {}
        if user_input is not None:
            return await self.async_step_details(user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_PRICE_SENSOR, default="sensor.nordpool_kwh_dk2_dkk_3_095_0"): str,
                }
            ),
            errors=errors,
        )

    async def async_step_details(self, user_input: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        errors: Dict[str, str] = {}
        if user_input is not None:
            return self.async_show_form(
                step_id="details",
                data_schema=vol.Schema(
                    {
                        vol.Required(CONF_ELOVERBLIK_TOKEN): str,
                        vol.Required(CONF_METERING_POINT): str,
                    }
                ),
                errors=errors,
            )

        return self.async_create_entry(title="Electricity Price", data=user_input)
