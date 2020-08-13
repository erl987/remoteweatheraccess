from datetime import datetime
from json import JSONEncoder

import requests
import json

from frontend.utils.helpers import is_temp_sensor, is_humidity_sensor


class IsoDatetimeJSONEncoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()

        return super().default(o)


class Backend(object):
    API_VERSION = "/api/v1"

    def __init__(self, url, port):
        self._url = url
        self._port = port

    def get_all_stations(self):
        return self._simple_get_request("station")

    def get_available_time_limits(self):
        return self._simple_get_request("data/limits")

    def get_all_available_sensors(self):
        available_sensors = {}

        temperature_sensor_info = None
        humidity_sensor_info = None

        sensor_infos = self._simple_get_request("sensor")
        for sensor_info in sensor_infos:
            sensor_id = sensor_info["sensor_id"]
            if sensor_id == "temperature":
                temperature_sensor_info = sensor_info
            elif sensor_id == "humidity":
                humidity_sensor_info = sensor_info
            else:
                available_sensors[sensor_id] = {
                    "description": sensor_info["description"],
                    "unit": sensor_info["unit"]
                }

        sensor_infos = self._simple_get_request("temp-humidity-sensor")
        for sensor_info in sensor_infos:
            temp_sensor_id = sensor_info["sensor_id"] + "_temp"
            humidity_sensor_id = sensor_info["sensor_id"] + "_humid"
            available_sensors[temp_sensor_id] = {
                "description": temperature_sensor_info["description"] + " " + sensor_info["description"],
                "unit": temperature_sensor_info["unit"]
            }
            available_sensors[humidity_sensor_id] = {
                "description": humidity_sensor_info["description"] + " " + sensor_info["description"],
                "unit": humidity_sensor_info["unit"]
            }

        return available_sensors

    def get_weather_data_in_time_range(self, chosen_stations, chosen_sensors, start_time, end_time):
        provided_sensors = []
        for sensor in chosen_sensors:
            if is_temp_sensor(sensor):
                provided_sensors.append("temperature")
            elif is_humidity_sensor(sensor):
                provided_sensors.append("humidity")
            else:
                provided_sensors.append(sensor)

        request_payload = {
            "first_timepoint": start_time,
            "last_timepoint": end_time,
            "sensors": provided_sensors,
            "stations": chosen_stations
        }

        headers = {
            "Content-Type": "application/json"
        }

        r = requests.get('http://{}:{}{}/data'.format(self._url, self._port, Backend.API_VERSION),
                         data=json.dumps(request_payload, cls=IsoDatetimeJSONEncoder),
                         headers=headers)
        r.raise_for_status()
        return r.json()

    def _simple_get_request(self, endpoint):
        r = requests.get('http://{}:{}{}/{}'.format(self._url, self._port, Backend.API_VERSION, endpoint))
        r.raise_for_status()
        return r.json()
