"""Helper Manager integration — provides services to create HA helper entities."""
from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.util import slugify

DOMAIN = "helper_manager"
_LOGGER = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Service schemas — mirrors the CREATE_FIELDS defined in each input_* domain
# ---------------------------------------------------------------------------

CREATE_INPUT_TEXT_SCHEMA = vol.Schema(
    {
        vol.Required("name"): vol.All(str, vol.Length(min=1)),
        vol.Optional("initial"): cv.string,
        vol.Optional("min", default=0): vol.All(int, vol.Range(min=0)),
        vol.Optional("max", default=100): vol.All(int, vol.Range(min=1)),
        vol.Optional("pattern"): cv.string,
        vol.Optional("mode", default="text"): vol.In(["text", "password"]),
        vol.Optional("icon"): cv.icon,
    }
)

CREATE_INPUT_BOOLEAN_SCHEMA = vol.Schema(
    {
        vol.Required("name"): vol.All(str, vol.Length(min=1)),
        vol.Optional("initial"): cv.boolean,
        vol.Optional("icon"): cv.icon,
    }
)

CREATE_INPUT_NUMBER_SCHEMA = vol.Schema(
    {
        vol.Required("name"): vol.All(str, vol.Length(min=1)),
        vol.Required("min"): vol.Coerce(float),
        vol.Required("max"): vol.Coerce(float),
        vol.Optional("initial"): vol.Coerce(float),
        vol.Optional("step", default=1.0): vol.All(
            vol.Coerce(float), vol.Range(min=1e-3)
        ),
        vol.Optional("mode", default="slider"): vol.In(["box", "slider"]),
        vol.Optional("unit_of_measurement"): cv.string,
        vol.Optional("icon"): cv.icon,
    }
)

CREATE_INPUT_SELECT_SCHEMA = vol.Schema(
    {
        vol.Required("name"): vol.All(str, vol.Length(min=1)),
        vol.Required("options"): vol.All(cv.ensure_list, [cv.string]),
        vol.Optional("initial"): cv.string,
        vol.Optional("icon"): cv.icon,
    }
)

CREATE_INPUT_DATETIME_SCHEMA = vol.Schema(
    {
        vol.Required("name"): vol.All(str, vol.Length(min=1)),
        vol.Optional("has_date", default=True): cv.boolean,
        vol.Optional("has_time", default=True): cv.boolean,
        vol.Optional("initial"): cv.string,
        vol.Optional("icon"): cv.icon,
    }
)

CONFIG_SCHEMA = cv.empty_config_schema(DOMAIN)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Helper Manager from a config entry."""

    def _entity_exists(domain: str, name: str) -> bool:
        """Return True if a helper with the given name is already loaded."""
        entity_id = f"{domain}.{slugify(name)}"
        return hass.states.get(entity_id) is not None

    def _get_ws_storage_collection(domain: str):
        """Locate the StorageCollection via the websocket create handler.

        DictStorageCollectionWebsocket registers a '{domain}/create' WS
        command whose handler chain is:
          require_admin(@wraps) → async_response(@wraps) → bound ws_create_item
        Both decorators use @wraps so __wrapped__ lets us peel them off and
        reach the bound method, giving us the storage_collection attribute.
        """
        ws_handlers = hass.data.get("websocket_api", {})
        entry = ws_handlers.get(f"{domain}/create")
        if entry is None:
            return None
        func = entry[0]
        while hasattr(func, "__wrapped__"):
            func = func.__wrapped__
        return getattr(getattr(func, "__self__", None), "storage_collection", None)

    async def _create_helper(domain: str, data: dict) -> None:
        """Create a helper entity using whichever mechanism is available.

        1. Use the native HA service if the domain registered one.
        2. Fall back to calling async_create_item on the storage collection
           obtained by introspecting the websocket handler chain.
        """
        if hass.services.has_service(domain, "create"):
            await hass.services.async_call(domain, "create", data, blocking=True)
            return

        storage_collection = _get_ws_storage_collection(domain)
        if storage_collection is None:
            raise HomeAssistantError(
                f"{domain} does not support programmatic helper creation — "
                "component may not be loaded"
            )
        await storage_collection.async_create_item(data)

    # ------------------------------------------------------------------
    # Service handlers
    # ------------------------------------------------------------------

    async def handle_create_input_text(call: ServiceCall) -> None:
        """Create an input_text helper if it does not already exist."""
        name = call.data["name"]
        if _entity_exists("input_text", name):
            _LOGGER.debug("input_text.%s already exists — skipping", slugify(name))
            return
        await _create_helper("input_text", dict(call.data))
        _LOGGER.info("Created input_text helper: %s", name)

    async def handle_create_input_boolean(call: ServiceCall) -> None:
        """Create an input_boolean helper if it does not already exist."""
        name = call.data["name"]
        if _entity_exists("input_boolean", name):
            _LOGGER.debug(
                "input_boolean.%s already exists — skipping", slugify(name)
            )
            return
        await _create_helper("input_boolean", dict(call.data))
        _LOGGER.info("Created input_boolean helper: %s", name)

    async def handle_create_input_number(call: ServiceCall) -> None:
        """Create an input_number helper if it does not already exist."""
        name = call.data["name"]
        if _entity_exists("input_number", name):
            _LOGGER.debug(
                "input_number.%s already exists — skipping", slugify(name)
            )
            return
        await _create_helper("input_number", dict(call.data))
        _LOGGER.info("Created input_number helper: %s", name)

    async def handle_create_input_select(call: ServiceCall) -> None:
        """Create an input_select helper if it does not already exist."""
        name = call.data["name"]
        if _entity_exists("input_select", name):
            _LOGGER.debug(
                "input_select.%s already exists — skipping", slugify(name)
            )
            return
        await _create_helper("input_select", dict(call.data))
        _LOGGER.info("Created input_select helper: %s", name)

    async def handle_create_input_datetime(call: ServiceCall) -> None:
        """Create an input_datetime helper if it does not already exist."""
        name = call.data["name"]
        if _entity_exists("input_datetime", name):
            _LOGGER.debug(
                "input_datetime.%s already exists — skipping", slugify(name)
            )
            return
        await _create_helper("input_datetime", dict(call.data))
        _LOGGER.info("Created input_datetime helper: %s", name)

    # ------------------------------------------------------------------
    # Register services
    # ------------------------------------------------------------------

    hass.services.async_register(
        DOMAIN,
        "create_input_text",
        handle_create_input_text,
        schema=CREATE_INPUT_TEXT_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        "create_input_boolean",
        handle_create_input_boolean,
        schema=CREATE_INPUT_BOOLEAN_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        "create_input_number",
        handle_create_input_number,
        schema=CREATE_INPUT_NUMBER_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        "create_input_select",
        handle_create_input_select,
        schema=CREATE_INPUT_SELECT_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        "create_input_datetime",
        handle_create_input_datetime,
        schema=CREATE_INPUT_DATETIME_SCHEMA,
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry and remove registered services."""
    for service in (
        "create_input_text",
        "create_input_boolean",
        "create_input_number",
        "create_input_select",
        "create_input_datetime",
    ):
        hass.services.async_remove(DOMAIN, service)
    return True
