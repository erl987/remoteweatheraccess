def is_temp_sensor(sensor_id):
    return sensor_id.endswith("_temp")


def is_humidity_sensor(sensor_id):
    return sensor_id.endswith("_humid")


def get_temp_humidity_sensor_id(sensor_id):
    return sensor_id.split("_")[0]


def get_sensor_data(data, station_id, sensor_id):
    if is_temp_sensor(sensor_id):
        sensor_data = data[station_id]["temperature_humidity"][get_temp_humidity_sensor_id(sensor_id)]["temperature"]
    elif is_humidity_sensor(sensor_id):
        sensor_data = data[station_id]["temperature_humidity"][get_temp_humidity_sensor_id(sensor_id)]["humidity"]
    else:
        sensor_data = data[station_id][sensor_id]
    return sensor_data
