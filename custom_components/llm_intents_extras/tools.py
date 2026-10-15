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
    """Calculate the number of days between two dates, or from today to a date."""

    name = "days_between"
    description = (
        "Calculate the number of days between two dates. "
        "If only one date is given, calculates from today. "
        "Use this after you have looked up the exact date of an event."
    )

    parameters = vol.Schema(
        {
            vol.Required(
                "month",
                description="The target month (1-12).",
            ): int,
            vol.Required(
                "day",
                description="The target day of the month (1-31).",
            ): int,
            vol.Optional(
                "year",
                description="The target year. Defaults to the current year, "
                "or next year if the date has already passed.",
            ): int,
            vol.Optional(
                "from_month",
                description="The starting month (1-12). Defaults to today.",
            ): int,
            vol.Optional(
                "from_day",
                description="The starting day of the month (1-31). Defaults to today.",
            ): int,
            vol.Optional(
                "from_year",
                description="The starting year. Defaults to the current year.",
            ): int,
        },
    )

    async def async_call(
        self,
        hass: HomeAssistant,
        tool_input: llm.ToolInput,
        llm_context: llm.LLMContext,
    ) -> JsonObjectType:
        """Return the number of days between two dates."""
        now = datetime.now(tz=ZoneInfo(hass.config.time_zone))
        today = now.date()

        args = tool_input.tool_args
        target_year = args.get("year")
        target_month = args["month"]
        target_day = args["day"]

        from_year = args.get("from_year", today.year)
        from_month = args.get("from_month", today.month)
        from_day = args.get("from_day", today.day)

        try:
            from_date = date(from_year, from_month, from_day)
        except ValueError as e:
            return {"error": f"Invalid start date: {e}"}

        if target_year is None:
            try:
                target = date(today.year, target_month, target_day)
            except ValueError as e:
                return {"error": f"Invalid target date: {e}"}
            if target < from_date:
                target = date(today.year + 1, target_month, target_day)
        else:
            try:
                target = date(target_year, target_month, target_day)
            except ValueError as e:
                return {"error": f"Invalid target date: {e}"}

        delta = (target - from_date).days
        direction = "from now" if from_date == today else f"from {from_date.strftime('%B %d, %Y')}"

        return {
            "days": delta,
            "from_date": from_date.strftime("%B %d, %Y"),
            "target_date": target.strftime("%B %d, %Y"),
            "target_day_of_week": target.strftime("%A"),
            "message": (
                f"{target.strftime('%A, %B %d, %Y')} is {abs(delta)} days {direction}"
                if delta >= 0
                else f"{target.strftime('%A, %B %d, %Y')} was {abs(delta)} days ago"
            ),
        }


class SearchCalendarTool(llm.Tool):
    """Search a calendar for events by name within a date range."""

    name = "find_event"
    description = (
        "Find an event on a calendar by name. "
        "Returns matching events with their exact dates."
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
                description="How many months ahead to search, defaults to 6",
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
        months_ahead = args.get("months_ahead", 6)

        tz = ZoneInfo(hass.config.time_zone)
        now = datetime.now(tz=tz)
        start = now
        end = now + timedelta(days=months_ahead * 31)

        _LOGGER.debug(
            "SearchCalendar: calendar=%s query=%s range=%s to %s",
            calendar_id, query, start.isoformat(), end.isoformat(),
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
                matches.append({
                    "summary": summary,
                    "start": start_str,
                    "end": end_str,
                })

        if not matches:
            return {
                "found": False,
                "message": f"No events matching '{args['query']}' found in the next {months_ahead} months.",
                "events": [],
            }

        return {
            "found": True,
            "count": len(matches),
            "events": matches,
            "message": f"Found {len(matches)} event(s) matching '{args['query']}'.",
        }
