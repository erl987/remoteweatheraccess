import pickle

def write_station_data(station_data_file_name, rain_calib_factor, station_name, station_height, storage_interval):
    try:
        with open( station_data_file_name, 'wb' ) as f:
            pickle.dump( dict( rain_calib_factor = rain_calib_factor, station_name = station_name, station_height = station_height, storage_interval = storage_interval ), f )
    except Exception:
        print( 'Station data file ' + station_data_file_name + ' could not be opened!' )