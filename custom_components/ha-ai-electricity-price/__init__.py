from .const import DOMAIN

async def async_setup(hass, config):
    # Your setup code here
    return True

async def async_setup_entry(hass, config_entry):
    # Your setup code here
    hass.data[DOMAIN] = {"entity_id": config_entry.data["entity_id"], 
                         "url": config_entry.data["url"], 
                         "api_token": config_entry.data["api_token"],
                         "fees": {"current_tax": 1, "current_electricity_fee": 50, "current_transport_fees": 20, "nettarif_c_time": []}}
    return True
