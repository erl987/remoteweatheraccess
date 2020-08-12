from datetime import datetime
from json import JSONEncoder

import requests
import json

from frontend.utils.helpers import is_temp_sensor, is_humidity_sensor

API_VERSION = "/api/v1"


class IsoDatetimeJSONEncoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()

        return super().default(o)


# TODO: generalize these functions
def get_all_stations(url, port):
    r = requests.get('http://{}:{}{}/station'.format(url, port, API_VERSION))
    r.raise_for_status()
    return r.json()


def get_available_time_limits(url, port):
    r = requests.get('http://{}:{}{}/data/limits'.format(url, port, API_VERSION))
    r.raise_for_status()
    return r.json()


def get_all_available_sensors(url, port):
    available_sensors = {}

    temperature_sensor_info = None
    humidity_sensor_info = None

    sensor_infos = _get_all_sensor_details(url, port)
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

    sensor_infos = _get_all_temp_humidity_sensor_ids(url, port)
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


def _get_all_sensor_details(url, port):
    r = requests.get('http://{}:{}{}/sensor'.format(url, port, API_VERSION))
    r.raise_for_status()
    return r.json()


def _get_all_temp_humidity_sensor_ids(url, port):
    r = requests.get('http://{}:{}{}/temp-humidity-sensor'.format(url, port, API_VERSION))
    r.raise_for_status()
    return r.json()


def get_weather_data_in_time_range(chosen_stations, chosen_sensors, start_time, end_time, url, port):
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

    r = requests.get('http://{}:{}{}/data'.format(url, port, API_VERSION),
                     data=json.dumps(request_payload, cls=IsoDatetimeJSONEncoder),
                     headers=headers)
    r.raise_for_status()
    return r.json()
