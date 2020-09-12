#  Remote Weather Access - Client/server solution for distributed weather networks
#   Copyright (C) 2013-2020 Ralf Rettig (info@personalfme.de)
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

import random
import string
from dataclasses import dataclass
from datetime import datetime
from http import HTTPStatus
from typing import List

from sqlalchemy import ForeignKey
from sqlalchemy.orm import validates

from src.exceptions import APIError
from src.extensions import db, flask_bcrypt
from src.sensor.models import generate_sensors, Sensor
from src.utils import Role, ROLES, USER_NAME_REGEX

DEFAULT_ADMIN_USER_NAME = 'default_admin'


@dataclass
class WeatherStation(db.Model):
    __bind_key__ = 'weather-data'

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
    __bind_key__ = 'weather-data'

    sensor_id: str = db.Column(db.String(10), primary_key=True)

    description: str = db.Column(db.String(255), nullable=False)

    sensor_data = db.relationship('TempHumiditySensorData')


@dataclass
class TempHumiditySensorData(db.Model):
    __bind_key__ = 'weather-data'

    timepoint: int = db.Column(db.DateTime(timezone=True), primary_key=True)
    station_id: str = db.Column(db.String(10), primary_key=True)
    sensor_id: str = db.Column(db.String(10), ForeignKey(TempHumiditySensor.sensor_id), primary_key=True)

    temperature: float = db.Column(db.Float, nullable=False)
    humidity: float = db.Column(db.Float, nullable=False)

    __table_args__ = (db.ForeignKeyConstraint(
        [timepoint, station_id],
        ['weather_dataset.timepoint', 'weather_dataset.station_id']),
    )


@dataclass
class WeatherDataset(db.Model):
    __bind_key__ = 'weather-data'

    timepoint: datetime = db.Column(db.DateTime(timezone=True), primary_key=True)
    station_id: str = db.Column(db.String(10), ForeignKey(WeatherStation.station_id), primary_key=True)

    pressure: float = db.Column(db.Float, nullable=False)
    uv: float = db.Column(db.Float, nullable=False)
    rain_counter: float = db.Column(db.Float, nullable=False)

    direction: float = db.Column(db.Float, nullable=False)
    speed: float = db.Column(db.Float, nullable=False)
    wind_temperature: float = db.Column(db.Float, nullable=False)
    gusts: float = db.Column(db.Float, nullable=False)

    temperature_humidity: List[TempHumiditySensorData] = db.relationship(
        TempHumiditySensorData,
        cascade='all, delete-orphan')
    weather_station = db.relationship(WeatherStation, backref=db.backref(
        'data',
        cascade='all, delete-orphan'))


@dataclass
class FullUser(db.Model):
    id: int = db.Column(db.Integer, primary_key=True)

    name: str = db.Column(db.String(120), unique=True, nullable=False)
    password: str = db.Column(db.String(120), nullable=False)
    role: str = db.Column(db.String(10), nullable=False)
    station_id: str = db.Column(db.String(10), nullable=True)

    @validates('role')
    def validate_role(self, _, value):
        if value.upper() not in ROLES:
            raise APIError('Role not existing', status_code=HTTPStatus.BAD_REQUEST)
        return value

    @validates('name')
    def validate_name(self, _, value):
        if USER_NAME_REGEX.match(value) is None:
            raise APIError('User name does not fulfill the constraints (3-30 characters, only letters, '
                           'digits and "-_.")'.format(id), status_code=HTTPStatus.BAD_REQUEST)
        return value

    def validate_password(self):
        if not self.password or len(self.password) < 3:
            raise APIError('Password does not fulfill constraints (>= 3 characters)',
                           status_code=HTTPStatus.BAD_REQUEST)

    def save_to_db(self, do_add=True):
        self.validate_password()
        self.password = flask_bcrypt.generate_password_hash(self.password).decode('utf-8')
        self.role = self.role.upper()
        if do_add:
            db.session.add(self)
        db.session.commit()


def generate_temp_humidity_sensors():
    in_sensor = TempHumiditySensor()
    in_sensor.sensor_id = 'IN'
    in_sensor.description = 'innen'

    out_sensor_1 = TempHumiditySensor()
    out_sensor_1.sensor_id = 'OUT1'
    out_sensor_1.description = 'außen'

    sensors = [in_sensor, out_sensor_1]

    return sensors


def generate_random_password(string_length=8):
    password_characters = string.ascii_letters + string.digits
    return ''.join(random.choice(password_characters) for _ in range(string_length))


def generate_default_admin_user():
    default_admin = FullUser()
    default_admin.name = DEFAULT_ADMIN_USER_NAME
    default_admin.password = generate_random_password()
    default_admin.role = Role.ADMIN.name
    default_admin.station_id = None  # irrelevant for admin role

    return default_admin


def create_default_admin_user(app):
    admin_user = generate_default_admin_user()
    admin_password = admin_user.password
    admin_user.save_to_db()
    app.logger.warning('Added a new default ADMIN user \'{}\' with password \'{}\' to the database. '
                       'Create an own admin user with another password and delete the default '
                       'admin user immediately!'.format(admin_user.name, admin_password))


def create_temp_humidity_sensors():
    sensors = generate_temp_humidity_sensors()
    db.session.add_all(sensors)
    db.session.commit()


def create_sensors():
    sensors = generate_sensors()
    db.session.add_all(sensors)
    db.session.commit()


def prepare_database(app):
    with app.app_context():
        db.create_all()

        default_admin_user = db.session.query(FullUser).filter(FullUser.name == DEFAULT_ADMIN_USER_NAME).one_or_none()
        if not default_admin_user:
            create_default_admin_user(app)

        num_temp_humidity_sensors = db.session.query(TempHumiditySensor).count()
        if num_temp_humidity_sensors == 0:
            create_temp_humidity_sensors()

        num_sensors = db.session.query(Sensor).count()
        if num_sensors == 0:
            create_sensors()
