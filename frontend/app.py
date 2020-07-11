"""
Run in production with:
`cd ..` (you should be now in the root directory of the content root path of the project (i.e. `weatherstation`)
`export PYTHONPATH=weatherstation`
`gunicorn3 -b 0.0.0.0:8050 frontend.app:server`
"""
import os
from datetime import timedelta, datetime

import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import dateutil.parser
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from math import ceil
import pytz

import frontend.utils.dash_reusable_components as drc
from frontend.utils import plot_config
from frontend.utils.plot_config import get_current_date
from remote_weather_access.remote_weather_access.common.datastructures import BaseStationSensorData, RainSensorData, \
    WindSensorData
from remote_weather_access.remote_weather_access.server.sqldatabase import SQLWeatherDB

db_file_name = os.environ.get("DBFILE", "weather.db")
data_protection_policy_file_path = r"text_content/data-protection-policy.md"
impress_file_path = r"text_content/impress.md"
initial_time_period = timedelta(days=7)
user_time_zone = pytz.timezone("Europe/Berlin")

# this app uses the Bootstrap theme United
app = dash.Dash(__name__,
                meta_tags=[
                    {"name": "viewport", "content": "width=device-width, initial-scale=1"}
                ])
server = app.server
app.title = "Wetterdaten"

config_plots = {"locale": "de"}

# color scheme based on that of the Bootstrap theme United
color_list = [
    "#007bff",
    "#38B44A",
    "#DF382C",
    "#868e96",
    "#772953",
    "#E95420",
    "#772953",
    "#e83e8c",
    "#20c997",
    "#17a2b8"]

graph_front_color = "black"
grid_color = "#a5b1cd"
diagram_font_size = 18
diagram_font_family = "Helvetica Neue, Helvetica, Arial, sans-serif"  # default for Bootstrap
diagram_line_width = 2

# default plot.ly styles
dash_list = ["solid", "dash", "dot", "dashdot"]

secondary_axis_offset = 0.1


def relative_to_file_path(relative_path):
    return os.path.abspath(os.path.dirname(__file__) + os.sep + relative_path)


with open(relative_to_file_path(data_protection_policy_file_path), "r", encoding="utf8") as data_protection_policy_file:
    data_protection_policy_text = data_protection_policy_file.read()

with open(relative_to_file_path(impress_file_path), "r", encoding="utf8") as impress_file:
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
    "xaxis": {
        "color": graph_front_color,
        "linewidth": diagram_line_width,
        "gridcolor": grid_color,
        "tickformatstops": [{
            "dtickrange": [None, 36000000],
            "value": "%d.%m.\n%H:%M"
        }, {
            "dtickrange": [36000000, None],
            "value": "%a\n%d.%m.%Y"
        }],
        "titlefont": {
            "family": diagram_font_family,
            "size": diagram_font_size
        },
        "tickfont": {
            "family": diagram_font_family,
            "size": diagram_font_size
        },
    },
    "legend": {
        "font": {
            "family": diagram_font_family,
            "color": graph_front_color,
            "size": diagram_font_size
        },
        "orientation": "h",
        "xanchor": "center",
        "y": 1.3,
        "x": 0.5
    },
    "margin": dict(l=20, r=20, t=40, b=100)  # in px
}

db_file_parent_path = os.environ.get("DBBASEDIR", relative_to_file_path("test_data"))
db_file_path = db_file_parent_path + os.path.sep + db_file_name
weather_db = SQLWeatherDB(db_file_path)
first_time = weather_db.get_most_early_time_with_data()
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
        dbc.Tab(
            dbc.Col([
                dbc.FormGroup([
                    dbc.Label("Standort", html_for="location_info_{}".format(station_id)),
                    dbc.Input(id="location_info_{}".format(station_id), placeholder=location,
                              disabled=True)
                ]),
                dbc.FormGroup([
                    dbc.Label("Höhe", html_for="height_info_{}".format(station_id)),
                    dbc.Input(id="height_info_{}".format(station_id), placeholder="{} m".format(height),
                              disabled=True)

                ]),
                dbc.FormGroup([
                    dbc.Label("Koordinaten", html_for="coordinates_info_{}".format(station_id)),
                    dbc.Input(id="coordinates_info_{}".format(station_id),
                              placeholder="{} / {}".format(latitude_str, longitude_str),
                              disabled=True)
                ]),
                dbc.FormGroup([
                    dbc.Label("Wetterstation", html_for="device_info_{}".format(station_id)),
                    dbc.Input(id="device_info_{}".format(station_id), placeholder=device,
                              disabled=True)
                ])
            ]),
            label=station_town,
            tab_id=station_id
        )
    )

navbar_component = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink("Home", href="")),
        dbc.NavItem(dbc.NavLink("Datenschutz", href="#", id="open-data-protection-policy")),
        dbc.NavItem(dbc.NavLink("Impressum", href="#", id="open-impress"))
    ],
    brand="Rettigs Wetternetzwerk",
    brand_href="",
    color="primary",
    dark=True,
    fluid=True,
    expand="lg"
)

date_picker_card = \
    dbc.Card(
        [
            html.H2("Zeitraum"),
            html.Div(
                dcc.DatePickerRange(
                    id="time-period-picker",
                    min_date_allowed=first_time,
                    display_format="DD.MM.YYYY",
                    stay_open_on_select=True,
                    start_date_placeholder_text="Startdatum",
                    end_date_placeholder_text="Enddatum",
                    first_day_of_week=1
                )
            )
        ], body=True
    )

sensor_dropdown_card = \
    dbc.Card(
        [
            html.H2("Sensoren"),
            html.Div(
                dcc.Dropdown(
                    id="sensor-dropdown",
                    placeholder="Auswählen ...",
                    options=available_sensors,
                    value=default_selected_sensor_ids,
                    searchable=False,
                    multi=True
                )
            )
        ], body=True
    )

station_dropdown_card = \
    dbc.Card(
        [
            html.H2("Stationen"),
            html.Div(
                dcc.Dropdown(
                    id="station-dropdown",
                    placeholder="Auswählen ...",
                    options=available_stations,
                    value=available_stations[-1]["value"],
                    searchable=False,
                    multi=True
                )
            )

        ], body=True
    )

station_data_card = \
    dbc.Card([
        html.H2("Stationsdaten"),
        dbc.Tabs(
            station_info_tabs,
            id="station-data-tab"
        )
    ], body=True)

app.layout = dbc.Container(
    fluid=True,
    children=[
        dcc.Location(id='url', refresh=True),

        drc.ModalDialog(
            id="data-protection-policy",
            dialog_content=data_protection_policy_text
        ),

        drc.ModalDialog(
            id="impress",
            dialog_content=impress_text
        ),

        dbc.Row(
            [
                dbc.Col(
                    navbar_component,
                    width=12
                )
            ]
        ),

        dbc.Row(
            [
                dbc.Col(
                    id="configuration",
                    children=[
                        date_picker_card,
                        sensor_dropdown_card,
                        station_dropdown_card,
                        station_data_card
                    ],
                    width=12,
                    lg=4
                ),

                dbc.Col(
                    dbc.Spinner(dcc.Graph(id="weather-data-graph", config=config_plots, className="diagram")),
                    width="auto",
                    lg=8,
                    style={"minWidth": "800px"}
                )
            ]
        ),

        dbc.Row(
            [dbc.Col(
                html.P(children="Copyright (C) 2020 Ralf Rettig"),
                width=12)
            ]
        )
    ]
)


@app.callback([Output('time-period-picker', 'max_date_allowed'),
               Output('time-period-picker', 'end_date'),
               Output('time-period-picker', 'start_date')],
              [Input('url', 'pathname')])
def display_page(pathname):
    last_time = get_current_date(user_time_zone)
    return last_time, last_time, last_time - initial_time_period


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
    Output("station-data-tab", "active_tab"),
    [Input(component_id="station-dropdown", component_property="value")]
)
def select_station_info_tab(chosen_stations):
    if isinstance(chosen_stations, str):
        chosen_stations = [chosen_stations]

    if len(chosen_stations) > 0:
        open_tab_id = chosen_stations[0]
    else:
        open_tab_id = ""

    return open_tab_id


@app.callback(
    Output("weather-data-graph", "figure"),
    [Input(component_id="time-period-picker", component_property="start_date"),
     Input(component_id="time-period-picker", component_property="end_date"),
     Input(component_id="station-dropdown", component_property="value"),
     Input(component_id="sensor-dropdown", component_property="value")]
)
def update_weather_plot(start_time_str, end_time_str, chosen_stations, sensors):
    start_time, end_time = determine_start_and_end_times(end_time_str, start_time_str)
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

    data = {}
    for station_id in chosen_stations:
        data[station_id] = weather_db.get_data_in_time_range(station_id, start_time, end_time)
    left_main_axis_pos, right_main_axis_pos, min_max_limits, num_ticks = determine_plot_axis_setup(chosen_stations,
                                                                                                   data, sensors)

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

            time = [line.get_time() for line in data[station_id]]
            sensor_data = [float(line.get_sensor_value(sensor_tuple)) for line in data[station_id]]
            if len(data[station_id]) > 0:
                sensor_unit = data[station_id][0].get_sensor_unit(sensor_tuple)
                plot_data.append(create_sensor_plot_data(color_index, dash_index, sensor_data, sensor_description,
                                                         sensor_index, station_id, time))

                if sensor_index == 0:
                    axis_name = "yaxis"
                else:
                    axis_name = "yaxis{}".format(sensor_index + 1)
                figure_layout[axis_name] = create_plot_axis_layout(color_index, min_max_limits, num_ticks,
                                                                   sensor_description, sensor_tuple, sensor_unit)
                configure_plot_axis_layout(axis_name, left_main_axis_pos, right_main_axis_pos, sensor_index)

    if len(plot_data) == 0:
        create_empty_plot_axis_layout()

    figure_config = {
        "data": plot_data,
        "layout": figure_layout
    }

    return figure_config


def determine_start_and_end_times(end_time_str, start_time_str):
    actual_start_time = dateutil.parser.parse(start_time_str)
    start_time = datetime(actual_start_time.year, actual_start_time.month, actual_start_time.day)
    actual_end_time = dateutil.parser.parse(end_time_str)
    end_time = datetime(actual_end_time.year, actual_end_time.month, actual_end_time.day) + timedelta(days=1)
    return start_time, end_time


def create_empty_plot_axis_layout():
    current_date = get_current_date(user_time_zone)

    figure_layout["yaxis"] = {
        "title": "",
        "tickfont": {
            "color": graph_front_color,
            "size": diagram_font_size
        },
        "linecolor": graph_front_color,
        "zeroline": False,
        "gridcolor": grid_color,
        "range": [0, 100]
    }
    figure_layout["xaxis"]["range"] = [current_date - initial_time_period, current_date]
    figure_layout["xaxis"]["type"] = "date"


def create_sensor_plot_data(color_index, dash_index, sensor_data, sensor_description, sensor_index, station_id, time):
    return {"x": time,
            "y": sensor_data,
            "name": "{} - {}".format(station_id, sensor_description),
            "line": {
                "color": color_list[color_index],
                "width": diagram_line_width,
                "dash": dash_list[dash_index]
            },
            "yaxis": "y{}".format(sensor_index + 1),
            "hoverlabel": {
                "namelength": "-1",
                "font": {
                    "family": diagram_font_family,
                    "size": diagram_font_size
                }
            }
            }


def configure_plot_axis_layout(axis_name, left_main_axis_pos, right_main_axis_pos, sensor_index):
    if sensor_index == 0:
        figure_layout[axis_name]["gridcolor"] = grid_color
    if sensor_index > 0:
        figure_layout[axis_name]["anchor"] = "free"
        figure_layout[axis_name]["overlaying"] = "y"
        figure_layout[axis_name]["showgrid"] = False
    if sensor_index % 2 == 0:
        figure_layout[axis_name]["side"] = "left"
        figure_layout[axis_name]["position"] = left_main_axis_pos - sensor_index / 2 * secondary_axis_offset
    else:
        figure_layout[axis_name]["side"] = "right"
        figure_layout[axis_name]["position"] = right_main_axis_pos + \
                                               (sensor_index - 1) / 2 * secondary_axis_offset


def create_plot_axis_layout(color_index, min_max_limits, num_ticks, sensor_description, sensor_tuple, sensor_unit):
    return {
        "title": "{} / {}".format(sensor_description, sensor_unit),
        "titlefont": {
            "family": diagram_font_family,
            "color": color_list[color_index],
            "size": diagram_font_size
        },
        "tickfont": {
            "family": diagram_font_family,
            "color": color_list[color_index],
            "size": diagram_font_size
        },
        "linecolor": color_list[color_index],
        "linewidth": diagram_line_width,
        "zeroline": False,
        "nticks": num_ticks,
        "range": [min_max_limits[sensor_tuple]["min"], min_max_limits[sensor_tuple]["max"]]
    }


def determine_plot_axis_setup(chosen_stations, data, sensors):
    if len(chosen_stations) > 0 and len(sensors) > 0:
        _num_axis_on_left = ceil(len(sensors) / 2)
        _num_axis_on_right = ceil((len(sensors) - 1) / 2)
        left_main_axis_pos = _num_axis_on_left * secondary_axis_offset
        right_main_axis_pos = 1 - _num_axis_on_right * secondary_axis_offset

        figure_layout["xaxis"]["domain"] = [left_main_axis_pos, right_main_axis_pos]

        _min_max_sensors = {}
        for internal_sensor_id in sensors:
            _sensor_tuple = sensor_mapping[internal_sensor_id]["id"]
            _min_data = float("inf")
            _max_data = float("-inf")
            for station_index, station_id in enumerate(chosen_stations):
                if len(data[station_id]) > 0:
                    sensor_data = [float(line.get_sensor_value(_sensor_tuple)) for line in data[station_id]]
                    _min_data = min(_min_data, min(sensor_data))
                    _max_data = max(_max_data, max(sensor_data))
            if _min_data != float("inf") and _max_data != float("-inf"):
                _min_max_sensors[_sensor_tuple] = {"min": _min_data, "max": _max_data}

        if len(_min_max_sensors) > 0:
            num_ticks, min_max_limits = plot_config.get_scalings(_min_max_sensors)
        else:
            num_ticks = 0
            min_max_limits = None

        return left_main_axis_pos, right_main_axis_pos, min_max_limits, num_ticks
    else:
        return float("inf"), float("inf"), None, 0


if __name__ == "__main__":
    app.run_server(host="0.0.0.0", debug=True)
