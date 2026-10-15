# Extra Tools for Assist

A companion integration to [Tools for Assist (llm_intents)](https://github.com/skye-harris/llm_intents) that provides additional LLM tools for Home Assistant conversation agents.

## Tools

### `days_between`

Calculate the number of days between two dates, or from today to a future date.

**Examples:**
- "How many days until Thanksgiving?" — looks up the date, then calls `days_between` to get the count
- "How many days between Christmas and New Year's?" — calculates the delta between two dates
- "How long until July 4th?" — days from today to the target date

**Parameters:**
| Parameter | Required | Description |
|-----------|----------|-------------|
| `month` | Yes | Target month (1-12) |
| `day` | Yes | Target day (1-31) |
| `year` | No | Target year (defaults to current/next year) |
| `from_month` | No | Start month (defaults to today) |
| `from_day` | No | Start day (defaults to today) |
| `from_year` | No | Start year (defaults to current year) |

**Response:**
```json
{
  "days": 45,
  "from_date": "October 12, 2026",
  "target_date": "November 26, 2026",
  "target_day_of_week": "Thursday",
  "message": "Thursday, November 26, 2026 is 45 days from now"
}
```

## Installation

### HACS (Custom Repository)

[![Open your Home Assistant instance and open this repository in HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=nkcx&repository=ha-llm-intents-extras&category=integration)

Or by hand:

1. Open HACS in Home Assistant
2. Click the three-dot menu → Custom repositories
3. Add `https://github.com/nkcx/ha-llm-intents-extras` as an Integration
4. Install "Extra Tools for Assist"
5. Restart Home Assistant
6. Go to Settings → Devices & Services → Add Integration → "Extra Tools for Assist", or use this button:

   [![Open your Home Assistant instance and start setting up Extra Tools for Assist.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=llm_intents_extras)

### Manual

Copy `custom_components/llm_intents_extras/` to your Home Assistant `config/custom_components/` directory.

## Configuration

After adding the integration, enable it as an Agent API in your conversation agent's configuration (e.g., in the Local OpenAI LLM integration settings).

The API will appear as **"Extra Utilities"** in the list of available LLM APIs.

## License

MIT
