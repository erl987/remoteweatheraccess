from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from dataclasses_jsonschema import JsonSchemaMixin
from sqlalchemy import ForeignKey

from ..extensions import db


@dataclass
class WeatherStation(db.Model):
    id: Optional[int] = db.Column(db.Integer, primary_key=True)

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
class CombiSensorData(db.Model):
    dataset_id: Optional[int] = db.Column(ForeignKey("weather_dataset.id"), primary_key=True)
    sensor_id: Optional[str] = db.Column(ForeignKey(CombiSensor.sensor_id), primary_key=True)

    temperature: float = db.Column(db.Float, nullable=False)
    humidity: float = db.Column(db.Float, nullable=False)

    combi_sensor = db.relationship(CombiSensor)


@dataclass
class WindSensorData(db.Model):
    id: Optional[int] = db.Column(db.Integer, primary_key=True)
    dataset_id: Optional[int] = db.Column(ForeignKey("weather_dataset.id"))

    direction: float = db.Column(db.Float, nullable=False)
    speed: float = db.Column(db.Float, nullable=False)
    wind_temperature: float = db.Column(db.Float, nullable=False)
    gusts: float = db.Column(db.Float, nullable=False)


@dataclass
class RainSensorData(db.Model):
    id: Optional[int] = db.Column(db.Integer, primary_key=True)
    dataset_id: Optional[int] = db.Column(ForeignKey("weather_dataset.id"))

    rain_counter_in_mm: float = db.Column(db.Float, nullable=False)


@dataclass
class WeatherDataset(db.Model):
    id: Optional[int] = db.Column(db.Integer, primary_key=True)
    station_id: Optional[str] = db.Column(ForeignKey(WeatherStation.id))

    timepoint: datetime = db.Column(db.DateTime, nullable=False)
    pressure: float = db.Column(db.Float, nullable=False)
    uv: float = db.Column(db.Float, nullable=False)

    combi_sensor_data: List[CombiSensorData] = db.relationship(CombiSensorData, lazy='joined', innerjoin=True,
                                                               cascade="all, delete-orphan")
    rain_sensor_data: RainSensorData = db.relationship(RainSensorData, lazy='joined', innerjoin=True, uselist=False,
                                                       cascade="all, delete-orphan")
    wind_sensor_data: WindSensorData = db.relationship(WindSensorData, lazy='joined', innerjoin=True, uselist=False,
                                                       cascade="all, delete-orphan")
    weather_station = db.relationship(WeatherStation, backref=db.backref("data", lazy='joined', innerjoin=True,
                                                                         uselist=False))


@dataclass()
class CombiSensorRawData(JsonSchemaMixin):
    sensor_id: str
    temperature: float
    humidity: float


@dataclass
class WindSensorRawData(JsonSchemaMixin):
    direction: float
    speed: float
    wind_temperature: float
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
class GetWeatherdataPayload(JsonSchemaMixin):
    first_timepoint: datetime
    last_timepoint: datetime
    sensors: List[str]
