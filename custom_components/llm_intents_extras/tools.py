"""LLM tools for Extra Tools for Assist."""

import logging
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import voluptuous as vol
from homeassistant.core import HomeAssistant
from homeassistant.helpers import llm
from homeassistant.util.json import JsonObjectType

_LOGGER = logging.getLogger(__name__)


class DaysBetweenTool(llm.Tool):
    """Count the days between two dates, or from today to a date."""

    name = "days_between"
    description = (
        "Count the days between two dates given as YYYY-MM-DD, such as the start "
        "dates find_event returns. Leave out start_date to count from today. "
        "For days until a single event, find_event's days_from_now already has it."
    )

    parameters = vol.Schema(
        {
            vol.Optional(
                "start_date",
                description="The earlier date, YYYY-MM-DD (e.g. 2026-12-25). "
                "Defaults to today.",
            ): str,
            vol.Required(
                "end_date",
                description="The later date, YYYY-MM-DD (e.g. 2027-01-01).",
            ): str,
        },
    )

    async def async_call(
        self,
        hass: HomeAssistant,
        tool_input: llm.ToolInput,
        llm_context: llm.LLMContext,
    ) -> JsonObjectType:
        """Return the number of days between two dates."""
        today = datetime.now(tz=ZoneInfo(hass.config.time_zone)).date()
        args = tool_input.tool_args

        start = _parse_date(args.get("start_date")) if args.get("start_date") else today
        if start is None:
            return {
                "error": f"Invalid start_date '{args['start_date']}', use YYYY-MM-DD."
            }
        end = _parse_date(args.get("end_date"))
        if end is None:
            return {
                "error": f"Invalid end_date '{args.get('end_date')}', use YYYY-MM-DD."
            }

        days = (end - start).days
        start_text = "today" if start == today else start.strftime("%A, %B %d, %Y")
        end_text = end.strftime("%A, %B %d, %Y")
        if start == today:
            message = (
                f"{end_text} is {days} days from now."
                if days >= 0
                else f"{end_text} was {-days} days ago."
            )
        else:
            message = f"From {start_text} to {end_text} is {days} days."

        return {
            "days": days,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "end_day_of_week": end.strftime("%A"),
            "message": message,
        }


def _parse_date(value: str | None) -> date | None:
    """Parse YYYY-MM-DD (also accepts a full ISO datetime)."""
    if not value:
        return None
    try:
        return date.fromisoformat(str(value).strip()[:10])
    except ValueError:
        return None


class SearchCalendarTool(llm.Tool):
    """Search a calendar for events by name within a date range."""

    name = "find_event"
    description = (
        "Find an event on a calendar by name. "
        "Returns matching events with their exact dates, day of the week, and how many "
        "days from today (days_from_now), so no separate day count is needed."
    )

    parameters = vol.Schema(
        {
            vol.Required(
                "calendar",
                description="The calendar to search, as an entity ID",
            ): str,
            vol.Required(
                "query",
                description="The event name to search for",
            ): str,
            vol.Optional(
                "months_ahead",
                description="How many months ahead to search, defaults to 13",
            ): int,
        },
    )

    async def async_call(
        self,
        hass: HomeAssistant,
        tool_input: llm.ToolInput,
        llm_context: llm.LLMContext,
    ) -> JsonObjectType:
        """Search a calendar for events matching a query string."""
        args = tool_input.tool_args
        calendar_id = args["calendar"]
        query = args["query"].lower()
        months_ahead = args.get("months_ahead", 13)

        tz = ZoneInfo(hass.config.time_zone)
        now = datetime.now(tz=tz)
        today = now.date()
        start = now
        end = now + timedelta(days=months_ahead * 31)

        _LOGGER.debug(
            "SearchCalendar: calendar=%s query=%s range=%s to %s",
            calendar_id,
            query,
            start.isoformat(),
            end.isoformat(),
        )

        try:
            result = await hass.services.async_call(
                "calendar",
                "get_events",
                {
                    "start_date_time": start.isoformat(),
                    "end_date_time": end.isoformat(),
                },
                target={"entity_id": calendar_id},
                blocking=True,
                return_response=True,
            )
        except Exception as e:
            _LOGGER.error("SearchCalendar service call failed: %s", e)
            return {"error": f"Failed to query calendar: {e}"}

        events = result.get(calendar_id, {}).get("events", [])

        matches = []
        for event in events:
            summary = event.get("summary", "")
            if query in summary.lower():
                start_str = event.get("start")
                end_str = event.get("end")
                match = {
                    "summary": summary,
                    "start": start_str,
                    "end": end_str,
                }
                start_date = _event_date(start_str, tz)
                if start_date is not None:
                    match["day_of_week"] = start_date.strftime("%A")
                    match["days_from_now"] = (start_date - today).days
                matches.append(match)

        if not matches:
            return {
                "found": False,
                "message": f"No events matching '{args['query']}' found in the next {months_ahead} months.",
                "events": [],
            }

        first = matches[0]
        if "days_from_now" in first:
            when = _event_date(first["start"], tz)
            days = first["days_from_now"]
            relative = (
                "today"
                if days == 0
                else ("tomorrow" if days == 1 else f"{days} days from now")
            )
            message = (
                f"{first['summary']} is {when.strftime('%A, %B %d, %Y')}, {relative}."
            )
            if len(matches) > 1:
                message += f" ({len(matches)} matching events in total.)"
        else:
            message = f"Found {len(matches)} event(s) matching '{args['query']}'."

        return {
            "found": True,
            "count": len(matches),
            "events": matches,
            "message": message,
        }


def _event_date(value: str | None, tz: ZoneInfo) -> date | None:
    """Return the local calendar date an event starts on (all-day or timed)."""
    if not value:
        return None
    try:
        if "T" not in value:
            return date.fromisoformat(value[:10])
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.date()
    return parsed.astimezone(tz).date()
