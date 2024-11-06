"""Sensor for Kanboard."""

from datetime import timedelta
import requests
import logging
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle
from _datetime import time

MIN_TIME_BETWEEN_UPDATES = timedelta(minutes=10)

_LOGGER = logging.getLogger(__name__)

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Kanboardizer sensor."""
    api_url = hass.data["kanboardizer"]["api_url"]
    api_token = hass.data["kanboardizer"]["api_token"]
    """user = hass.data["kanboardizer"]["user"]"""
    _LOGGER.info("Initializing sensors...")

    sensors = [
        KanboardizerUserCountSensor(api_url, api_token, hass),
        KanboardizerProjectCountSensor(api_url, api_token, hass),
        KanboardizerTaskCountSensor(api_url, api_token, hass),
        KanboardizerDeadlineSensor(api_url, api_token, hass)
    ]
        
    add_entities(sensors, True)
    _LOGGER.info("Initialized all sensors")

class KanboardizerSensor(Entity):
    """Representation of a base Kanboardizer sensor."""
    def __init__(self, api_url, api_token, hass):
        """Initialize the sensor."""
        self.api_url = api_url
        self.api_token = api_token
        self.hass = hass
        self._state = None
        self._attributes = {}
        
    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return self._attributes

class KanboardizerUserCountSensor(KanboardizerSensor):
    """Sensor for the number of users."""
    def __init__(self, api_url, api_token, hass):
        """Initialize the user count sensor."""
        super().__init__(api_url, api_token, hass)
        _LOGGER.info("Initialized User Count Sensor")

    @property
    def name(self):
        """Return the name of the sensor."""
        return "Kanboard User Count"

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        """Fetch new state data for the sensor."""
        try:
            _LOGGER.info("Updating User Count Sensor")            
            response = requests.post(
                self.api_url,
                json={
                    "jsonrpc": "2.0",
                    "method": "getAllUsers",
                    "id": 1,
                    "params": {"token": self.api_token},
                },
            )
            data = response.json()["result"]
            _LOGGER.debug(f"Response: {data}")
            self._state = len(data)
            _LOGGER.info("Updated User Count Sensor")
        except Exception as e:
            _LOGGER.error(f"Error fetching user data: {e}")

class KanboardizerProjectCountSensor(KanboardizerSensor):
    """Sensor for the number of projects."""
    def __init__(self, api_url, api_token, hass):
        """Initialize the project count sensor."""
        super().__init__(api_url, api_token, hass)
        _LOGGER.info("Initialized Project Count Sensor")

    @property
    def name(self):
        """Return the name of the sensor."""
        return "Kanboard Project Count"

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        """Fetch new state data for the sensor."""
        try:
            _LOGGER.info("Updating Project Count Sensor")
            response = requests.post(
                self.api_url,
                json={
                    "jsonrpc": "2.0",
                    "method": "getAllProjects",
                    "id": 1,
                    "params": {"token": self.api_token},
                },
            )
            data = response.json()["result"]
            self._state = len(data)
            self._attributes = {"total_projects": len(data)}
            self._attributes["open_projects"] = len([project for project in data if project["is_active"] == 1])
            _LOGGER.info("Updated Project Count Sensor")
        except Exception as e:
            _LOGGER.error(f"Error fetching project data: {e}")

class KanboardizerTaskCountSensor(KanboardizerSensor):
    """Sensor for the number of tasks."""
    def __init__(self, api_url, api_token, hass):
        """Initialize the task count sensor."""
        super().__init__(api_url, api_token, hass)
        _LOGGER.info("Initialized Task Count Sensor")

    @property
    def name(self):
        """Return the name of the sensor."""
        return "Kanboardizer Task Count"

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        """Fetch new state data for the sensor."""
        try:
            _LOGGER.info("Updating Task Count Sensor")
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
            self._state = len(data)
            _LOGGER.info("Updated Task Count Sensor")
        except Exception as e:
            _LOGGER.error(f"Error fetching task data: {e}")

class KanboardizerDeadlineSensor(KanboardizerSensor):
    """Sensor for task deadlines."""
    def __init__(self, api_url, api_token, hass):
        """Initialize the deadline sensor."""
        super().__init__(api_url, api_token, hass)
        _LOGGER.info("Initialized Deadline Sensor")

    @property
    def name(self):
        """Return the name of the sensor."""
        return "Kanboardizer Task Deadlines"

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        """Fetch new state data for the sensor."""
        try:
            _LOGGER.info("Updating Deadline Sensor")
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
            self._state = len(deadlines)
            self._attributes = {"deadlines": deadlines}
            _LOGGER.info("Updated Deadline Sensor")
            
            # Genera eventi di allarme per i task scaduti
            current_time = int(time.time())
            for task in deadlines:
                if task["date_due"] < current_time:
                    self.hass.bus.fire("kanboardizer_task_due", {
                        "task_id": task["id"],
                        "title": task["title"],
                        "due_date": task["date_due"]
                    })
            _LOGGER.info("Sent Deadline Overdue Events")
        except Exception as e:
            _LOGGER.error(f"Error fetching deadline data: {e}")
