"""Read in data from a TE923-compatible weather station via USB and store the data in a CSV-file compatible to PC-Wetterstation."""
import te923ToCSVreader

data_folder = '/home/pi/weatherstation/data/'
station_data_file_name = 'stationData.dat'
log_file_name = 'te923ToCSV.log'

# Read new weather data from the TE923-station and save it in a CSV-file compatible to PC-Wetterstation
te923ToCSVreader.te923ToCSVreader( data_folder, station_data_file_name, log_file_name )
