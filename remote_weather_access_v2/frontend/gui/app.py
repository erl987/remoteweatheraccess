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
from utils import plot_config


db_file_name = r"C:\Users\Ralf\Documents\code\remote-weather-access\remote_weather_access_v2\frontend\gui\weather.db"
initial_time_period = timedelta(days=7)

app = dash.Dash(__name__)

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

background_color = "#282b38"
graph_front_color = "#a5b1cd"

# default plot.ly styles
dash_list = ["solid", "dash", "dot", "dashdot"]

SECONDARY_AXIS_OFFSET = 0.07

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
        }]
    },
    "legend": {
        "font": {
            "color": graph_front_color
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

    min_max_sensors = {}
    for internal_sensor_id in sensors:
        sensor_tuple = sensor_mapping[internal_sensor_id]["id"]
        min_data = float("inf")
        max_data = float("-inf")
        for station_index, station_id in enumerate(chosen_stations):
            data = weather_db.get_data_in_time_range(station_id, start_time, end_time)
            sensor_data = [float(line.get_sensor_value(sensor_tuple)) for line in data]
            min_data = min(sensor_data)
            max_data = max(sensor_data)
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
                        "color": color_list[color_index]
                    },
                    "tickfont": {
                        "color": color_list[color_index]
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

    figure_config = {
        "data": plot_data,
        "layout": figure_layout
    }

    return figure_config


if __name__ == "__main__":
    app.run_server(debug=True)
