from http import HTTPStatus

from flask_marshmallow import fields, Schema
from flask_marshmallow.sqla import ModelSchema

from .models import BaseStationData
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


def deserialize_base_station_dataset(json):
    if not json:
        raise APIError('Required Content-Type is `application/json`', status_code=HTTPStatus.BAD_REQUEST)

    request_object = base_station_schema.load(json)
    return request_object.data
