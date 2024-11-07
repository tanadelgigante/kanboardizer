"""Calendar platform for Kanboard integration."""

from .const import DOMAIN, CALENDAR_NAME
from argparse import OPTIONAL
from datetime import datetime, timedelta
from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import BaseCoordinatorEntity
from typing import List


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Kanboard calendar."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([KanboardCalendar(coordinator)], True)


class KanboardCalendar(BaseCoordinatorEntity, CalendarEntity):
    """Kanboard Calendar class."""

    def __init__(self, coordinator):
        """Initialize the calendar."""
        super().__init__(coordinator)
        self._attr_name = CALENDAR_NAME
        self._attr_unique_id = f"{DOMAIN}_calendar"

    @property
    def event(self) -> OPTIONAL[CalendarEvent]:
        """Return the next upcoming event."""
        events = self._get_events(
            datetime.now(),
            datetime.now() + timedelta(days=7)
        )
        return events[0] if events else None

    async def async_get_events(
        self,
        hass: HomeAssistant,
        start_date: datetime,
        end_date: datetime
    ) -> List[CalendarEvent]:
        """Get all events in a specific time frame."""
        return self._get_events(start_date, end_date)

    def _get_events(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[CalendarEvent]:
        """Get all events in a specific time frame."""
        events = []
        tasks = self.coordinator.data.get("tasks", [])
        
        for task in tasks:
            if task["date_due"]:
                due_date = datetime.fromtimestamp(task["date_due"])
                
                if start_date <= due_date <= end_date:
                    event = CalendarEvent(
                        summary=f"Task Due: {task['title']}",
                        start=due_date,
                        end=due_date + timedelta(hours=1),
                        description=task.get("description", ""),
                        location=None,
                    )
                    events.append(event)
        
        return sorted(events, key=lambda x: x.start)
