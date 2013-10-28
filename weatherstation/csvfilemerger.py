#!/usr/bin/python
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

import pcwetterstation
import te923ToCSVreader

data_folder = './data/merge_test/'


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
    filename = filename.upper()
    filename = str.replace( filename, 'EXP', '' )
    filename = str.replace( filename, '.CSV', '' )
    splitted_id = str.split( filename, '_' )
    month = int( splitted_id[0] )
    year = int( splitted_id[1] )

    return month, year


def main():
    """Main function merging the data files."""
    # Find all weather data files potentially compatible to PC-Wetterstation
    file_list = pcwetterstation.finddatafiles( data_folder )

    # Find all monthly data files
    monthly_file_list = []
    for file in file_list:
        pcwetterstation_id = re.search( 'EXP\d\d_\d\d.CSV', file.upper() )
        if pcwetterstation_id is not None:
            if len( str.replace( file.upper(), pcwetterstation_id.group(0), '' ) ) == 0:
                monthly_file_list.append( file ) 
            
    # Delete all monthly files from the list
    file_list = [ x for x in file_list if not x in monthly_file_list ]        

    # Analyse all files for their month of validity
    analyzed_file_list = []
    months_set = set()
    for file in file_list:
        pcwetterstation_id = re.search( 'EXP\d\d_\d\d.CSV', file.upper() )
        month, year = extractdate( pcwetterstation_id.group(0) )
        analyzed_file_list.append( ( ( month, year ), file ) )
        months_set.add( ( month, year ) )

        # Copy the first file to generate a monthly file if it is not yet existing
        total_month_file = 'EXP%02i_%02i.csv' % ( month, year )
        if not os.path.exists( data_folder + '/' + total_month_file ):
            shutil.copyfile( data_folder + '/' + file, data_folder + '/' + total_month_file )

    # merge all new data files into the monthly files
    for month in months_set:
        total_month_file = 'EXP%02i_%02i.csv' % month
        for file in analyzed_file_list:
            if ( file[0] == month ):
                pcwetterstation.merge( data_folder, file[1], total_month_file, te923ToCSVreader.sensor_list )      

    # Delete the processed new data files
    pcwetterstation.deletedatafiles( data_folder, file_list )


if __name__ == "__main__":
    main()
