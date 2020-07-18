"""
Reads the HealthGrapi API in a sensor.
For more details about this platform, please refer to the documentation at
GITHUB HERE BABY
"""

import logging
import voluptuous as vol
import json
import requests
import homeassistant.helpers.config_validation as cv

from datetime import datetime
from datetime import timedelta
from homeassistant.components.sensor import (PLATFORM_SCHEMA)
from homeassistant.util import Throttle
from homeassistant.helpers.entity import Entity

__version__ = '0.2'

CONF_API_KEY = 'api_key'
CONF_NAME = 'name'

# Put this in config
MIN_TIME_BETWEEN_UPDATES = timedelta(minutes=60)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_NAME): cv.string,
    vol.Required(CONF_API_KEY): cv.string
})

_LOG = logging.getLogger(__name__)

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the accounts to query"""
    _LOG.info(">>>>>>>>>>>>>>> Setting up HealthGraph <<<<<<<<<<<<<<")
    add_entities([HealthGraph(hass, config)])

class HealthGraph(Entity):
    def __init__(self, hass, config):
        _LOG.info("Initializing")
        self.hass = hass
        self._api_key = config[CONF_API_KEY]
        self._name = config[CONF_NAME]
        self._state = None
        self._latest_type = None
        self._latest = None
        self._release = None
        self._snapshot = None
        self._lastupdated = None
        self._total_time = None
        self._total_bike = 0
        self._bike_distance = 0
        self._bike_time = None
        self._total_runs = 0
        self._run_distance = None
        self._run_time = None
        self._average_pace = None
        self._total_weights = 0
        self.update()

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        _LOG.info("Updating from HealthGraph API")
        today = datetime.today()
        offset = (today.weekday() - 6) % 7
        lastsundate = today-timedelta(days=offset)
        sunday = lastsundate.strftime("%Y-%m-%d")
        _LOG.debug("Last Sunday was %s", sunday)

        url = "https://api.runkeeper.com/fitnessActivities?noEarlierThan={0}".format(sunday)

        head = {"authorization": self._api_key }

        try:
            response = requests.get(url,headers=head)
            _LOG.debug("Return code %i", response.status_code)
            payload = response.json()
            _LOG.debug("Activites: %s", payload['items'] )
            runningDistance = 0
            totalSeconds = 0
            runningSeconds = 0
            runCount = 0
            weightCount = 0
            bikeCount = 0
            bikeDistance = 0
            bikeSeconds = 0

            for activity in payload['items']:
                activityType = activity['type']
                _LOG.debug(">>> Processing: %s", activityType )
                seconds = activity['duration']
                totalSeconds += seconds
                if activityType == "Running":
                    _LOG.debug("Running Activity")
                    runningDistance += (activity['total_distance'] * 0.000621371)
                    runningSeconds += seconds
                    runCount += 1
                elif activityType == 'Strength Training':
                    _LOG.debug("Weights")
                    weightCount += 1
                elif activityType == 'Cycling':
                    _LOG.debug("Cycling")
                    bikeCount += 1
                    bikeDistance += (activity['total_distance'] * 0.000621371)
                    bikeSeconds += seconds

            _LOG.debug("Total Seconds: %f", totalSeconds)

            _LOG.debug("Total Runs: %i", runCount)
            runningDistance = round(runningDistance, 2)
            _LOG.debug("Running Distance: %s", str(runningDistance))
            runningTime = str(timedelta(seconds=runningSeconds))
            _LOG.debug("Running Time: %s", runningTime )
            
            averagePaceSeconds = runningSeconds / runningDistance
            hours, remainder = divmod(averagePaceSeconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            averagePace = str(int(minutes)) + ":" + str(int(seconds))
            # averagePace = timedelta(seconds=averagePaceSeconds).strftime("%M:%S")
            _LOG.debug("Average Pace: %s", averagePace )

            totalTime = str(timedelta(seconds=totalSeconds))
            _LOG.debug("Total Time: %s", totalTime )
            
            self._total_runs = runCount
            self._run_time = runningTime
            self._run_distance = str(runningDistance)
            self._average_pace = averagePace

            self._total_bike = bikeCount
            self._bike_distance = round(bikeDistance, 2)
            self._bike_time = str(timedelta(seconds=bikeSeconds))

            self._total_weights = weightCount
            self._total_time = totalTime

            self._state = "Connected"
            """self._state = data[self.departure].get('prdctdn')        """
        except Exception as err:  
            _LOG.warning("Exception calling HealthGraph API: %s", err)
            traceback.print_exc(file=sys.stdout)
            self._state = "Failed"
        _LOG.debug(self._state)
    @property
    def state(self):
        return self._state
    
    @property
    def name(self):
        return "healthgraph." + self._name

    @property
    def total_runs(self):
        return self._total_runs

    @property
    def total_weights(self):
        return self._total_weights

    @property
    def total_runs(self):
        return self._total_time

    @property
    def running_distance(self):
        return self._run_distance

    @property
    def running_time(self):
        return self._run_time

    @property
    def average_pace(self):
        return self._average_pace

    @property 
    def total_bike(self):
        return self._total_bike

    @property
    def bike_distance(self):
        return self._bike_distance

    @property
    def bike_time(self):
        return self._bike_time

    @property
    def icon(self):
        return 'mdi:weight-lifter'
    
    @property
    def device_state_attributes(self):
        return {
            'total_runs': self._total_runs,
            'total_weights': self._total_weights,
            'total_time': self._total_time,
            'running_distance': self._run_distance,
            'running_time' : self._run_time,
            'average_pace': self._average_pace,
            'total_bike' : self._total_bike,
            'bike_distance': self._bike_distance,
            'bike_time': self._bike_time,
            'latest_type': self._latest_type,
            'latest': self._latest,
            'release': self._release,
            'snapshot': self._snapshot
        }        