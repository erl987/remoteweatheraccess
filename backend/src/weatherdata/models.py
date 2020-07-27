from dataclasses import dataclass
from datetime import datetime
from typing import List

from sqlalchemy import ForeignKey

from ..extensions import db


@dataclass
class WeatherStation(db.Model):
    id: int = db.Column(db.Integer, primary_key=True)

    station_id: str = db.Column(db.String(10), unique=True, nullable=False)
    device: str = db.Column(db.String(255), nullable=False)
    location: str = db.Column(db.String(255), nullable=False)
    latitude: float = db.Column(db.Float, nullable=False)
    longitude: float = db.Column(db.Float, nullable=False)
    height: float = db.Column(db.Float, nullable=False)
    rain_calib_factor: float = db.Column(db.Float, nullable=False)


@dataclass
class TempHumiditySensor(db.Model):
    sensor_id: str = db.Column(db.String(10), primary_key=True)

    description: str = db.Column(db.String(255), nullable=False)

    sensor_data = db.relationship("TempHumiditySensorData")


@dataclass
class TempHumiditySensorData(db.Model):
    timepoint: int = db.Column(db.DateTime, primary_key=True)
    station_id: str = db.Column(db.String(10), primary_key=True)
    sensor_id: str = db.Column(db.String(10), ForeignKey(TempHumiditySensor.sensor_id), primary_key=True)

    temperature: float = db.Column(db.Float, nullable=False)
    humidity: float = db.Column(db.Float, nullable=False)

    __table_args__ = (db.ForeignKeyConstraint(
        [timepoint, station_id],
        ['weather_dataset.timepoint', 'weather_dataset.station_id']),
    )


@dataclass
class WindSensorData(db.Model):
    timepoint: int = db.Column(db.DateTime, primary_key=True)
    station_id: str = db.Column(db.String(10), primary_key=True)

    direction: float = db.Column(db.Float, nullable=False)
    speed: float = db.Column(db.Float, nullable=False)
    wind_temperature: float = db.Column(db.Float, nullable=False)
    gusts: float = db.Column(db.Float, nullable=False)

    __table_args__ = (db.ForeignKeyConstraint(
        [timepoint, station_id],
        ['weather_dataset.timepoint', 'weather_dataset.station_id']),
    )


@dataclass
class WeatherDataset(db.Model):
    timepoint: datetime = db.Column(db.DateTime, primary_key=True)
    station_id: str = db.Column(db.String(10), ForeignKey(WeatherStation.station_id), primary_key=True)

    pressure: float = db.Column(db.Float, nullable=False)
    uv: float = db.Column(db.Float, nullable=False)
    rain_counter: float = db.Column(db.Float, nullable=False)

    temperature_humidity: List[TempHumiditySensorData] = db.relationship(
        TempHumiditySensorData,
        cascade='all, delete-orphan')
    wind: WindSensorData = db.relationship(
        WindSensorData,
        uselist=False,
        cascade='all, delete-orphan')
    weather_station = db.relationship(WeatherStation, backref=db.backref(
        'data',
        cascade='all, delete-orphan'))


def generate_temp_humidity_sensors():
    in_sensor = TempHumiditySensor()
    in_sensor.sensor_id = 'IN'
    in_sensor.description = 'innen'

    out_sensor_1 = TempHumiditySensor()
    out_sensor_1.sensor_id = 'OUT1'
    out_sensor_1.description = 'außen'

    sensors = [in_sensor, out_sensor_1]

    return sensors
