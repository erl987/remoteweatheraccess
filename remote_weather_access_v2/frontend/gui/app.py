from datetime import timedelta, datetime

import dash
from dash.dependencies import Input, Output
import utils.dash_reusable_components as drc
import dash_core_components as dcc
import dash_html_components as html
import dateutil

from remote_weather_access.common.datastructures import BaseStationSensorData, RainSensorData, WindSensorData
from remote_weather_access.server.sqldatabase import SQLWeatherDB


db_file_name = r"C:\Users\Ralf\Documents\code\remote-weather-access\remote_weather_access_v2\frontend\gui\weather.db"
initial_time_period = timedelta(days=7)

app = dash.Dash(__name__)

tab_style = {
    'borderBottom': '1px solid #d6d6d6',
    'padding': '6px',
    'fontWeight': 'bold'
}

tab_selected_style = {
    'borderTop': '1px solid #d6d6d6',
    'borderBottom': '1px solid #d6d6d6',
    'backgroundColor': '#ff4444',
    'color': 'white',
    'padding': '6px'
}

config_plots = {"locale": "de"}

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
station_info_tabs = []
for station_id in weather_db.get_stations():
    available_stations.append({"label": station_id, "value": station_id})
    station_metadata = weather_db.get_station_metadata(station_id)
    device = station_metadata.get_device_info()
    location = station_metadata.get_location_info()
    latitude, longitude, height = station_metadata.get_geo_info()
    if latitude > 0:
        latitude_str = "{}\N{DEGREE SIGN} N".format(latitude)
    else:
        latitude_str = "{}\N{DEGREE SIGN} S".format(latitude)
    if longitude > 0:
        longitude_str = "{}\N{DEGREE SIGN} O".format(longitude)
    else:
        longitude_str = "{}\N{DEGREE SIGN} W".format(longitude)

    station_info_tabs.append(
        dcc.Tab(
            label=station_id,
            value=station_id,
            style=tab_style,
            selected_style=tab_selected_style,
            children=[
                html.Div(
                    id="location_info_div_{}".format(station_id),
                    children=[
                        drc.NamedInput(
                            name="Standort",
                            className="input",
                            id="location_info_{}".format(station_id),
                            placeholder=location,
                        )
                    ]
                ),
                html.Div(
                    id="height_info_div_{}".format(station_id),
                    children=[
                        drc.NamedInput(
                            name="Höhe",
                            className="input",
                            id="height_info_{}".format(station_id),
                            placeholder="{} m".format(height),
                        )
                    ]
                ),
                html.Div(
                    id="coordinates_info_div_{}".format(station_id),
                    children=[
                        drc.NamedInput(
                            name="Koordinaten",
                            className="input",
                            id="coordinates_info_{}".format(station_id),
                            placeholder="{} / {}".format(latitude_str, longitude_str),
                        )
                    ]
                ),
                html.Div(
                    id="device_info_div_{}".format(station_id),
                    children=[
                        drc.NamedInput(
                            name="Wetterstation",
                            className="input",
                            id="device_info_{}".format(station_id),
                            placeholder=device,
                        )
                    ]
                )
            ]
        )
    )

app.layout = html.Div(
    id="app-container",

    children=[
        html.H1(className="heading", children="Wetterdaten"),

        html.Div(
            id="configuration",

            children=[
                drc.NamedDatePickerRange(
                    name="Zeitraum",
                    id="time-period-picker",
                    min_date_allowed=datetime(2000, 1, 1),
                    max_date_allowed=last_time,
                    initial_visible_month=last_time,
                    start_date=last_time - initial_time_period,
                    end_date=last_time
                ),

                drc.NamedDropdown(
                    name="Sensoren",
                    id="sensor-dropdown",
                    options=available_sensors,
                    value=available_sensors[0]["value"],
                    multi=True
                ),

                drc.NamedDropdown(
                    name="Station",
                    id="station-dropdown",
                    options=available_stations,
                    value=available_stations[-1]["value"],
                    multi=True
                ),

                drc.NamedTabs(
                    name="Stationsdaten",
                    id="station-info-tabs",
                    parent_className='station-info-tabs',
                    className='station-info-tabs-container',
                    children=station_info_tabs
                ),
            ]
        ),

        html.Div(
            id="diagram",

            children=[
                dcc.Graph(id="weather-data-graph",
                          config=config_plots,
                          style={"height": "70vh"})
            ]
        )
    ]
)


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
            plot_data.append({"x": time,
                              "y": sensor_data,
                              "name": "{} - {}".format(station_id, sensor_description),
                              "linewidth": 2})

    figure_config = {
        "data": plot_data,
        "layout": {
            "plot_bgcolor": "#282b38",
            "paper_bgcolor": "#282b38",
            "xaxis": {
                "color":  "#a5b1cd",
                "linewidth": 2,
                "gridcolor": "#a5b1cd"
            },
            "yaxis": {
                "color": "#a5b1cd",
                "linewidth": 2,
                "gridcolor": "#a5b1cd"
            },
            "legend": {
                "font": {
                    "color": "#a5b1cd"
                }
            }
        }
    }

    return figure_config


if __name__ == "__main__":
    app.run_server(debug=True)
