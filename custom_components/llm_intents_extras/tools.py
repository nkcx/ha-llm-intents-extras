"""LLM tools for Extra Tools for Assist."""

from datetime import date, datetime
from zoneinfo import ZoneInfo

import voluptuous as vol
from homeassistant.core import HomeAssistant
from homeassistant.helpers import llm
from homeassistant.util.json import JsonObjectType


class DaysBetweenTool(llm.Tool):
    """Calculate the number of days between two dates, or from today to a date."""

    name = "days_between"
    description = (
        "Calculate the number of days between two dates. "
        "If only one date is given, calculates from today. "
        "Use this for questions like 'how many days until Thanksgiving' "
        "or 'how many days between two events'."
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

        # Build the "from" date (default: today)
        from_year = args.get("from_year", today.year)
        from_month = args.get("from_month", today.month)
        from_day = args.get("from_day", today.day)

        try:
            from_date = date(from_year, from_month, from_day)
        except ValueError as e:
            return {"error": f"Invalid start date: {e}"}

        # If no target year given, pick the current year — or next year
        # if the date has already passed.
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
