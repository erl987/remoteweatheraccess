from datetime import timedelta, datetime

import dash
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
import dateutil

from remote_weather_access.common.datastructures import BaseStationSensorData, RainSensorData, WindSensorData
from remote_weather_access.server.sqldatabase import SQLWeatherDB


db_file_name = r"C:\Users\Ralf\Documents\code\remote-weather-access\remote_weather_access_v2\frontend\gui\weather.db"
initial_time_period = timedelta(days=7)

external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

sensor_mapping = {"uv": {"description": "Luftdruck",
                         "id": (BaseStationSensorData.BASE_STATION, BaseStationSensorData.PRESSURE)},
                  "pressure": {"description": "UV",
                               "id": (BaseStationSensorData.BASE_STATION, BaseStationSensorData.UV)},
                  "rain_cumulated": {"description": "Regen",
                                     "id": (RainSensorData.RAIN, RainSensorData.CUMULATED)},
                  "rain_period": {"description": "Regenrate",
                                  "id": (RainSensorData.RAIN, RainSensorData.PERIOD)},
                  "wind_average": {"description": "Mittelwind",
                                   "id": (WindSensorData.WIND, WindSensorData.AVERAGE)},
                  "wind_gusts": {"description": "Windböen",
                                 "id": (WindSensorData.WIND, WindSensorData.GUSTS)},
                  "wind_direction": {"description": "Windrichtung",
                                     "id": (WindSensorData.WIND, WindSensorData.DIRECTION)},
                  "wind_chill": {"description": "Windchilltemperatur",
                                 "id": (WindSensorData.WIND, WindSensorData.WIND_CHILL)}
                  }

weather_db = SQLWeatherDB(db_file_name)
last_time = datetime.min
for station_id in weather_db.get_stations():
    last_time = max(last_time, weather_db.get_most_recent_time_with_data(station_id))
combi_sensor_ids, combi_sensor_descriptions = weather_db.get_combi_sensors()
for id in combi_sensor_ids:
    sensor_mapping["{}_temp".format(id)] = {"description": "{} Temperatur".format(id), "id": (id, "temperature")}
    sensor_mapping["{}_humid".format(id)] = {"description": "{} Luftfeuchte".format(id), "id": (id, "humidity")}

available_sensors = []
for internal_sensor_id, sensor_info in sensor_mapping.items():
    available_sensors.append({"label": sensor_info["description"], "value": internal_sensor_id})

available_stations = []
for station_id in weather_db.get_stations():
    available_stations.append({"label": station_id, "value": station_id})

app.layout = html.Div(children=[
    html.H1(children="Wetterdaten"),

    dcc.Graph(id="weather-data-graph"),

    html.H2(children="Sensoren"),

    dcc.Dropdown(
      id="sensor-dropdown",
      options=available_sensors,
      value=available_sensors[0]["value"],
      multi=True
    ),

    html.H2(children="Station"),

    dcc.Dropdown(
        id="station-dropdown",
        options=available_stations,
        value=available_stations[-1]["value"],
        multi=True
    ),

    html.H2(children="Zeitraum"),

    html.Div(
        dcc.DatePickerRange(
            id="time-period-picker",
            min_date_allowed=datetime(2000, 1, 1),
            max_date_allowed=last_time,
            initial_visible_month=last_time,
            start_date=last_time - initial_time_period,
            end_date=last_time
        )
    )
])


@app.callback(
    Output("weather-data-graph", "figure"),
    [Input(component_id="time-period-picker", component_property="start_date"),
     Input(component_id="time-period-picker", component_property="end_date"),
     Input(component_id="station-dropdown", component_property="value"),
     Input(component_id="sensor-dropdown", component_property="value")]
)
def update_weather_plot(start_time_str, end_time_str, chosen_stations, sensors):
    start_time = dateutil.parser.parse(start_time_str)
    end_time = dateutil.parser.parse(end_time_str)

    if isinstance(chosen_stations, str):
        chosen_stations = [chosen_stations]
    if isinstance(sensors, str):
        sensors = [sensors]

    plot_data = []
    for internal_sensor_id in sensors:
        sensor_tuple = sensor_mapping[internal_sensor_id]["id"]
        sensor_description = sensor_mapping[internal_sensor_id]["description"]
        for station_id in chosen_stations:
            data = weather_db.get_data_in_time_range(station_id, start_time, end_time)
            time = [line.get_time() for line in data]
            sensor_data = [float(line.get_sensor_value(sensor_tuple)) for line in data]
            plot_data.append({"x": time, "y": sensor_data,
                              "name": "{} - {}".format(station_id, sensor_description)})

    figure_config = {
        "data": plot_data,
        "layout": {
            "title": "Wetterdaten"
        }
    }

    return figure_config


if __name__ == "__main__":
    app.run_server(debug=True)
