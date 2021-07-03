#  Remote Weather Access - Client/server solution for distributed weather networks
#   Copyright (C) 2013-2021 Ralf Rettig (info@personalfme.de)
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

import marshmallow
import marshmallow_sqlalchemy
from marshmallow.schema import Schema
from marshmallow_sqlalchemy import fields, field_for

from ..extensions import ma
from ..models import TempHumiditySensorData, WeatherDataset


class TempHumiditySensorSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = TempHumiditySensorData
        exclude = ('timepoint', 'station_id')
        include_fk = True
        load_instance = True
        transient = True

        timepoint = field_for(TempHumiditySensorData, 'timepoint', dump_only=True)
        station_id = field_for(TempHumiditySensorData, 'station_id', dump_only=True)
        sensor_id = field_for(TempHumiditySensorData, 'sensor_id', dump_only=True)


class WeatherDatasetSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = WeatherDataset
        include_fk = True
        load_instance = True
        transient = True

    temperature_humidity = marshmallow_sqlalchemy.fields.Nested(TempHumiditySensorSchema, many=True)


class TimePeriodWithSensorsAndStationsSchema(Schema):
    first_timepoint = marshmallow.fields.DateTime(required=True)
    last_timepoint = marshmallow.fields.DateTime(required=True)
    sensors = marshmallow.fields.List(marshmallow.fields.String, required=True)
    stations = marshmallow.fields.List(marshmallow.fields.String, required=True)


class TimePeriodWithStationSchema(Schema):
    first_timepoint = marshmallow.fields.DateTime(required=True)
    last_timepoint = marshmallow.fields.DateTime(required=True)
    stations = marshmallow.fields.List(marshmallow.fields.String, required=True)


# initialize the schemas
time_period_with_sensors_and_stations_schema = TimePeriodWithSensorsAndStationsSchema()
time_period_with_stations_schema = TimePeriodWithStationSchema()
single_weather_dataset_schema = WeatherDatasetSchema()
many_weather_datasets_schema = WeatherDatasetSchema(many=True)
