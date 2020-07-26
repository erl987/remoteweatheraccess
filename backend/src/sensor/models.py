from dataclasses import dataclass

from ..extensions import db


@dataclass
class Sensor(db.Model):
    sensor_id: str = db.Column(db.String(10), primary_key=True)

    description: str = db.Column(db.String(255), nullable=False)
    unit: str = db.Column(db.String(10), nullable=False)


def generate_sensors():
    sensors_info = {
        "pressure": {"description": "Druck", "unit": "Pa"},
        "uv": {"description": "UV", "unit": "UV-X"},
        "rain_counter": {"description": "Regenzähler", "unit": "mm"},
        "temperature": {"description": "Temperatur", "unit": "\N{DEGREE SIGN}C"},
        "humidity": {"description": "Luftfeuchte", "unit": "%"},
        "wind_speed": {"description": "Windgeschwindigkeit", "unit": "km/h"},
        "wind_gusts": {"description": "Windböen", "unit": "km/h"},
        "wind_direction": {"description": "Windrichtung", "unit": "\{DEGREE SIGN}"},
        "wind_temperature": {"description": "Windchilltemperatur", "unit": "\N{DEGREE SIGN}C"}
    }

    all_sensors = []
    for sensor_id, sensor_info in sensors_info.items():
        sensor = Sensor()
        sensor.sensor_id = sensor_id
        sensor.description = sensor_info["description"]
        sensor.unit = sensor_info["unit"]
        all_sensors.append(sensor)

    return all_sensors
