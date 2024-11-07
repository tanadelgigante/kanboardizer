from datetime import timedelta
import requests
import logging
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle
from _datetime import datetime

MIN_TIME_BETWEEN_UPDATES = timedelta(minutes=10)

_LOGGER = logging.getLogger(__name__)

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Kanboard sensor."""
    api_url = hass.data["kanboardizer"]["api_url"]
    api_token = hass.data["kanboardizer"]["api_token"]

    sensors = [
        KanboardUserCountSensor(api_url, api_token, hass),
        KanboardProjectCountSensor(api_url, api_token, hass),
        KanboardTaskCountSensor(api_url, api_token, hass),
        KanboardProjectTaskCountSensor(api_url, api_token, hass), 
        KanboardCalendarSensor(api_url, api_token, hass)
    ]
    
    add_entities(sensors, True)

class KanboardSensor(Entity):
    """Representation of a base Kanboard sensor."""
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

class KanboardUserCountSensor(KanboardSensor):
    """Sensor for the number of users."""
    def __init__(self, api_url, api_token, hass):
        """Initialize the user count sensor."""
        super().__init__(api_url, api_token, hass)

    @property
    def name(self):
        """Return the name of the sensor."""
        return "Kanboard User Count"

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        """Fetch new state data for the sensor."""
        try:
            response = requests.post(
                self.api_url,
                auth=('jsonrpc', self.api_token),
                json={
                    "jsonrpc": "2.0",
                    "method": "getAllUsers",
                    "id": 1
                },
            )
            _LOGGER.debug(f"API Response: {response.json()}")
            data = response.json().get("result")
            if data is None:
                _LOGGER.error(f"Unexpected API response format: {response.json()}")
                return
            self._state = len(data)
        except Exception as e:
            _LOGGER.error(f"Error fetching user data: {e}")

class KanboardProjectCountSensor(KanboardSensor):
    """Sensor for the number of projects."""
    def __init__(self, api_url, api_token, hass):
        """Initialize the project count sensor."""
        super().__init__(api_url, api_token, hass)

    @property
    def name(self):
        """Return the name of the sensor."""
        return "Kanboard Project Count"

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        """Fetch new state data for the sensor."""
        try:
            response = requests.post(
                self.api_url,
                auth=('jsonrpc', self.api_token),
                json={
                    "jsonrpc": "2.0",
                    "method": "getAllProjects",
                    "id": 1
                },
            )
            data = response.json()["result"]
            self._state = len(data)
            self._attributes = {"total_projects": len(data)}
            self._attributes["open_projects"] = len([project for project in data if project["is_active"] == 1])
            self._attributes["closed_projects"] = len([project for project in data if project["is_active"] == 0])
        except Exception as e:
            _LOGGER.error(f"Error fetching project data: {e}")

class KanboardTaskCountSensor(KanboardSensor):
    """Sensor for the number of tasks."""
    def __init__(self, api_url, api_token, hass):
        """Initialize the task count sensor."""
        super().__init__(api_url, api_token, hass)

    @property
    def name(self):
        """Return the name of the sensor."""
        return "Kanboard Task Count"

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        """Fetch new state data for the sensor."""
        try:
            response = requests.post(
                self.api_url,
                auth=('jsonrpc', self.api_token),
                json={
                    "jsonrpc": "2.0",
                    "method": "getAllTasks",
                    "id": 1
                },
            )
            data = response.json()["result"]
            self._state = len(data)
            self._attributes = {"total_tasks": len(data)}
            self._attributes["in_progress_tasks"] = len([task for task in data if task["is_active"] == 1])
            self._attributes["stalled_tasks"] = len([task for task in data if task["is_active"] == 0])
        except Exception as e:
            _LOGGER.error(f"Error fetching task data: {e}")

class KanboardProjectTaskCountSensor(KanboardSensor):
    """Sensor for the number of tasks per project."""
    def __init__(self, api_url, api_token, hass):
        """Initialize the task per project count sensor."""
        super().__init__(api_url, api_token, hass)

    @property
    def name(self):
        """Return the name of the sensor."""
        return "Kanboard Task Count per Project"

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        """Fetch new state data for the sensor."""
        try:
            response = requests.post(
                self.api_url,
                auth=('jsonrpc', self.api_token),
                json={
                    "jsonrpc": "2.0",
                    "method": "getAllTasks",
                    "id": 1
                },
            )
            data = response.json()["result"]
            projects = {}
            for task in data:
                project_id = task["project_id"]
                if project_id not in projects:
                    projects[project_id] = {"total": 0, "in_progress": 0, "stalled": 0}
                projects[project_id]["total"] += 1
                if task["is_active"] == 1:
                    projects[project_id]["in_progress"] += 1
                else:
                    projects[project_id]["stalled"] += 1
            self._state = len(projects)
            self._attributes = projects
        except Exception as e:
            _LOGGER.error(f"Error fetching tasks per project data: {e}")
            
class KanboardCalendarSensor(KanboardSensor):
    """Sensor for Kanboard task deadlines."""
    def __init__(self, api_url, api_token, hass):
        """Initialize the calendar sensor."""
        super().__init__(api_url, api_token, hass)
        self._name = "Kanboard Task Calendar"

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        """Fetch new state data for the sensor."""
        try:
            _LOGGER.debug("Fetching task deadlines...")
            response = requests.post(
                self.api_url,
                auth=('jsonrpc', self.api_token),
                json={
                    "jsonrpc": "2.0",
                    "method": "getAllTasks",
                    "id": 1
                },
            )
            data = response.json()["result"]
            deadlines = [task for task in data if task.get("date_due")]
            _LOGGER.debug(f"Task deadlines: {deadlines}")
            self._state = len(deadlines)
            self._attributes = {"deadlines": deadlines}
            
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

