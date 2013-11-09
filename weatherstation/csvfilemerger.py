#!/opt/python3.3/bin/python3.3
"""Merging all PC-Wetterstation CSV-files in a folder into the monthly files.
Functions:
extractdate:                    Extracting the month and the year of the file data from the file name.
main:                           Main function merging the data files.

Global variables:
data_folder:                    Folder containing the data files to be merged.
"""
import os
import os.path
import shutil
import re
import sys
from datetime import datetime as dt

import pcwetterstation
import te923ToCSVreader

data_storage_folder = './data/merge_test/'
new_data_folder = './data/merge_test/new_data/'
temp_data_folder = './data/merge_test/new_data/temp/'


def extractdate( filename ):
    """Extracting the month and the year of the file data from the file name.
    
    Args:
    filename:                   File name (must only be of the style 'EXPMM_YY.CSV')
                                
    Returns:
    month:                      Month of the file data validity.
    year:                       Year of the file data validity.
                               
    Raises:
    None
    """
    splitted_id = str.split( re.search( '\d\d_\d\d', filename ).group(0), '_' )
    month = int( splitted_id[0] )
    year = int( splitted_id[1] )

    return month, year


def main():
    """Main function merging the data files."""
    # Load new data files from the command line arguments
    if ( len(sys.argv) == 1 ):
        raise RuntimeError( 'The new files must be given as command line arguments.' )
    new_data_file_list = sys.argv
    new_data_file_list.pop(0)

    # Load all new data and write it to temporary monthly files
    new_data =  []
    for file in new_data_file_list:
        curr_data, rain_calib_factor, rain_counter_base, station_name, station_height, station_type, sensor_descriptions_dict, sensor_units_dict = pcwetterstation.read( new_data_folder, file, te923ToCSVreader.sensor_list )
        new_data = new_data + curr_data
    
    pcwetterstation.write( temp_data_folder, rain_calib_factor, station_name, station_height, station_type, new_data, te923ToCSVreader.sensor_list )

    # Delete the read new data files
    pcwetterstation.deletedatafiles( new_data_folder, new_data_file_list )

    # Merge the monthly data files with those in the storage folder
    new_monthly_file_list = pcwetterstation.finddatafiles( temp_data_folder )
    existing_monthly_file_list = pcwetterstation.finddatafiles( data_storage_folder )
    for file in new_monthly_file_list:
        if not os.path.exists( data_storage_folder + '/' + file ):
            shutil.copyfile( temp_data_folder + '/' + file, data_storage_folder + '/' + file )
        else:
            pcwetterstation.merge( data_storage_folder, temp_data_folder, file, data_storage_folder, file, te923ToCSVreader.sensor_list ) 

    # Delete the processed monthly data files in the new data folder
    pcwetterstation.deletedatafiles( temp_data_folder, new_monthly_file_list )


if __name__ == "__main__":
    main()
