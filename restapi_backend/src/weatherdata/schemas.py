import marshmallow
import marshmallow_sqlalchemy
from marshmallow.schema import Schema
from marshmallow_sqlalchemy import fields

from ..extensions import ma
from ..weatherdata.models import WindSensorData, TempHumiditySensorData, WeatherDataset


class WindSensorSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = WindSensorData
        exclude = ("id", "dataset_id")
        include_fk = True
        load_instance = True


class TempHumiditySensorSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = TempHumiditySensorData
        exclude = ("dataset_id",)
        include_fk = True
        load_instance = True


class WeatherDatasetSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = WeatherDataset
        exclude = ("id", )
        include_fk = True
        load_instance = True

    wind = marshmallow_sqlalchemy.fields.Nested(WindSensorSchema)
    temperature_humidity = marshmallow_sqlalchemy.fields.Nested(TempHumiditySensorSchema, many=True)


class GetWeatherdataPayloadSchema(Schema):
    first_timepoint = marshmallow.fields.DateTime()
    last_timepoint = marshmallow.fields.DateTime()
    sensors = marshmallow.fields.List(marshmallow.fields.String)


# initialize the schemas
get_weatherdata_payload_schema = GetWeatherdataPayloadSchema()
weather_dataset_schema = WeatherDatasetSchema(many=True)
