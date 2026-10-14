"""Extra Tools for Assist — companion LLM tools for home-assistant-llm-intents."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import llm
from homeassistant.util.json import JsonObjectType

from .const import CONF_DATE_TOOLS_ENABLED, DOMAIN
from .tools import DaysBetweenTool, SearchCalendarTool

_LOGGER = logging.getLogger(__name__)

TOOLS = [
    (CONF_DATE_TOOLS_ENABLED, DaysBetweenTool),
    (CONF_DATE_TOOLS_ENABLED, SearchCalendarTool),
]


class ExtrasAPI(llm.API):
    """LLM API providing extra utility tools for Assist."""

    TOOLS_CONF_MAP: list = []

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the API."""
        super().__init__(
            hass=hass,
            id="extra_utilities",
            name="Extra Utilities",
        )
        self.entry = entry
        self._tools: list[llm.Tool] = []

        data = {**entry.data, **entry.options}
        for conf_key, tool_class in TOOLS:
            if data.get(conf_key, True):
                self._tools.append(tool_class())

    async def async_get_api_instance(
        self,
        llm_context: llm.LLMContext,
    ) -> llm.APIInstance:
        """Return an API instance with the enabled tools."""
        return llm.APIInstance(
            api=self,
            api_prompt="",
            llm_context=llm_context,
            tools=self._tools,
        )


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the integration (YAML, unused)."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up from a config entry."""
    api = ExtrasAPI(hass, entry)

    if not api._tools:
        _LOGGER.warning("No tools enabled — nothing to register")
        return True

    unregister = llm.async_register_api(hass, api)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = unregister

    _LOGGER.info(
        "Registered %d extra LLM tool(s): %s",
        len(api._tools),
        ", ".join(t.name for t in api._tools),
    )
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unregister = hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    if unregister:
        unregister()
    return True
