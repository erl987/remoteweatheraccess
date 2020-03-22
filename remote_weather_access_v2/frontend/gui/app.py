from datetime import timedelta, datetime
from math import ceil

import dash
from dash.dependencies import Input, Output
from dash.exceptions import PreventUpdate

import utils.dash_reusable_components as drc
import dash_core_components as dcc
import dash_html_components as html
import dateutil

from remote_weather_access.common.datastructures import BaseStationSensorData, RainSensorData, WindSensorData
from remote_weather_access.server.sqldatabase import SQLWeatherDB


db_file_name = r"C:\Users\Ralf\Documents\code\remote-weather-access\remote_weather_access_v2\frontend\gui\weather.db"
initial_time_period = timedelta(days=7)

app = dash.Dash(__name__)

config_plots = {"locale": "de"}

# default plot.ly colors
color_list = [
    "#1f77b4",  # muted blue
    "#ff7f0e",  # safety orange
    "#2ca02c",  # cooked asparagus green
    "#d62728",  # brick red
    "#9467bd",  # muted purple
    "#8c564b",  # chestnut brown
    "#e377c2",  # raspberry yogurt pink
    "#7f7f7f",  # middle gray
    "#bcbd22",  # curry yellow-green
    "#17becf"]  # blue-teal

SECONDARY_AXIS_OFFSET = 0.07

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

figure_layout = {
    "plot_bgcolor": "#282b38",
    "paper_bgcolor": "#282b38",
    "xaxis": {
        "tickformat": "%a\n%d.%m.%Y",
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

weather_db = SQLWeatherDB(db_file_name)
last_time = datetime.min
for station_id in weather_db.get_stations():
    last_time = max(last_time, weather_db.get_most_recent_time_with_data(station_id))
combi_sensor_ids, combi_sensor_descriptions = weather_db.get_combi_sensors()
for id in combi_sensor_ids:
    if id == "IN":
        description = "innen"
    elif id.startswith("OUT"):
        description = "außen"
    else:
        description = "unknown"
    sensor_mapping["{}_temp".format(id)] = {"description": "Temperatur {}".format(description),
                                            "id": (id, "temperature")}
    sensor_mapping["{}_humid".format(id)] = {"description": "Luftfeuchte {}".format(description),
                                             "id": (id, "humidity")}

available_sensors = []
for internal_sensor_id, sensor_info in sensor_mapping.items():
    available_sensors.append({"label": sensor_info["description"], "value": internal_sensor_id})

available_stations = []
station_info_tabs = []
for station_id in weather_db.get_stations():
    station_metadata = weather_db.get_station_metadata(station_id)
    device = station_metadata.get_device_info()
    location = station_metadata.get_location_info()
    latitude, longitude, height = station_metadata.get_geo_info()
    splitted_location_info = location.split("/")
    station_town = splitted_location_info[0]
    available_stations.append({"label": station_town, "value": station_id})
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
            className="station-info-tab--selector",
            label=station_town,
            value=station_id,
            selected_className="station-info-tab--selected",
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
                    start_date=last_time - initial_time_period,
                    end_date=last_time,
                    display_format="DD.MM.YYYY",
                    stay_open_on_select=True,
                    start_date_placeholder_text="Startdatum",
                    end_date_placeholder_text="Enddatum",
                    first_day_of_week=1
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
                          config=config_plots)
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

    if end_time < start_time:
        raise PreventUpdate

    if isinstance(chosen_stations, str):
        chosen_stations = [chosen_stations]
    if isinstance(sensors, str):
        sensors = [sensors]

    num_axis_on_left = ceil(len(sensors) / 2)
    num_axis_on_right = ceil((len(sensors) - 1) / 2)
    left_main_axis_pos = num_axis_on_left * SECONDARY_AXIS_OFFSET
    right_main_axis_pos = 1 - num_axis_on_right * SECONDARY_AXIS_OFFSET

    figure_layout["xaxis"]["domain"] = [left_main_axis_pos, right_main_axis_pos]

    plot_data = []
    color_index = 0
    for sensor_index, internal_sensor_id in enumerate(sensors):
        color_index += 1
        if color_index >= len(color_list):
            color_index = 0

        sensor_tuple = sensor_mapping[internal_sensor_id]["id"]
        sensor_description = sensor_mapping[internal_sensor_id]["description"]
        for station_id in chosen_stations:
            data = weather_db.get_data_in_time_range(station_id, start_time, end_time)
            time = [line.get_time() for line in data]
            sensor_data = [float(line.get_sensor_value(sensor_tuple)) for line in data]
            plot_data.append({"x": time,
                              "y": sensor_data,
                              "name": "{} - {}".format(station_id, sensor_description),
                              "line": {
                                  "color": color_list[color_index],
                                  "width": 2,
                              },
                              "yaxis": "y{}".format(sensor_index + 1)})

            if sensor_index == 0:
                axis_name = "yaxis"
            else:
                axis_name = "yaxis{}".format(sensor_index + 1)
            figure_layout[axis_name] = {
                "title": sensor_description,
                "titlefont": {
                    "color": color_list[color_index]
                },
                "tickfont": {
                    "color": color_list[color_index]
                },
                "linecolor": color_list[color_index]
            }

            if sensor_index == 0:
                figure_layout[axis_name]["gridcolor"] = "#a5b1cd"

            if sensor_index > 0:
                figure_layout[axis_name]["anchor"] = "free"
                figure_layout[axis_name]["overlaying"] = "y"

            if sensor_index % 2 == 0:
                figure_layout[axis_name]["side"] = "left"
                figure_layout[axis_name]["position"] = left_main_axis_pos - sensor_index / 2 * SECONDARY_AXIS_OFFSET
            else:
                figure_layout[axis_name]["side"] = "right"
                figure_layout[axis_name]["position"] = right_main_axis_pos +\
                                                       (sensor_index - 1) / 2 * SECONDARY_AXIS_OFFSET

    figure_config = {
        "data": plot_data,
        "layout": figure_layout
    }

    return figure_config


if __name__ == "__main__":
    app.run_server(debug=True)
