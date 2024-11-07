"""Platform for Kanboard sensor integration."""
from datetime import datetime, timedelta
import logging

from kanboard import Client

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, BaseCoordinatorEntity

from .const import DOMAIN, DEFAULT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Kanboard sensor."""
    client = Client(
        url=config_entry.data["url"],
        token=config_entry.data["api_token"]
    )

    coordinator = KanboardDataUpdateCoordinator(hass, client)
    await coordinator.async_config_entry_first_refresh()

    entities = [
        KanboardUserCountSensor(coordinator),
        KanboardProjectCountSensor(coordinator),
        KanboardTaskCountSensor(coordinator),
    ]

    # Aggiungi sensori per ogni progetto
    projects = coordinator.data.get("projects", [])
    for project in projects:
        entities.append(KanboardProjectTaskSensor(coordinator, project["id"], project["name"]))

    async_add_entities(entities)

class KanboardDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Kanboard data."""

    def __init__(self, hass: HomeAssistant, client: Client) -> None:
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.client = client

    async def _async_update_data(self):
        """Fetch data from Kanboard."""
        data = {}
        
        # Recupera tutti gli utenti
        data["users"] = await self.hass.async_add_executor_job(
            self.client.get_all_users
        )
        
        # Recupera tutti i progetti
        data["projects"] = await self.hass.async_add_executor_job(
            self.client.get_all_projects
        )
        
        # Recupera tutti i task
        data["tasks"] = []
        for project in data["projects"]:
            tasks = await self.hass.async_add_executor_job(
                self.client.get_all_tasks,
                project["id"]
            )
            data["tasks"].extend(tasks)
            
        return data

class KanboardUserCountSensor(BaseCoordinatorEntity, SensorEntity):
    """Sensor for tracking number of Kanboard users."""

    def __init__(self, coordinator):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = "Kanboard Users"
        self._attr_unique_id = f"{DOMAIN}_users"

    @property
    def state(self):
        """Return the state of the sensor."""
        return len(self.coordinator.data.get("users", []))

class KanboardProjectCountSensor(BaseCoordinatorEntity, SensorEntity):
    """Sensor for tracking number of Kanboard projects."""

    def __init__(self, coordinator):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = "Kanboard Projects"
        self._attr_unique_id = f"{DOMAIN}_projects"

    @property
    def state(self):
        """Return the state of the sensor."""
        projects = self.coordinator.data.get("projects", [])
        return len(projects)

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        projects = self.coordinator.data.get("projects", [])
        open_projects = len([p for p in projects if p["is_active"] == 1])
        closed_projects = len(projects) - open_projects
        
        return {
            "open": open_projects,
            "closed": closed_projects,
            "total": len(projects)
        }

class KanboardTaskCountSensor(BaseCoordinatorEntity, SensorEntity):
    """Sensor for tracking number of Kanboard tasks."""

    def __init__(self, coordinator):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = "Kanboard Tasks"
        self._attr_unique_id = f"{DOMAIN}_tasks"

    @property
    def state(self):
        """Return the state of the sensor."""
        return len(self.coordinator.data.get("tasks", []))

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        tasks = self.coordinator.data.get("tasks", [])
        in_progress = len([t for t in tasks if t["is_active"] == 1])
        stopped = len(tasks) - in_progress
        
        # Controllo scadenze
        today = datetime.now()
        due_soon = []
        overdue = []
        
        for task in tasks:
            if task["date_due"]:
                due_date = datetime.fromtimestamp(task["date_due"])
                if due_date < today:
                    overdue.append(task["title"])
                elif (due_date - today).days <= 2:
                    due_soon.append(task["title"])
        
        return {
            "in_progress": in_progress,
            "stopped": stopped,
            "total": len(tasks),
            "due_soon": due_soon,
            "overdue": overdue
        }

class KanboardProjectTaskSensor(BaseCoordinatorEntity, SensorEntity):
    """Sensor for tracking tasks in a specific Kanboard project."""

    def __init__(self, coordinator, project_id, project_name):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.project_id = project_id
        self._attr_name = f"Kanboard Project {project_name} Tasks"
        self._attr_unique_id = f"{DOMAIN}_project_{project_id}_tasks"

    @property
    def state(self):
        """Return the state of the sensor."""
        tasks = [t for t in self.coordinator.data.get("tasks", []) 
                if t["project_id"] == self.project_id]
        return len(tasks)

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        tasks = [t for t in self.coordinator.data.get("tasks", []) 
                if t["project_id"] == self.project_id]
        
        in_progress = len([t for t in tasks if t["is_active"] == 1])
        stopped = len(tasks) - in_progress
        
        return {
            "in_progress": in_progress,
            "stopped": stopped,
            "total": len(tasks)
        }