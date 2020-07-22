from http import HTTPStatus

from flask import request, jsonify, current_app, Blueprint
import pandas as pd

from ..extensions import db
from ..exceptions import APIError
from ..utils import Role, with_rollback_and_raise_exception
from .models import WeatherDataset, GetWeatherdataPayload, WeatherRawDataset, WindSensorData, CombiSensorData, \
    RainSensorData
from ..utils import access_level_required, json_with_rollback_and_raise_exception, to_utc

weatherdata_blueprint = Blueprint('data', __name__, url_prefix='/api/v1/data')


@weatherdata_blueprint.route('', methods=['POST'])
@access_level_required(Role.PUSH_USER)
@json_with_rollback_and_raise_exception
def add_weather_dataset():
    new_dataset = _create_weather_dataset()

    existing_dataset = WeatherDataset.query.filter_by(timepoint=new_dataset.timepoint).first()
    if not existing_dataset:
        db.session.add(new_dataset)
        db.session.commit()

        response = jsonify(new_dataset)
        current_app.logger.info('Added new dataset for time \'{}\' to the database'.format(new_dataset.timepoint))
        response.status_code = HTTPStatus.CREATED
    else:
        raise APIError('Dataset for time \'{}\' already in the database'.format(new_dataset.timepoint),
                       status_code=HTTPStatus.CONFLICT, location='/api/v1/data/{}'.format(existing_dataset.id))

    response.headers['location'] = '/api/v1/data/{}'.format(new_dataset.id)

    return response


def _create_weather_dataset():
    new_dataset = WeatherRawDataset.from_dict(request.json)

    all_combi_sensor_data = []
    for combi_sensor_data in new_dataset.temperature_humidity:
        all_combi_sensor_data.append(CombiSensorData(**combi_sensor_data.to_dict()))
    wind_sensor_data = WindSensorData(**new_dataset.wind.to_dict())
    rain_sensor_data = RainSensorData(rain_counter_in_mm=new_dataset.rain_counter)
    weather_dataset = WeatherDataset(
        timepoint=new_dataset.timepoint,
        station_id=new_dataset.station,
        pressure=new_dataset.pressure,
        uv=new_dataset.uv,
        rain_sensor_data=rain_sensor_data,
        wind_sensor_data=wind_sensor_data,
        combi_sensor_data=all_combi_sensor_data
    )

    return weather_dataset


@weatherdata_blueprint.route('', methods=['GET'])
@json_with_rollback_and_raise_exception
def get_weather_datasets():
    time_period = GetWeatherdataPayload.from_dict(request.json)
    first = time_period.first_timepoint
    last = time_period.last_timepoint
    requested_sensors = time_period.sensors  # TODO: validation using marshmallow-enum ...

    requested_base_station_sensors, requested_entities, requested_temp_humidity_sensors, requested_wind_sensors = \
        _create_query_configuration(requested_sensors)

    if last < first:
        raise APIError('Last time \'{}\' is later than first time \'{}\''.format(last, first),
                       status_code=HTTPStatus.BAD_REQUEST)

    found_datasets = pd.read_sql(db.session.query(WeatherDataset)
                                 .filter(WeatherDataset.timepoint >= first)
                                 .filter(WeatherDataset.timepoint <= last)
                                 .join(WeatherDataset.rain_sensor_data)
                                 .join(WeatherDataset.wind_sensor_data)
                                 .join(WeatherDataset.combi_sensor_data)
                                 .order_by(WeatherDataset.timepoint).with_entities(WeatherDataset.timepoint,
                                                                                   WeatherDataset.station_id,
                                                                                   CombiSensorData.sensor_id,
                                                                                   *requested_entities)
                                 .statement,
                                 db.session.bind)

    if found_datasets.empty:
        return jsonify({}), HTTPStatus.OK

    combi_sensor_ids = found_datasets.sensor_id.unique()

    found_datasets_per_station = {}
    station_ids = found_datasets['station_id'].unique()
    for station_id in station_ids:
        station_datasets = found_datasets.loc[(found_datasets.station_id == station_id) &
                                              (found_datasets.sensor_id == "IN")]

        found_datasets_per_station[station_id] =\
            station_datasets.loc[:, requested_base_station_sensors].to_dict("list")
        found_datasets_per_station[station_id]["wind"] = \
            station_datasets.loc[:, requested_wind_sensors].to_dict("list")
        found_datasets_per_station[station_id]["temperature_humidity"] = {}
        for combi_sensor_id in combi_sensor_ids:
            found_datasets_per_station[station_id]["temperature_humidity"][combi_sensor_id] =\
                found_datasets.loc[(found_datasets.station_id == station_id) &
                                   (found_datasets.sensor_id == combi_sensor_id), requested_temp_humidity_sensors]\
                .to_dict("list")

    response = jsonify(found_datasets_per_station)
    response.status_code = HTTPStatus.OK
    current_app.logger.info('Returned {} datasets from \'{}\'-\'{}\''.format(len(found_datasets), first, last))

    return response


def _create_query_configuration(requested_sensors):
    do_configure_all = (len(requested_sensors) == 0)
    requested_base_station_sensors, requested_entities = _create_base_station_query_configuration(requested_sensors,
                                                                                                  do_configure_all)
    requested_wind_sensors = _create_wind_sensor_query_configuration(requested_entities, requested_sensors,
                                                                     do_configure_all)
    requested_temp_humidity_sensors = _create_temp_humidity_sensor_query_configuration(requested_entities,
                                                                                       requested_sensors,
                                                                                       do_configure_all)

    return requested_base_station_sensors, requested_entities, requested_temp_humidity_sensors, requested_wind_sensors


def _create_temp_humidity_sensor_query_configuration(requested_entities, requested_sensors, do_configure_all):
    requested_entities.extend([CombiSensorData.temperature, CombiSensorData.humidity])
    requested_temp_humidity_sensors = ["temperature", "humidity"]

    if not do_configure_all:
        if "temperature" not in requested_sensors:
            requested_temp_humidity_sensors.remove("temperature")
            requested_entities.remove(CombiSensorData.temperature)
        if "humidity" not in requested_sensors:
            requested_temp_humidity_sensors.remove("humidity")
            requested_entities.remove(CombiSensorData.humidity)

    return requested_temp_humidity_sensors


def _create_wind_sensor_query_configuration(requested_entities, requested_sensors, do_configure_all):
    requested_entities.extend(
        [WindSensorData.gusts, WindSensorData.direction, WindSensorData.wind_temperature, WindSensorData.speed])
    requested_wind_sensors = ["gusts", "direction", "wind_temperature", "speed"]

    if not do_configure_all:
        if "gusts" not in requested_sensors:
            requested_wind_sensors.remove("gusts")
            requested_entities.remove(WindSensorData.gusts)
        if "direction" not in requested_sensors:
            requested_wind_sensors.remove("direction")
            requested_entities.remove(WindSensorData.direction)
        if "wind_temperature" not in requested_sensors:
            requested_wind_sensors.remove("wind_temperature")
            requested_entities.remove(WindSensorData.wind_temperature)
        if "speed" not in requested_sensors:
            requested_wind_sensors.remove("speed")
            requested_entities.remove(WindSensorData.speed)

    return requested_wind_sensors


def _create_base_station_query_configuration(requested_sensors, do_configure_all):
    requested_entities = [WeatherDataset.pressure, WeatherDataset.uv, RainSensorData.rain_counter_in_mm]
    requested_base_station_sensors = ["pressure", "uv", "rain_counter_in_mm"]

    if not do_configure_all:
        if "pressure" not in requested_sensors:
            requested_base_station_sensors.remove("pressure")
            requested_entities.remove(WeatherDataset.pressure)
        if "uv" not in requested_sensors:
            requested_base_station_sensors.remove("uv")
            requested_entities.remove(WeatherDataset.uv)
        if "rain_counter_in_mm" not in requested_sensors:
            requested_base_station_sensors.remove("rain_counter_in_mm")
            requested_entities.remove(RainSensorData.rain_counter_in_mm)

    return requested_base_station_sensors, requested_entities


@weatherdata_blueprint.route('/<id>', methods=['PUT'])
@access_level_required(Role.PUSH_USER)
@json_with_rollback_and_raise_exception
def update_weather_dataset(id):
    new_dataset = _create_weather_dataset()
    existing_dataset = WeatherDataset.query.get(id)
    if not existing_dataset:
        raise APIError('No dataset with id \'{}\''.format(id), status_code=HTTPStatus.NOT_FOUND)

    if to_utc(new_dataset.timepoint) != to_utc(existing_dataset.timepoint):
        raise APIError('The time \'{}\' stored for id \'{}\' does not match the time \'{}\' of the submitted '
                       'dataset'.format(existing_dataset.timepoint, id, new_dataset.timepoint),
                       status_code=HTTPStatus.CONFLICT,
                       location='/api/v1/data/{}'.format(existing_dataset.id))

    # TODO: needs to be completed for all relevant fields ...
    existing_dataset.pressure = new_dataset.pressure
    db.session.commit()
    current_app.logger.info('Updated dataset for time \'{}\' to the database'.format(existing_dataset.timepoint))

    response = jsonify(existing_dataset)
    response.status_code = HTTPStatus.OK
    response.headers['location'] = '/api/v1/data/{}'.format(existing_dataset.id)

    return response


@weatherdata_blueprint.route('/<id>', methods=['DELETE'])
@access_level_required(Role.PUSH_USER)
@with_rollback_and_raise_exception
def delete_weather_dataset(id):
    existing_dataset = WeatherDataset.query.get(id)
    if not existing_dataset:
        current_app.logger.info('Nothing to delete for dataset with id \'{}\' '.format(id))
        return '', HTTPStatus.NO_CONTENT

    db.session.delete(existing_dataset)
    db.session.commit()
    current_app.logger.info('Deleted dataset for time \'{}\' from the database'.format(existing_dataset.timepoint))

    response = jsonify(existing_dataset)
    response.status_code = HTTPStatus.OK

    return response


@weatherdata_blueprint.route('/<id>', methods=['GET'])
@with_rollback_and_raise_exception
def get_one_weather_dataset(id):
    dataset = WeatherDataset.query.get(id)
    if not dataset:
        raise APIError('No dataset with id \'{}\''.format(id), status_code=HTTPStatus.BAD_REQUEST)

    response = jsonify(dataset)
    response.status_code = HTTPStatus.OK
    current_app.logger.info('Returned dataset for id \'{}\''.format(id))

    return response


@weatherdata_blueprint.route('/limits', methods=['GET'])
@with_rollback_and_raise_exception
def get_available_time_period():
    time_range = GetWeatherdataPayload(
        first_timepoint=db.session.query(WeatherDataset.timepoint, db.func.min(WeatherDataset.timepoint)).scalar(),
        last_timepoint=db.session.query(WeatherDataset.timepoint, db.func.max(WeatherDataset.timepoint)).scalar()
    )

    if not time_range.first_timepoint or not time_range.last_timepoint:
        raise APIError('No data in the database', status_code=HTTPStatus.NOT_FOUND)

    response = jsonify(time_range)
    response.status_code = HTTPStatus.OK
    current_app.logger.info('Returned available time period: \'{}\'-\'{}\''.format(time_range.first_timepoint,
                                                                                   time_range.last_timepoint))

    return response
