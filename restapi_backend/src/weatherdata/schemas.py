import marshmallow
import marshmallow_sqlalchemy
from marshmallow.schema import Schema
from marshmallow_sqlalchemy import fields, field_for

from ..extensions import ma
from ..weatherdata.models import WindSensorData, TempHumiditySensorData, WeatherDataset


class WindSensorSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = WindSensorData
        exclude = ("timepoint", "station_id")
        include_fk = True
        load_instance = True

        timepoint = field_for(WindSensorData, "timepoint", dump_only=True)
        station_id = field_for(WindSensorData, "station_id", dump_only=True)


class TempHumiditySensorSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = TempHumiditySensorData
        exclude = ("timepoint", "station_id")
        include_fk = True
        load_instance = True

        timepoint = field_for(TempHumiditySensorData, "timepoint", dump_only=True)
        station_id = field_for(TempHumiditySensorData, "station_id", dump_only=True)
        sensor_id = field_for(TempHumiditySensorData, "sensor_id", dump_only=True)


class WeatherDatasetSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = WeatherDataset
        include_fk = True
        load_instance = True

    wind = marshmallow_sqlalchemy.fields.Nested(WindSensorSchema)
    temperature_humidity = marshmallow_sqlalchemy.fields.Nested(TempHumiditySensorSchema, many=True)


class TimePeriodWithSensorsSchema(Schema):
    first_timepoint = marshmallow.fields.DateTime(required=True)
    last_timepoint = marshmallow.fields.DateTime(required=True)
    sensors = marshmallow.fields.List(marshmallow.fields.String, required=True)


class TimePeriodWithStationSchema(Schema):
    first_timepoint = marshmallow.fields.DateTime(required=True)
    last_timepoint = marshmallow.fields.DateTime(required=True)
    stations = marshmallow.fields.List(marshmallow.fields.String, required=True)


# initialize the schemas
time_period_with_sensors_schema = TimePeriodWithSensorsSchema()
time_period_with_stations_schema = TimePeriodWithStationSchema()
weather_dataset_schema = WeatherDatasetSchema(many=True)
