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

from weathernetwork.common.sensor import CombiSensorData, BaseStationSensorData

"""Generation of weather data plots.

Functions:
get_last_n_days_data:           Returns the data of the latest n days of the datasets stored in all PC-Wetterstation compatible CSV-files in the specified folder.
plot_of_last_days:              Plots the weather data of the last n days from all data available in a defined folder.

Global variables:
delta:                          Assumed width of a single y-axis label set (in pixel).
"""
import matplotlib
from weathernetwork.server.sqldatabase import SQLWeatherDB
matplotlib.use( 'Agg' )
from mpl_toolkits.axes_grid1 import host_subplot
import mpl_toolkits.axisartist as AA
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as ticker
import matplotlib.font_manager as fonts
import numpy as np
import datetime
from datetime import datetime as dt
from datetime import timedelta
import re
import math

import pcwetterstation
import te923ToCSVreader
import csvfilemerger
import utilities

delta = 70


def get_last_n_days_data(num_days, db_file_name, station_ID):
    """Returns the data of the latest n days from the specified database.
    
    Args:
    num_days:                   The data for the last 'num_days' before the last entry in the data file will be returned.
    db_file_name:               Name and path of the SQL-database file
    required_sensor_IDs:        Sensors IDs for which the sensor description is required
    
    Returns:                             
    data:                       Weather dataset of the last 'num_days' before the the last entry in the specified folder containing all sensors stored
                                If rain data is present, the rain data will be returned as a cumulative sum starting from the first timepoint in the data with 0 mm
    """
    # Read the required data from the database
    #last_time = datetime.datetime.utcnow()
    last_time = datetime.datetime(year=2015, month=3, day=15) # TODO: temp
    first_time = last_time - timedelta(days=num_days)
    
    weather_db = SQLWeatherDB(db_file_name)
    data = weather_db.get_data_in_time_range(station_ID, first_time, last_time)
    
    # calculate cumulated rain amount
    #rain_in_period = []
    #for line in data:
    #    rain_in_period.append(line.get_rain_gauge())
    #
    #cumulated_rain = list(itertools.accumulate(rain_in_period))

    return data


def GetScalings( min_max_sensors ):
    """Obtains the minimum and maximum scalings of the y-axis for the sensors.
    
    Args:
    min_max_sensors:            Dict containing the minimum and maximum values of the sensors in the graph. Format: min_max_sensors[ sensor_name ]['min'/'max'].  
    
    Returns:                             
    num_ticks:                  Number of ticks of the y-axis. 
    min_max_axis:               Dict containing the minimum and maximum values for all sensors on the axis. Format: min_max_axis[ sensor_name ]['min'/'max'].
                                
    Raises:
    None
    """
    delta_T = 5.0       # degree C by definition
    delta_p = 5.0       # hPa by definition

    all_num_ticks = []
    # determine number of ticks
    for key, sensor in min_max_sensors.items():
        if CombiSensorData.TEMPERATURE in key:
            # temperatures should have an identical scaling
            curr_min_T = utilities.floor_to_n( sensor['min'], delta_T )
            if 'min_T' not in locals() or curr_min_T < min_T:
                min_T = curr_min_T
            curr_max_T = utilities.ceil_to_n( sensor['max'], delta_T )
            if 'max_T' not in locals() or curr_max_T > max_T:
                max_T = curr_max_T
            all_num_ticks.append( int( ( max_T - min_T ) / delta_T + 1 ) )
        elif BaseStationSensorData.RAIN in key:
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
            max_rain_counter = utilities.ceil_to_n( sensor['max'], delta_rain )
            all_num_ticks.append( int( ( max_rain_counter - 0 ) / delta_rain + 1 ) )
        elif BaseStationSensorData.PRESSURE in key:
            min_p = utilities.floor_to_n( sensor['min'], delta_p )
            max_p = utilities.ceil_to_n( sensor['max'], delta_p )
            all_num_ticks.append( int( ( max_p - min_p ) / delta_p + 1 ) )

    if len( all_num_ticks ) == 0:
        all_num_ticks.append( 5 ); # default value if no special sensors are present

    num_ticks = max( all_num_ticks )

    min_max_axis = dict()
    for key, sensor in min_max_sensors.items():
        if CombiSensorData.TEMPERATURE in key:
            # temperature minimum is always the next lower temperature dividable by 5 degree C (already calculated)
            max_T = min_T + delta_T * ( num_ticks - 1 )
            min_max_axis[key] = { 'min' : min_T, 'max' : max_T };
        elif CombiSensorData.HUMIDITY in key:
            # humidity is always in the range from 0 - 100 pct
            min_max_axis[key] = { 'min' : 0, 'max' : 100 };
        elif BaseStationSensorData.RAIN in key:
            # rain counter minimum is always 0 mm
            max_rain_counter = 0 + delta_rain * ( num_ticks - 1 )
            min_max_axis[key] = { 'min' : 0, 'max' : max_rain_counter }
        elif BaseStationSensorData.PRESSURE in key:
            # pressure minimum is always the next lower pressure dividable by 5 hPa (already calculated)
            max_p = min_p + delta_p * ( num_ticks - 1 )
            min_max_axis[key] = { 'min' : min_p, 'max' : max_p }
        else:
            # all other sensors are scaled by the min/max values
            min_max_axis[key] = { 'min' : sensor['min'], 'max' : sensor['max'] }

    return num_ticks, min_max_axis


def plot_of_last_n_days( num_days, db_file_name, station_ID, data_folder, sensors_to_plot, graph_folder, graph_file_name, is_save_to_fig ):
    """Plots the weather data of the last n days from all data available in a defined folder.
    
    Args:
    num_days:                   Last 'num_days' before the last entry in the data file will be plotted.
    data_folder:                Folder with the PC-Wetterstation compatible CSV-files which will be analyzed.
    sensors_to_plot:            List with all names of the sensors to be plotted. The names must be identical with the 'sensor_list' dictionary labels.
    graph_folder:               Folder where the graph plot file will be stored.
    graph_file_name:            Name of the graph plot file. Any graphics format supported by MATPLOTLIB can be used, for example '.svg' or '.png'.
    is_save_to_fig:             Flag stating if the graph will be written to file (True) or to a GUI (False)
    
    Returns:                             
    num_plot_datasets:          Number of datasets plotted
    first_plot_time:            Timepoint of the beginning of the plotted dataset
    last_plot_time:             Timepoint of the end of the plotted dataset
                                
    Raises:
    None
    """
    # Find data for the last n days in the data folder
    data = get_last_n_days_data( num_days, db_file_name, station_ID )

    # Calculate secondary y-axis positions
    yAxisPos = []
    for index, sensor in enumerate( sensors_to_plot ):
        if index % 2 == 0:
            yAxisPos.append( ( 'left', -index / 2 * delta ) )
        else:
            yAxisPos.append( ( 'right', ( index - 1 ) / 2 * delta ) )

    # Generate figure
    plt.figure( figsize = [13.5,6] )
    ax = [ host_subplot( 111, axes_class=AA.Axes ) ]
    for index, sensor in enumerate( sensors_to_plot ):
        if index > 0:
            ax.append( ax[0].twinx() )
            ax[-1].axis['right'].set_visible( False )
            ax[-1].axis[ yAxisPos[index][0] ] = ax[-1].new_fixed_axis( yAxisPos[index][0], offset = ( yAxisPos[index][1], 0 ) )
    
    # Plot graphs for the required data
    times = [ line.get_time() for line in data ]
    min_max_sensors = dict()
    for index, sensor in enumerate( sensors_to_plot ):
        # Plot data
        plot_data = [ float( line.get_sensor_value(sensor) ) for line in data ]
        ax[index].plot( times, plot_data, label = str(sensor), lw=2.0 )
        min_max_sensors[str(sensor)] = { 'min': min( plot_data ), 'max' : max( plot_data ) }

        # Set data axis settings
        sensor_color = ax[index].lines[0].get_color()
        ax[index].set_ylabel( data[0].get_sensor_description(sensor) + ' / ' + data[0].get_sensor_unit(sensor), color = sensor_color )
        ax[index].axis[ yAxisPos[index][0] ].label.set_font_properties( fonts.FontProperties( weight='bold', size=13 ) )
        ax[index].yaxis.set_minor_locator( ticker.AutoMinorLocator( 5 ) ) 
        ax[index].axis[ yAxisPos[index][0] ].minor_ticks.set_color( sensor_color )
        ax[index].axis[ yAxisPos[index][0] ].major_ticklabels.set_color( sensor_color )
        ax[index].axis[ yAxisPos[index][0] ].major_ticklabels.set_fontproperties( fonts.FontProperties( weight='bold' ) )
        ax[index].axis[ yAxisPos[index][0] ].major_ticks.set_color( sensor_color )
        ax[index].axis[ yAxisPos[index][0] ].line.set_color( sensor_color )
        ax[index].axis[ yAxisPos[index][0] ].line.set_linewidth( 2.0 )

    # Set appropriate scaling of the y-axis
    num_ticks, min_max_axis = GetScalings( min_max_sensors )
    for index, sensor in enumerate( sensors_to_plot ):
        ax[index].yaxis.set_major_locator( ticker.LinearLocator( numticks = num_ticks ) )
        ax[index].set_ylim( min_max_axis[str(sensor)]['min'], min_max_axis[str(sensor)]['max'] )
                    
    # Configure date axis and grid lines
    ax[0].xaxis.set_minor_locator( mdates.HourLocator( byhour = [ 0, 6, 12, 18 ] ) )
    ax[0].grid( True, which='minor', color='gray', linestyle='dotted', lw=0.5 )
    ax[0].axis['bottom'].minor_ticks.set_ticksize( 5 )  
    ax[0].axis['top'].minor_ticks.set_ticksize( 5 ) 
    ax[0].xaxis.set_major_locator( mdates.DayLocator() )
    ax[0].xaxis.set_major_formatter( mdates.DateFormatter('%a\n%d.%m.%y' ) )
    ax[-1].grid( True, which='major', color='k', linestyle='-', lw=1.0 )
    ax[0].axis['bottom'].major_ticklabels.set_pad( 20 )
    ax[0].axis['bottom'].major_ticklabels.set_horizontalalignment( 'left' )
    ax[0].axis['bottom'].major_ticklabels.set_fontproperties( fonts.FontProperties( weight='bold', size=13 ) )

    # Add information on last data
    plt.text( 0.99, 0.999, 'Letzte Daten: ' + dt.strftime( times[-1], '%d.%m.%Y %H:%M' ), horizontalalignment='right', verticalalignment='bottom', transform = ax[0].transAxes, fontproperties = fonts.FontProperties( weight='bold', size=12 ) )
    plt.tight_layout()

    # Save plot to file
    if is_save_to_fig:
        plt.savefig( graph_folder + '/' + graph_file_name )
    else:
        plt.show()

    # Set return data
    if len( times ) > 0:
        first_plot_time =  times[0]
        last_plot_time = times[-1]
    else:
        first_plot_time = dt( datetime.MINYEAR, 1, 1, 0, 0, 0, 0 )
        last_plot_time = dt( datetime.MINYEAR, 1, 1, 0, 0, 0, 0 )

    return len( times ), first_plot_time, last_plot_time
