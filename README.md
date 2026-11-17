# Extra Tools for Assist

A companion integration to [Tools for Assist (llm_intents)](https://github.com/skye-harris/llm_intents) that provides additional LLM tools for Home Assistant conversation agents.

## Tools

### `days_between`

Count the days between two dates, given as `YYYY-MM-DD` (the same form `find_event` returns), or from today to a date.

**Examples:**
- "How many days between Christmas and New Year's?" — two `find_event` calls, then `days_between(start_date="2026-12-25", end_date="2027-01-01")` → 7
- "How many days ago was the 4th of July?" — `days_between(end_date="2026-07-04")` → negative, "was … days ago"
- "How many days until Thanksgiving?" — use `find_event` alone; its result already has `days_from_now`

**Parameters:**
| Parameter | Required | Description |
|-----------|----------|-------------|
| `start_date` | No | Earlier date, `YYYY-MM-DD` (defaults to today) |
| `end_date` | Yes | Later date, `YYYY-MM-DD` |

**Response:**
```json
{
  "days": 7,
  "start_date": "2026-12-25",
  "end_date": "2027-01-01",
  "end_day_of_week": "Friday",
  "message": "From Friday, December 25, 2026 to Friday, January 01, 2027 is 7 days."
}
```

Changed in 0.3.0: `month`/`day`/`year` and `from_month`/`from_day`/`from_year` were replaced by `start_date`/`end_date`. Small local models reliably dropped the `from_*` arguments and counted from today instead.

### `find_event`

Find an event on a calendar by name (holidays, birthdays, sports schedules, household events). Each match comes back with its date, day of the week and `days_from_now`, so "how many days until …" is answered with one tool call.

**Examples:**
- "When is Thanksgiving?" / "How many days until Thanksgiving?" — `find_event(calendar="calendar.holidays_in_united_states", query="Thanksgiving")`
- "When do the Ducks play Ohio State?" — `find_event(calendar="calendar.oregon_ducks_football", query="Ohio State")`

**Parameters:**
| Parameter | Required | Description |
|-----------|----------|-------------|
| `calendar` | Yes | Calendar entity ID to search |
| `query` | Yes | Text to match in the event name (case-insensitive) |
| `months_ahead` | No | How far ahead to search (default 13, so events up to a year out are found) |

**Response:**
```json
{
  "found": true,
  "count": 1,
  "events": [
    {"summary": "Thanksgiving Day", "start": "2026-11-26", "end": "2026-11-27", "day_of_week": "Thursday", "days_from_now": 11}
  ],
  "message": "Thanksgiving Day is Thursday, November 26, 2026, 11 days from now."
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
