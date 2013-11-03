"""Generation of weather data plots.

Functions:
get_last_n_days_data:           Returns the data of the latest n days of the datasets stored in all PC-Wetterstation compatible CSV-files in the specified folder.
plot_of_last_days:              Plots the weather data of the last n days from all data available in a defined folder.

Global variables:
delta:                          Assumed width of a single y-axis label set (in pixel).
"""
from mpl_toolkits.axes_grid1 import host_subplot
import mpl_toolkits.axisartist as AA
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as ticker
import numpy as np
from datetime import datetime as dt
from datetime import timedelta
import re
import math

import pcwetterstation
import te923ToCSVreader
import csvfilemerger

delta = 70
time_import = lambda x: dt.strptime( x['date'] + ' ' + x['time'], '%d.%m.%Y %H:%M' )


def get_last_n_days_data( data_folder, num_days ):
    """Returns the data of the latest n days of the datasets stored in all PC-Wetterstation compatible CSV-files in the specified folder.
    
    Args:
    data_folder:                Folder with the PC-Wetterstation compatible CSV-files which will be analyzed.   
    num_days:                   The data for the last 'num_days' before the last entry in the data file will be returned.
    
    Returns:                             
    limited_data:               Weather dataset of the last 'num_days' before the the last entry in the specified folder containing all sensors stored. 
                                If rain data is present, the rain data will be returned as a cumulative sum starting from the first timepoint in the data with 0 mm.
                                
    Raises:
    None
    """
    # Find all monthly PC-Wetterstation CSV-files in the specified folder
    file_list = pcwetterstation.finddatafiles( data_folder )
    monthly_file_list = []
    for file in file_list:
        pcwetterstation_id = re.search( 'EXP\d\d_\d\d.CSV', file.upper() )
        if pcwetterstation_id is not None:
            if len( str.replace( file.upper(), pcwetterstation_id.group(0), '' ) ) == 0:
                monthly_file_list.append( file ) 

    # Determine which files might contain required data
    num_potential_months = math.ceil( num_days / 30 ) + 1    # any series of days less than 30 can only be divided into two months
    analyzed_file_list = []
    for file in monthly_file_list:
        month, year = csvfilemerger.extractdate( file )
        analyzed_file_list.append( ( dt( day = 1, month = month, year = year + 2000 ), file ) )
    analyzed_file_list = sorted( analyzed_file_list, key=lambda x: x[0], reverse=True )
    analyzed_file_list = [ x for index, x in enumerate( analyzed_file_list ) if index < num_potential_months ]

    # Read weather data from these file and provide it sorted according to time
    data = []
    for file in analyzed_file_list:
        all_data = pcwetterstation.read( data_folder, file[1], te923ToCSVreader.sensor_list )
        data = all_data[0] + data

        # Abort reading of data if enough data has been read (the file order and properties guarantee sorted data)
        if ( time_import( data[-1] ) - time_import( data[0] ) ) > timedelta( days = num_days ):
            break

    # Limit data to the last days
    last_time = time_import( data[-1] )
    limited_data = [ line for line in data if ( last_time - time_import( line ) ) <= timedelta( days = num_days ) ]

    # Calculate cumulated rain amount
    search_list = [ key for key, val in limited_data[0].items() if key == 'rainCounter' ]
    if len( search_list ) > 0:
        for index, line in enumerate( limited_data[:] ):
            if ( index == 0 ):
                line['rainCounter'] = 0
            else:
                line['rainCounter'] = limited_data[ index - 1 ]['rainCounter'] + float( line['rainCounter'] )

    return limited_data


def plot_of_last_n_days( num_days, data_folder, sensors_to_plot, graph_folder, graph_file_name ):
    """Plots the weather data of the last n days from all data available in a defined folder.
    
    Args:
    num_days:                   Last 'num_days' before the last entry in the data file will be plotted.
    data_folder:                Folder with the PC-Wetterstation compatible CSV-files which will be analyzed.
    sensors_to_plot:            List with all names of the sensors to be plotted. The names must be identical with the 'sensor_list' dictionary labels.
    graph_folder:               Folder where the graph plot file will be stored.
    graph_file_name:            Name of the graph plot file. Any graphics format supported by MATPLOTLIB can be used, for example '.svg' or '.png'.
    
    Returns:                             
    None
                                
    Raises:
    None
    """
    # Find data for the last n days in the data folder
    data = get_last_n_days_data( data_folder, num_days )

    # Calculate secondary y-axis positions
    yAxisPos = []
    for index, sensor in enumerate( sensors_to_plot ):
        if index % 2 == 0:
            yAxisPos.append( ( 'left', -index / 2 * delta ) )
        else:
            yAxisPos.append( ( 'right', ( index - 1 ) / 2 * delta ) )

    # Generate figure
    plt.figure( figsize = [15,7] )
    ax = [ host_subplot( 111, axes_class=AA.Axes ) ]
    for index, sensor in enumerate( sensors_to_plot ):
        if index > 0:
            ax.append( ax[0].twinx() )
            ax[-1].axis['right'].set_visible( False )
            ax[-1].axis[ yAxisPos[index][0] ] = ax[-1].new_fixed_axis( yAxisPos[index][0], offset = ( yAxisPos[index][1], 0 ) )
    
    # Plot graphs for the required data
    times = [ time_import( line ) for line in data ]
    for index, sensor in enumerate( sensors_to_plot ):
        # Plot data
        plot_data = [ float( line[ sensor ] ) for line in data ]
        ax[index].plot( times, plot_data, label = sensor, lw=2.0  )

        # Set data axis settings
        sensor_color = ax[index].lines[0].get_color()
        ax[index].set_ylabel( sensor, color = sensor_color )
        ax[index].axis[ yAxisPos[index][0] ].major_ticklabels.set_color( sensor_color )
        ax[index].axis[ yAxisPos[index][0] ].major_ticks.set_color( sensor_color )
        ax[index].axis[ yAxisPos[index][0] ].line.set_color( sensor_color )
        ax[index].axis[ yAxisPos[index][0] ].line.set_linewidth( 2.0 )
        ax[index].yaxis.set_major_locator( ticker.LinearLocator( numticks = 5 ) )
                    
    # Configure date axis and grid lines
    ax[0].xaxis.set_minor_locator( mdates.HourLocator( byhour = 12 ) )
    ax[0].xaxis.set_minor_formatter( mdates.DateFormatter('%a\n%d.%m.%y') )
    ax[0].grid( True, which='minor', color='gray', linestyle='--', lw=0.5 )
    ax[0].axis['bottom'].minor_ticklabels.set_pad( 35 )    
    ax[0].xaxis.set_major_locator( mdates.DayLocator() )
    ax[0].xaxis.set_major_formatter( mdates.DateFormatter('%H:%M' ) )
    ax[-1].grid( True, which='major', color='k', linestyle='-', lw=1.0 )
    ax[0].axis['bottom'].major_ticklabels.set_pad( 5 )    
    plt.tight_layout()

    # Save plot to file
    plt.savefig( graph_folder + '/' + graph_file_name )
