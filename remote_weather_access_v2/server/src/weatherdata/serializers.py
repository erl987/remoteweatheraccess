from http import HTTPStatus

from flask_marshmallow import fields, Schema
from flask_marshmallow.sqla import ModelSchema

from .models import BaseStationData, WindSensorData, RainSensorData, WeatherData, RainDataMessage
from ..exceptions import APIError


class BaseStationDataSchema(ModelSchema):
    class Meta:
        strict = True
        model = BaseStationData


base_station_schema = BaseStationDataSchema()
base_stations_schema = BaseStationDataSchema(many=True)


class TimeRangeSchema(Schema):
    first = fields.fields.DateTime(required=True)
    last = fields.fields.DateTime(required=True)

    class Meta:
        strict = True


time_range_schema = TimeRangeSchema()


class WindSensorDataSchema(ModelSchema):
    class Meta:
        strict = True
        model = WindSensorData  # TODO: that contains the timepoint, is that required???


class RainSensorDataSchema(ModelSchema):
    class Meta:
        strict = True
        model = RainSensorData


class RainDataMessageSchema(ModelSchema):
    class Meta:
        strict = True
        model = RainDataMessage


class CombiSensorDataSchema(ModelSchema):
    class Meta:
        strict = True
        model = BaseStationData  # TODO: should have better name ...


class WeatherDataSchema(ModelSchema):
    class Meta:
        strict = True
        model = WeatherData


class WeatherDataMessageSchema(ModelSchema):
    timepoint = fields.fields.DateTime(required=True)
    station = fields.fields.String(required=True)
    base = fields.fields.Nested(WeatherDataSchema, required=True, exclude=['timepoint'])
    temperature_humidity = fields.fields.Nested(CombiSensorDataSchema, many=True, required=True, exclude=['timepoint'])
    rain = fields.fields.Nested(RainDataMessageSchema, required=True)
    wind = fields.fields.Nested(WindSensorDataSchema, required=True, exclude=['timepoint'])

    class Meta:
        strict = True


weather_data_message_schema = WeatherDataMessageSchema()


def deserialize_weather_data_message(json):
    if not json:
        raise APIError('Required Content-Type is `application/json`', status_code=HTTPStatus.BAD_REQUEST)

    # TODO: fails with NoneType error ...
    request_object = weather_data_message_schema.load(json)
    return request_object.data


def deserialize_base_station_dataset(json):
    if not json:
        raise APIError('Required Content-Type is `application/json`', status_code=HTTPStatus.BAD_REQUEST)

    request_object = base_station_schema.load(json)
    return request_object.data
