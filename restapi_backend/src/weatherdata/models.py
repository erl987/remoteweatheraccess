from dataclasses import dataclass
from datetime import datetime
from typing import List

from dataclasses_jsonschema import JsonSchemaMixin
from sqlalchemy import ForeignKey

from ..extensions import db


@dataclass
class WeatherStation(db.Model):
    id: int = db.Column(db.Integer, primary_key=True)

    station_id: str = db.Column(db.String(10), nullable=False)
    device: str = db.Column(db.String(255), nullable=False)
    location: str = db.Column(db.String(255), nullable=False)
    latitude: float = db.Column(db.Float, nullable=False)
    longitude: float = db.Column(db.Float, nullable=False)
    height: float = db.Column(db.Float, nullable=False)
    rain_calib_factor: float = db.Column(db.Float, nullable=False)


@dataclass
class CombiSensor(db.Model):
    sensor_id: str = db.Column(db.String(10), primary_key=True)
    description: str = db.Column(db.String(255), nullable=False)


@dataclass
class BaseStationData(db.Model):
    dataset_id: int = db.Column(db.Integer, primary_key=True)
    station_id: int = db.Column(ForeignKey(WeatherStation.id))

    timepoint: datetime = db.Column(db.DateTime, nullable=False)
    pressure: float = db.Column(db.Float, nullable=False)
    uv: float = db.Column(db.Float, nullable=False)

    root = db.relationship(WeatherStation, uselist=False, single_parent=True, backref="data")


@dataclass
class CombiSensorData(db.Model):
    id: int = db.Column(db.Integer, primary_key=True)
    dataset_id: int = db.Column(ForeignKey(BaseStationData.dataset_id))
    sensor_id: int = db.Column(ForeignKey(CombiSensor.sensor_id))

    temperature: float = db.Column(db.Float, nullable=False)
    humidity: float = db.Column(db.Float, nullable=False)

    data_root = db.relationship(BaseStationData, foreign_keys=[dataset_id], backref="combi_sensor_data")
    sensor_root = db.relationship(CombiSensor, foreign_keys=[sensor_id], backref="combi_sensor_data")


@dataclass
class WindSensorData(db.Model):
    id: int = db.Column(db.Integer, primary_key=True)
    dataset_id: int = db.Column(ForeignKey(BaseStationData.dataset_id))

    direction: float = db.Column(db.Float, nullable=False)
    speed: float = db.Column(db.Float, nullable=False)
    temperature: float = db.Column(db.Float, nullable=False)
    gusts: float = db.Column(db.Float, nullable=False)

    root = db.relationship(BaseStationData, backref=db.backref("wind_sensor_data", uselist=False))


@dataclass
class RainSensorData(db.Model):
    id: int = db.Column(db.Integer, primary_key=True)
    dataset_id: int = db.Column(ForeignKey(BaseStationData.dataset_id))

    rain_counter_in_mm: float = db.Column(db.Float, nullable=False)

    root = db.relationship(BaseStationData, backref=db.backref("rain_sensor_data", uselist=False))


@dataclass()
class CombiSensorRawData(JsonSchemaMixin):
    sensor_id: str
    temperature: float
    humidity: float


@dataclass
class WindSensorRawData(JsonSchemaMixin):
    direction: float
    speed: float
    temperature: float
    gusts: float


@dataclass
class WeatherRawDataset(JsonSchemaMixin):
    timepoint: datetime
    station: str
    pressure: float
    uv: float
    rain_counter: float
    temperature_humidity: List[CombiSensorRawData]
    wind: WindSensorRawData


@dataclass
class TimeRange(JsonSchemaMixin):
    first_timepoint: datetime
    last_timepoint: datetime
