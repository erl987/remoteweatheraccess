from ..extensions import ma
from ..models import WeatherStation


class WeatherStationSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = WeatherStation
        load_instance = True


# initialize the schemas
weather_station_schema = WeatherStationSchema()
many_weather_stations_schema = WeatherStationSchema(many=True)
