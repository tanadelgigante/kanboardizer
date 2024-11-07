from datetime import timedelta, datetime
import requests
import logging
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle

MIN_TIME_BETWEEN_UPDATES = timedelta(minutes=10)

_LOGGER = logging.getLogger(__name__)

class KanboardCalendarSensor(Entity):
    """Sensor for Kanboard task deadlines."""
    def __init__(self, api_url, api_token, hass):
        """Initialize the calendar sensor."""
        self.api_url = api_url
        self.api_token = api_token
        self.hass = hass
        self._state = None
        self._attributes = {}
        self._name = "Kanboard Task Calendar"

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return self._attributes

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        """Fetch new state data for the sensor."""
        try:
            _LOGGER.debug("Fetching task deadlines...")
            response = requests.post(
                self.api_url,
                json={
                    "jsonrpc": "2.0",
                    "method": "getAllTasks",
                    "id": 1,
                    "params": {"token": self.api_token},
                },
            )
            data = response.json()["result"]
            deadlines = [task for task in data if task["date_due"]]
            _LOGGER.debug(f"Task deadlines: {deadlines}")
            self._state = len(deadlines)
            self._attributes = {"deadlines": deadlines}
            
            # Current time
            current_time = datetime.now()
            for task in deadlines:
                task_due_date = datetime.fromtimestamp(task["date_due"])
                days_until_due = (task_due_date - current_time).days
                if days_until_due <= 2 and task_due_date > current_time:
                    _LOGGER.debug(f"Task due soon: {task}")
                    self.hass.bus.fire("kanboard_task_due_soon", {
                        "task_id": task["id"],
                        "title": task["title"],
                        "due_date": task_due_date.isoformat(),
                        "days_until_due": days_until_due
                    })
                elif task_due_date < current_time:
                    _LOGGER.debug(f"Task overdue: {task}")
                    self.hass.bus.fire("kanboard_task_overdue", {
                        "task_id": task["id"],
                        "title": task["title"],
                        "due_date": task_due_date.isoformat()
                    })
        except Exception as e:
            _LOGGER.error(f"Error fetching task deadlines: {e}")
