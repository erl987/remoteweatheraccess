# RemoteWeatherAccess - Weather network connecting to remote stations
# Copyright(C) 2013-2016 Ralf Rettig (info@personalfme.de)
#
# This program is free software: you can redistribute it and / or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.If not, see <http://www.gnu.org/licenses/>

from weathernetwork.common.datastructures import CombiSensorData, BaseStationSensorData, RainSensorData
from weathernetwork.common import utilities
import matplotlib
from weathernetwork.server.sqldatabase import SQLWeatherDB

matplotlib.use('Agg')
from mpl_toolkits.axes_grid1 import host_subplot
import mpl_toolkits.axisartist as aa
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as ticker
import matplotlib.font_manager as fonts
import datetime
from datetime import datetime as dt
from datetime import timedelta


_DELTA = 70  # assumed width of a single y-axis label set (in pixel)


def get_last_n_days_data(num_days, db_file_name, station_id, last_time=None):
    """
    Returns the data of the latest n days from the specified database.

    :param num_days:            the data for the last 'num_days' before the last entry in the data file will be
                                returned.
    :type num_days:             int
    :param db_file_name:        name and path of the SQL-database file
    :type db_file_name:         string
    :param station_id:          id of the required station
    :type station_id:           string
    :param last_time:           timepoint of the last required data. If omitted, the last time of the data is used.
    :type last_time:            datetime.datetime
    :return:                    weather dataset of the last 'num_days' before the the last entry
                                containing all sensors stored
    :rtype:                     list of common.datastructures.WeatherStationDataset
    """
    # Read the required data from the database
    if not last_time:
        last_time = datetime.datetime.utcnow()
    first_time = last_time - timedelta(days=num_days)

    weather_db = SQLWeatherDB(db_file_name)
    data = weather_db.get_data_in_time_range(station_id, first_time, last_time)

    return data


def get_scalings(min_max_sensors):
    """
    Obtains the minimum and maximum scalings of the y-axis for the sensors.

    :param min_max_sensors:     containing the minimum and maximum values of the sensors in the graph.
                                example: {"('baseStation', 'pressure')": {'max': 1018.4, 'min': 1018.4}}
    :type min_max_sensors:      dict(string, dict(string, float))
    :return:                    number of ticks of the y-axis.
    :rtype:                     int
    :return:                    containing the minimum and maximum values for all sensors on the axis.
                                example: {"('baseStation', 'pressure')": {'max': 1018.4, 'min': 1018.4}}
    :rtype:                     dict(string, dict(string, float))
    """
    delta_temp = 5.0  # degree C by definition
    delta_p = 5.0  # hPa by definition

    all_num_ticks = []
    # determine number of ticks
    for key, sensor in min_max_sensors.items():
        if CombiSensorData.TEMPERATURE in key:
            # temperatures should have an identical scaling
            curr_min_temp = utilities.floor_to_n(sensor['min'], delta_temp)
            if 'min_temp' not in locals() or curr_min_temp < min_temp:
                min_temp = curr_min_temp
            curr_max_temp = utilities.ceil_to_n(sensor['max'], delta_temp)
            if 'max_temp' not in locals() or curr_max_temp > max_temp:
                max_temp = curr_max_temp
            all_num_ticks.append(int((max_temp - min_temp) / delta_temp + 1))
        elif RainSensorData.RAIN in key:
            if sensor['max'] < 20:
                delta_rain = 2.5
            elif sensor['max'] < 40:
                delta_rain = 5.0
            elif sensor['max'] < 80:
                delta_rain = 10.0
            elif sensor['max'] < 160:
                delta_rain = 20.0
            else:
                delta_rain = 50.0
            max_rain_counter = utilities.ceil_to_n(sensor['max'], delta_rain)
            all_num_ticks.append(int((max_rain_counter - 0) / delta_rain + 1))
        elif BaseStationSensorData.PRESSURE in key:
            min_p = utilities.floor_to_n(sensor['min'], delta_p)
            max_p = utilities.ceil_to_n(sensor['max'], delta_p)
            all_num_ticks.append(int((max_p - min_p) / delta_p + 1))

    if len(all_num_ticks) == 0:
        all_num_ticks.append(5)  # default value if no special sensors are present

    num_ticks = max(all_num_ticks)

    min_max_axis = dict()
    for key, sensor in min_max_sensors.items():
        if CombiSensorData.TEMPERATURE in key:
            # temperature minimum is always the next lower temperature dividable by 5 degree C (already calculated)
            max_temp = min_temp + delta_temp * (num_ticks - 1)
            min_max_axis[key] = {'min': min_temp, 'max': max_temp}
        elif CombiSensorData.HUMIDITY in key:
            # humidity is always in the range from 0 - 100 pct
            min_max_axis[key] = {'min': 0, 'max': 100}
        elif RainSensorData.RAIN in key:
            # rain counter minimum is always 0 mm
            max_rain_counter = 0 + delta_rain * (num_ticks - 1)
            min_max_axis[key] = {'min': 0, 'max': max_rain_counter}
        elif BaseStationSensorData.PRESSURE in key:
            # pressure minimum is always the next lower pressure dividable by 5 hPa (already calculated)
            max_p = min_p + delta_p * (num_ticks - 1)
            min_max_axis[key] = {'min': min_p, 'max': max_p}
        else:
            # all other sensors are scaled by the min/max values
            min_max_axis[key] = {'min': sensor['min'], 'max': sensor['max']}

    return num_ticks, min_max_axis


def plot_of_last_n_days(num_days, db_file_name, station_id, sensors_to_plot, graph_folder, graph_file_name,
                        is_save_to_fig, last_time=None):
    """
    Plots the weather data of the last n days from all data available in a defined folder.

    :param num_days:            last 'num_days' before the last entry in the data file will be plotted
    :type num_days:             int
    :param db_file_name:        name of the SQL weather database file
    :type db_file_name:         string
    :param station_id:          id of the station
    :type station_id:           string
    :param sensors_to_plot:     sensors to be plotted (format: [('baseStation', 'pressure'), ...])
    :type sensors_to_plot:      list of tuple
    :param graph_folder:        base folder where the graph plot file will be stored, the file is stored in a
                                subfolder named by the station ID
    :type graph_folder:         string
    :param graph_file_name:     name of the graph plot file. Any graphics format supported by MATPLOTLIB can be used,
                                for example '.svg' or '.png'.
    :type graph_file_name:      string
    :param is_save_to_fig:      flag stating if the graph will be written to file (True) or to a GUI (False)
    :type is_save_to_fig:       boolean
    :param last_time:           timepoint of the last required data. If omitted, the last time of the data is used.
    :type last_time:            datetime.datetime
    :return:                    number of datasets plotted, timepoint of the beginning of the plotted dataset,
                                timepoint of the end of the plotted dataset
    :rtype:                     tuple(int, datetime.datetime, datetime.datetime)
    """
    # Find data for the last n days in the data folder
    data = get_last_n_days_data(num_days, db_file_name, station_id, last_time)

    # Calculate secondary y-axis positions
    y_axis_pos = []
    for index, sensor in enumerate(sensors_to_plot):
        if index % 2 == 0:
            y_axis_pos.append(('left', -index / 2 * _DELTA))
        else:
            y_axis_pos.append(('right', (index - 1) / 2 * _DELTA))

    # Generate figure
    plt.figure(figsize=[13.5, 6])
    ax = [host_subplot(111, axes_class=aa.Axes)]
    for index, sensor in enumerate(sensors_to_plot):
        if index > 0:
            ax.append(ax[0].twinx())
            ax[-1].axis['right'].set_visible(False)
            ax[-1].axis[y_axis_pos[index][0]] = \
                ax[-1].new_fixed_axis(y_axis_pos[index][0], offset=(y_axis_pos[index][1], 0))

    # Plot graphs for the required data
    times = [line.get_time() for line in data]
    min_max_sensors = dict()
    for index, sensor in enumerate(sensors_to_plot):
        # Plot data
        plot_data = [float(line.get_sensor_value(sensor)) for line in data]
        ax[index].plot(times, plot_data, label=str(sensor), lw=2.0)
        min_max_sensors[str(sensor)] = {'min': min(plot_data), 'max': max(plot_data)}

        # Set data axis settings
        sensor_color = ax[index].lines[0].get_color()
        ax[index].set_ylabel(data[0].get_sensor_description(sensor) + ' / ' + data[0].get_sensor_unit(sensor),
                             color=sensor_color)
        ax[index].axis[y_axis_pos[index][0]].label.set_font_properties(fonts.FontProperties(weight='bold', size=13))
        ax[index].yaxis.set_minor_locator(ticker.AutoMinorLocator(5))
        ax[index].axis[y_axis_pos[index][0]].minor_ticks.set_color(sensor_color)
        ax[index].axis[y_axis_pos[index][0]].major_ticklabels.set_color(sensor_color)
        ax[index].axis[y_axis_pos[index][0]].major_ticklabels.set_fontproperties(fonts.FontProperties(weight='bold'))
        ax[index].axis[y_axis_pos[index][0]].major_ticks.set_color(sensor_color)
        ax[index].axis[y_axis_pos[index][0]].line.set_color(sensor_color)
        ax[index].axis[y_axis_pos[index][0]].line.set_linewidth(2.0)

    # Set appropriate scaling of the y-axis
    num_ticks, min_max_axis = get_scalings(min_max_sensors)
    for index, sensor in enumerate(sensors_to_plot):
        ax[index].yaxis.set_major_locator(ticker.LinearLocator(numticks=num_ticks))
        ax[index].set_ylim(min_max_axis[str(sensor)]['min'], min_max_axis[str(sensor)]['max'])

    # Configure date axis and grid lines
    ax[0].xaxis.set_minor_locator(mdates.HourLocator(byhour=[0, 6, 12, 18]))
    ax[0].grid(True, which='minor', color='gray', linestyle='dotted', lw=0.5)
    ax[0].axis['bottom'].minor_ticks.set_ticksize(5)
    ax[0].axis['top'].minor_ticks.set_ticksize(5)
    ax[0].xaxis.set_major_locator(mdates.DayLocator())
    ax[0].xaxis.set_major_formatter(mdates.DateFormatter('%a\n%d.%m.%y'))
    ax[-1].grid(True, which='major', color='k', linestyle='-', lw=1.0)
    ax[0].axis['bottom'].major_ticklabels.set_pad(20)
    ax[0].axis['bottom'].major_ticklabels.set_horizontalalignment('left')
    ax[0].axis['bottom'].major_ticklabels.set_fontproperties(fonts.FontProperties(weight='bold', size=13))

    # Add information on last data
    plt.text(0.99, 0.999, 'Letzte Daten: ' + dt.strftime(times[-1], '%d.%m.%Y %H:%M'), horizontalalignment='right',
             verticalalignment='bottom', transform=ax[0].transAxes,
             fontproperties=fonts.FontProperties(weight='bold', size=12))
    plt.tight_layout()

    # Save plot to file
    if is_save_to_fig:
        plt.savefig(graph_folder + '/' + station_id + '/' + graph_file_name)
    else:
        plt.show()

    # Set return data
    if len(times) > 0:
        first_plot_time = times[0]
        last_plot_time = times[-1]
    else:
        first_plot_time = dt(datetime.MINYEAR, 1, 1, 0, 0, 0, 0)
        last_plot_time = dt(datetime.MINYEAR, 1, 1, 0, 0, 0, 0)

    return len(times), first_plot_time, last_plot_time
