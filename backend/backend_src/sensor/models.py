#  Remote Weather Access - Client/server solution for distributed weather networks
#   Copyright (C) 2013-2023 Ralf Rettig (info@personalfme.de)
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.

from dataclasses import dataclass

from ..extensions import db


@dataclass
class Sensor(db.Model):
    __bind_key__ = 'weather-data'

    sensor_id: str = db.Column(db.String(30), primary_key=True)

    description: str = db.Column(db.String(255), nullable=False)
    unit: str = db.Column(db.String(30), nullable=False)


def generate_sensors():
    sensors_info = {
        'pressure': {'description': 'Luftdruck', 'unit': 'hPa'},
        'uv': {'description': 'UV', 'unit': 'UV-X'},
        'rain': {'description': 'Regen', 'unit': 'mm'},
        'rain_rate': {'description': 'Regenrate', 'unit': 'mm'},
        'temperature': {'description': 'Temperatur', 'unit': '\N{DEGREE SIGN}C'},
        'humidity': {'description': 'Luftfeuchte', 'unit': '%'},
        'dewpoint': {'description': 'Taupunkt', 'unit': '\N{DEGREE SIGN}C'},
        'speed': {'description': 'Windgeschwindigkeit', 'unit': 'km/h'},
        'gusts': {'description': 'Windböen', 'unit': 'km/h'},
        'direction': {'description': 'Windrichtung', 'unit': '\N{DEGREE SIGN}'},
        'wind_temperature': {'description': 'Windchilltemperatur', 'unit': '\N{DEGREE SIGN}C'}
    }

    all_sensors = []
    for sensor_id, sensor_info in sensors_info.items():
        sensor = Sensor()
        sensor.sensor_id = sensor_id
        sensor.description = sensor_info['description']
        sensor.unit = sensor_info['unit']
        all_sensors.append(sensor)

    return all_sensors
