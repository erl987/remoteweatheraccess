import graphs


if __name__ == "__main__":
    db_file_name = "data/weather.db"
    station_ID = "TES2"
    data_storage_folder = ""
    sensors_to_plot = [ 'pressure', 'rainCounter', 'tempOutside1', 'humidOutside1' ]
    graph_directory = []
    graph_file_name = []


    num_plot_datasets, first_plot_time, last_plot_time = graphs.plot_of_last_n_days( 7, db_file_name, station_ID, data_storage_folder, sensors_to_plot, graph_directory, graph_file_name, True )        