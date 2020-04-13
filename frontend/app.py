"""
Run in production with: `gunicorn3 -b 0.0.0.0:8000 app:server`
"""
import os
from datetime import timedelta, datetime
from math import ceil

import dash
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc

import frontend.utils.dash_reusable_components as drc
import dash_core_components as dcc
import dash_html_components as html
import dateutil.parser

from remote_weather_access.remote_weather_access.common.datastructures import BaseStationSensorData, RainSensorData, \
    WindSensorData
from remote_weather_access.remote_weather_access.server.sqldatabase import SQLWeatherDB
from frontend.utils import plot_config


db_file_name = os.environ.get("DBFILE", r"frontend/test_data/weather.db")
data_protection_policy_file_path = r"assets/data-protection-policy.md"
impress_file_path = r"assets/impress.md"
initial_time_period = timedelta(days=7)

db_file_parent_path = os.environ.get("BASEDIR", os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server
app.title = "Wetterdaten"

config_plots = {"locale": "de"}

color_list = [
    "#1f77b4",  # muted blue
    "#2ca02c",  # cooked asparagus green
    "#d62728",  # brick red
    "#7f7f7f",  # middle gray
    "#9467bd",  # muted purple
    "#ff7f0e",  # safety orange
    "#8c564b",  # chestnut brown
    "#e377c2",  # raspberry yogurt pink
    "#bcbd22",  # curry yellow-green
    "#17becf"]  # blue-teal

background_color = "#161a28"
graph_front_color = "#a5b1cd"
diagram_font_size = 14

# default plot.ly styles
dash_list = ["solid", "dash", "dot", "dashdot"]

SECONDARY_AXIS_OFFSET = 0.07

with open(data_protection_policy_file_path, "r", encoding="utf8") as data_protection_policy_file:
    data_protection_policy_text = data_protection_policy_file.read()

with open(impress_file_path, "r", encoding="utf8") as impress_file:
    impress_text = impress_file.read()

sensor_mapping = {"pressure": {"description": "Luftdruck",
                               "id": (BaseStationSensorData.BASE_STATION, BaseStationSensorData.PRESSURE)},
                  "uv": {"description": "UV",
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

default_selected_sensor_ids = ["pressure", "rain_cumulated", "OUT1_temp", "OUT1_humid"]

figure_layout = {
    "plot_bgcolor": background_color,
    "paper_bgcolor": background_color,
    "xaxis": {
        "color": graph_front_color,
        "linewidth": 2,
        "gridcolor": graph_front_color,
        "tickformatstops": [{
            "dtickrange": [None, 36000000],
            "value": "%d.%m.\n%H:%M"
        }, {
            "dtickrange": [36000000, None],
            "value": "%a\n%d.%m.%Y"
        }],
        "titlefont": {
            "size": diagram_font_size
        },
        "tickfont": {
            "size": diagram_font_size
        },
    },
    "legend": {
        "font": {
            "color": graph_front_color,
            "size": diagram_font_size
        },
        "orientation": "h"
    }
}

db_file_path = db_file_parent_path + os.path.sep + db_file_name
weather_db = SQLWeatherDB(db_file_path)
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
        dcc.Location(id='url', refresh=False),

        html.Div(
            id="banner",
            className="banner",
            children=[
                html.Div(
                    id="banner-text",
                    children=[
                        html.H5(
                            className="banner-item",
                            children=["Wetterdaten"]),
                        html.H6(
                            className="banner-item",
                            children=["Rettigs Wetternetzwerk"])
                    ]
                ),
                html.Div(
                    id="link-container",
                    children=[
                        html.Div(id="link-container-empty-placeholder"),
                        html.Div(
                            id="links",
                            children=[
                                drc.ModalDialog(
                                    id="data-protection-policy",
                                    button_text="Datenschutz",
                                    dialog_content=data_protection_policy_text,
                                    className="link-item"),
                                drc.ModalDialog(
                                    id="impress",
                                    button_text="Impressum",
                                    dialog_content=impress_text,
                                    className="link-item")
                            ]
                        )
                    ]
                )
            ]
        ),

        html.Div(
            id="content",
            children=[
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
                            placeholder="Auswählen ...",
                            options=available_sensors,
                            value=default_selected_sensor_ids,
                            multi=True
                        ),

                        drc.NamedDropdown(
                            name="Station",
                            id="station-dropdown",
                            placeholder="Auswählen ...",
                            options=available_stations,
                            value=available_stations[-1]["value"],
                            multi=True
                        ),

                        drc.NamedTabs(
                            name="Stationsdaten",
                            id="station-info-tabs",
                            parent_className="station-info-tabs",
                            className="station-info-tabs-container",
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
        ),

        html.Div(
            id="copyright-notice",
            children=[
                html.P(
                    className="label",
                    children=["Copyright (C) 2020 Ralf Rettig"]
                )
            ]
        )
    ]
)


@app.callback(
    Output("data-protection-policy-dialog", "is_open"),
    [Input("open-data-protection-policy", "n_clicks"), Input("close-data-protection-policy", "n_clicks")],
    [State("data-protection-policy-dialog", "is_open")],
)
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open


@app.callback(
    Output("impress-dialog", "is_open"),
    [Input("open-impress", "n_clicks"), Input("close-impress", "n_clicks")],
    [State("impress-dialog", "is_open")],
)
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open


@app.callback(
    Output("station-info-tabs", "value"),
    [Input(component_id="station-dropdown", component_property="value")]
)
def update_station_info_tabs(chosen_stations):
    if isinstance(chosen_stations, str):
        chosen_stations = [chosen_stations]

    if len(chosen_stations) > 0:
        return chosen_stations[-1]
    else:
        raise PreventUpdate


@app.callback(dash.dependencies.Output("station-dropdown", "value"),
              [dash.dependencies.Input("url", "pathname")])
def display_page(pathname):
    if pathname is None:
        raise PreventUpdate

    provided_station_id = pathname.replace("/", "").upper()

    if provided_station_id in weather_db.get_stations():
        return provided_station_id
    elif len(provided_station_id) == 0:
        return available_stations[-1]["value"]
    else:
        raise PreventUpdate


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

    if "range" in figure_layout["xaxis"]:
        del figure_layout["xaxis"]["range"]
    if "type" in figure_layout["xaxis"]:
        del figure_layout["xaxis"]["type"]

    if len(chosen_stations) > 0 and len(sensors) > 0:
        num_axis_on_left = ceil(len(sensors) / 2)
        num_axis_on_right = ceil((len(sensors) - 1) / 2)
        left_main_axis_pos = num_axis_on_left * SECONDARY_AXIS_OFFSET
        right_main_axis_pos = 1 - num_axis_on_right * SECONDARY_AXIS_OFFSET

        figure_layout["xaxis"]["domain"] = [left_main_axis_pos, right_main_axis_pos]

        min_max_sensors = {}
        for internal_sensor_id in sensors:
            sensor_tuple = sensor_mapping[internal_sensor_id]["id"]
            min_data = float("inf")
            max_data = float("-inf")
            for station_index, station_id in enumerate(chosen_stations):
                data = weather_db.get_data_in_time_range(station_id, start_time, end_time)
                sensor_data = [float(line.get_sensor_value(sensor_tuple)) for line in data]
                min_data = min(min_data, min(sensor_data))
                max_data = max(max_data, max(sensor_data))
            min_max_sensors[sensor_tuple] = {"min": min_data, "max": max_data}

        num_ticks, min_max_limits = plot_config.get_scalings(min_max_sensors)

    plot_data = []
    color_index = -1
    for sensor_index, internal_sensor_id in enumerate(sensors):
        color_index += 1
        if color_index >= len(color_list):
            color_index = 0

        sensor_tuple = sensor_mapping[internal_sensor_id]["id"]
        sensor_description = sensor_mapping[internal_sensor_id]["description"]
        dash_index = -1
        for station_index, station_id in enumerate(chosen_stations):
            dash_index += 1
            if dash_index >= len(dash_list):
                dash_index = 0

            data = weather_db.get_data_in_time_range(station_id, start_time, end_time)
            time = [line.get_time() for line in data]
            sensor_data = [float(line.get_sensor_value(sensor_tuple)) for line in data]
            if len(data) > 0:
                sensor_unit = data[0].get_sensor_unit(sensor_tuple)
                plot_data.append({"x": time,
                                  "y": sensor_data,
                                  "name": "{} - {}".format(station_id, sensor_description),
                                  "line": {
                                      "color": color_list[color_index],
                                      "width": 2,
                                      "dash": dash_list[dash_index]
                                  },
                                  "yaxis": "y{}".format(sensor_index + 1),
                                  "hoverlabel": {
                                      "namelength": "-1"
                                  }
                                  })

                if sensor_index == 0:
                    axis_name = "yaxis"
                else:
                    axis_name = "yaxis{}".format(sensor_index + 1)
                figure_layout[axis_name] = {
                    "title": "{} / {}".format(sensor_description, sensor_unit),
                    "titlefont": {
                        "color": color_list[color_index],
                        "size": diagram_font_size
                    },
                    "tickfont": {
                        "color": color_list[color_index],
                        "size": diagram_font_size
                    },
                    "linecolor": color_list[color_index],
                    "zeroline": False,
                    "nticks": num_ticks,
                    "range": [min_max_limits[sensor_tuple]["min"], min_max_limits[sensor_tuple]["max"]]
                }

                if sensor_index == 0:
                    figure_layout[axis_name]["gridcolor"] = graph_front_color

                if sensor_index > 0:
                    figure_layout[axis_name]["anchor"] = "free"
                    figure_layout[axis_name]["overlaying"] = "y"
                    figure_layout[axis_name]["showgrid"] = False

                if sensor_index % 2 == 0:
                    figure_layout[axis_name]["side"] = "left"
                    figure_layout[axis_name]["position"] = left_main_axis_pos - sensor_index / 2 * SECONDARY_AXIS_OFFSET
                else:
                    figure_layout[axis_name]["side"] = "right"
                    figure_layout[axis_name]["position"] = right_main_axis_pos +\
                                                           (sensor_index - 1) / 2 * SECONDARY_AXIS_OFFSET
    if len(plot_data) == 0:
        figure_layout["yaxis"] = {
            "title": "",
            "tickfont": {
                "color": graph_front_color,
                "size": diagram_font_size
            },
            "linecolor": graph_front_color,
            "zeroline": False,
            "gridcolor": graph_front_color,
            "range": [0, 100]
        }

        figure_layout["xaxis"]["range"] = [last_time - initial_time_period, last_time]
        figure_layout["xaxis"]["type"] = "date"

    figure_config = {
        "data": plot_data,
        "layout": figure_layout
    }

    return figure_config


if __name__ == "__main__":
    app.run_server(debug=True)
