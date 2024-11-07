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
    """Sensor for the total number of tasks."""
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
            # Step 1: Get all project IDs
            response = requests.post(
                self.api_url,
                auth=('jsonrpc', self.api_token),
                json={
                    "jsonrpc": "2.0",
                    "method": "getAllProjects",
                    "id": 1
                }
            )
            projects = response.json().get("result")
            if projects is None:
                _LOGGER.error(f"Unexpected API response format when fetching projects: {response.json()}")
                return
            
            total_tasks = 0
            active_tasks = 0
            stalled_tasks = 0

            # Step 2: Get all tasks for each project
            for project in projects:
                project_id = project["id"]
                
                # Get active tasks
                response = requests.post(
                    self.api_url,
                    auth=('jsonrpc', self.api_token),
                    json={
                        "jsonrpc": "2.0",
                        "method": "getAllTasks",
                        "id": project_id,
                        "params": {
                            "project_id": project_id,
                            "status_id": 1
                        }
                    }
                )
                active_tasks_data = response.json().get("result", [])
                active_tasks += len(active_tasks_data)

                # Get inactive tasks
                response = requests.post(
                    self.api_url,
                    auth=('jsonrpc', self.api_token),
                    json={
                        "jsonrpc": "2.0",
                        "method": "getAllTasks",
                        "id": project_id,
                        "params": {
                            "project_id": project_id,
                            "status_id": 0
                        }
                    }
                )
                stalled_tasks_data = response.json().get("result", [])
                stalled_tasks += len(stalled_tasks_data)

                total_tasks += len(active_tasks_data) + len(stalled_tasks_data)

            self._state = total_tasks
            self._attributes = {
                "total_tasks": total_tasks,
                "active_tasks": active_tasks,
                "stalled_tasks": stalled_tasks
            }
            
            _LOGGER.debug(f"Total tasks: {total_tasks}, Active tasks: {active_tasks}, Stalled tasks: {stalled_tasks}")
        except Exception as e:
            _LOGGER.error(f"Error fetching task data: {e}")


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
            _LOGGER.debug("Fetching overdue tasks...")
            response = requests.post(
                self.api_url,
                auth=('jsonrpc', self.api_token),
                json={
                    "jsonrpc": "2.0",
                    "method": "getOverdueTasks",
                    "id": 1
                },
            )
            data = response.json().get("result")
            if data is None:
                _LOGGER.error(f"Unexpected API response format: {response.json()}")
                return
            
            self._state = len(data)
            self._attributes = {"overdue_tasks": data}
            
            current_time = datetime.now()
            for task in data:
                task_due_date = datetime.fromtimestamp(int(task["date_due"]))
                if task_due_date < current_time:
                    _LOGGER.debug(f"Task overdue: {task}")
                    self.hass.bus.fire("kanboard_task_overdue", {
                        "task_id": task["id"],
                        "title": task["title"],
                        "due_date": task_due_date.isoformat(),
                        "project_id": task["project_id"],
                        "project_name": task["project_name"],
                        "assignee_username": task["assignee_username"],
                        "assignee_name": task["assignee_name"]
                    })
        except Exception as e:
            _LOGGER.error(f"Error fetching overdue tasks: {e}")

