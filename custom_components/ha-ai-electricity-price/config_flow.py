from typing import Any
import voluptuous as vol
from homeassistant import config_entries, exceptions
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
import logging
from .const import (
    DOMAIN,
    CONF_NAME,
    CONF_PRICE_SENSOR,
    CONF_ELOVERBLIK_TOKEN,
    CONF_METERING_POINT
)

_LOGGER = logging.getLogger(__name__)

PRICE_SENSOR_SCHEMA = vol.Schema({
    vol.Required(CONF_PRICE_SENSOR): str,  # cv.entity_id,
})

API_SCHEMA = vol.Schema({
    vol.Required(CONF_ELOVERBLIK_TOKEN): str,  # cv.entity_id,
    vol.Required(CONF_METERING_POINT): str,  # cv.entity_id,
})


async def async_validate_input_entity_id(hass: HomeAssistant, data: dict) -> dict[str, Any]:
    """Validate the user input is valid entity_id.
    Either sensor.* which should be a sensor for electricity price.
    At current, only the Nordpool sensor, or any custom sensor with same format is supported.
    """

    _LOGGER.debug("Validating the price sensor")

    valid_domains = [
        "sensor",
    ]

    if data[CONF_PRICE_SENSOR] is None:
        raise NoInputName
    else:
        entity = cv.entity_id(data[CONF_PRICE_SENSOR])
        entity_split = entity.split(".")
        if entity_split[0] not in valid_domains:
            raise InvalidEntityID

    return {"title": entity}


async def async_validate_api_token(hass: HomeAssistant, data: dict) -> dict[str, Any]:
    """Validate the user input is a string of length 3416."""
    _LOGGER.debug("Validating the API endpoint")

    if data[CONF_ELOVERBLIK_TOKEN] is None:
        raise NoInputName
    else:
        api_token = cv.string(data[CONF_ELOVERBLIK_TOKEN])
        if len(api_token) != 3416:
            raise InvalidAPIToken

    return {"title": api_token}


async def async_validate_metering_point(hass: HomeAssistant, data: dict) -> dict[str, Any]:
    """Validate the user input is a string."""
    _LOGGER.debug("Validating the metering point")

    if data[CONF_METERING_POINT] is None:
        raise NoInputName
    else:
        metering_point = data[CONF_METERING_POINT]
        if len(metering_point) != 18:
            raise InvalidMeteringPoint
        try:
            int(metering_point)
        except ValueError:
            raise InvalidMeteringPoint

    return {"title": metering_point}


@config_entries.HANDLERS.register(DOMAIN)
class FlowHandler(config_entries.ConfigFlow, domain=DOMAIN):

    def __init__(self):
        self.data: dict[str, dict[str, str]] = {}

    async def async_step_user(self, user_input=None):
        errors: dict = {}
        if user_input is not None:
            try:
                info_entity = await async_validate_input_entity_id(self.hass, user_input)
            except InvalidEntityID:
                errors["base"] = "invalid_entity_id"
            # except Exception:  # pylint: disable=broad-except
            #     _LOGGER.exception("Unexpected exception")
            #     errors["base"] = "unknown"

            if not errors:
                self.data[CONF_PRICE_SENSOR] = user_input[CONF_PRICE_SENSOR]

                return await self.async_step_api()

        # If there is no user input or there were errors, show the form again, incl. errors found with the input.
        return self.async_show_form(
            step_id="user", data_schema=PRICE_SENSOR_SCHEMA, errors=errors
        )

    async def async_step_api(self, user_input=None):
        errors: dict = {}
        if user_input is not None:
            try:
                info_api_token = await async_validate_api_token(self.hass, user_input)
            except InvalidEntityID:
                errors["base"] = "invalid_api_token"
            # except Exception:  # pylint: disable=broad-except
            #     _LOGGER.exception("Unexpected exception")
            #     errors["base"] = "unknown"
            try:
                info_metering_point = await async_validate_metering_point(self.hass, user_input)
            except InvalidEntityID:
                errors["base"] = "invalid_meting_point"
            # except Exception:  # pylint: disable=broad-except
            #     _LOGGER.exception("Unexpected exception")
            #     errors["base"] = "unknown"

            if not errors:
                self.data[CONF_ELOVERBLIK_TOKEN] = user_input[CONF_ELOVERBLIK_TOKEN]
                self.data[CONF_METERING_POINT] = user_input[CONF_METERING_POINT]

                return self.async_create_entry(title="Price Sensor", data=self.data)

        return self.async_show_form(
            step_id="api", data_schema=API_SCHEMA, errors=errors
        )


class InvalidEntityID(exceptions.InvalidEntityFormatError):
    """Error to indicate invalid entity_id."""
    def __init__(self, message="Invalid entity_id detected"):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f"{self.__class__.__name__}: {self.message}"


class NoInputName(exceptions.IntegrationError):
    """Error to indicate no input name."""
    def __init__(self, message="No input detected"):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f"{self.__class__.__name__}: {self.message}"


class InvalidAPIToken(exceptions.HomeAssistantError):
    """Error to indicate an invalid API token."""
    def __init__(self, message="Invalid API token provided"):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f"{self.__class__.__name__}: {self.message}"


class InvalidMeteringPoint(exceptions.IntegrationError):
    """Error to indicate an invalid metering point."""
    def __init__(self, message="Invalid metering point provided"):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f"{self.__class__.__name__}: {self.message}"
