from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

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
class TempHumiditySensorData(db.Model):
    dataset_id: Optional[int] = db.Column(ForeignKey("weather_dataset.id"), primary_key=True)
    sensor_id: str = db.Column(ForeignKey(CombiSensor.sensor_id), primary_key=True)

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
class WeatherDataset(db.Model):
    id: Optional[int] = db.Column(db.Integer, primary_key=True)
    station_id: str = db.Column(ForeignKey(WeatherStation.station_id))

    timepoint: datetime = db.Column(db.DateTime, nullable=False)
    pressure: float = db.Column(db.Float, nullable=False)
    uv: float = db.Column(db.Float, nullable=False)
    rain_counter: float = db.Column(db.Float, nullable=False)

    temperature_humidity: List[TempHumiditySensorData] = db.relationship(TempHumiditySensorData, lazy='joined',
                                                                         innerjoin=True, cascade="all, delete-orphan")
    wind: WindSensorData = db.relationship(WindSensorData, lazy='joined', innerjoin=True, uselist=False,
                                           cascade="all, delete-orphan")
    weather_station = db.relationship(WeatherStation, backref=db.backref("data", lazy='joined', innerjoin=True,
                                                                         uselist=False))
