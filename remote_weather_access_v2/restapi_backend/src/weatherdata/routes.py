from http import HTTPStatus

from flask import request, jsonify, current_app, Blueprint

from ..extensions import db
from ..exceptions import raise_api_error, APIError
from ..utils import Role
from .serializers import deserialize_base_station_dataset, base_station_schema, time_range_schema, \
    base_stations_schema, TimeRangeSchema, deserialize_weather_data_message
from .models import BaseStationData
from ..utils import access_level_required, rollback_and_raise_exception, to_utc


weatherdata_blueprint = Blueprint('data', __name__, url_prefix='/api/v1/data')


@weatherdata_blueprint.route('', methods=['POST'])
@access_level_required(Role.PUSH_USER)
@rollback_and_raise_exception
def add_weather_dataset():
    try:
        new_dataset = deserialize_weather_data_message(request.json)
        #new_dataset = deserialize_base_station_dataset(request.json)
    except Exception as e:
        raise raise_api_error(e, status_code=HTTPStatus.BAD_REQUEST)

    existing_dataset = BaseStationData.query.filter_by(timepoint=new_dataset.timepoint).first()
    if not existing_dataset:
        db.session.add(new_dataset)
        db.session.commit()

        response = base_station_schema.jsonify(new_dataset)
        current_app.logger.info('Added new dataset for time \'{}\' to the database'.format(new_dataset.timepoint))
        response.status_code = HTTPStatus.CREATED
    else:
        raise APIError('Dataset for time \'{}\' already in the database'.format(new_dataset.timepoint),
                       status_code=HTTPStatus.CONFLICT, location='/api/v1/data/{}'.format(existing_dataset.id))

    response.headers['location'] = '/api/v1/data/{}'.format(new_dataset.id)

    return response


@weatherdata_blueprint.route('', methods=['GET'])
@rollback_and_raise_exception
def get_weather_datasets():
    try:
        time_period = time_range_schema.load(request.args)
        first = time_period.data['first']
        last = time_period.data['last']
        if last < first:
            raise APIError('Last time \'{}\' is later than first time \'{}\''.
                           format(last, first), status_code=HTTPStatus.BAD_REQUEST)
    except Exception as e:
        raise raise_api_error(e, status_code=HTTPStatus.BAD_REQUEST)

    matching_datasets = (BaseStationData.query
                         .filter(BaseStationData.timepoint >= first)
                         .filter(BaseStationData.timepoint <= last)
                         .order_by(BaseStationData.timepoint).all())
    if not matching_datasets:
        return jsonify({}), HTTPStatus.OK

    response = base_stations_schema.jsonify(matching_datasets)
    response.status_code = HTTPStatus.OK
    current_app.logger.info('Returned {} datasets from \'{}\'-\'{}\''.format(len(matching_datasets), first, last))

    return response


@weatherdata_blueprint.route('/<id>', methods=['PUT'])
@access_level_required(Role.PUSH_USER)
@rollback_and_raise_exception
def update_weather_dataset(id):
    try:
        new_dataset = deserialize_base_station_dataset(request.json)
    except Exception as e:
        raise raise_api_error(e, status_code=HTTPStatus.BAD_REQUEST)

    existing_dataset = BaseStationData.query.get(id)
    if not existing_dataset:
        raise APIError('No dataset with id \'{}\''.format(id), status_code=HTTPStatus.NOT_FOUND)

    if to_utc(new_dataset.timepoint) != to_utc(existing_dataset.timepoint):
        raise APIError('The time \'{}\' stored for id \'{}\' does not match the time \'{}\' of the submitted '
                       'dataset'.format(existing_dataset.timepoint, id, new_dataset.timepoint),
                       status_code=HTTPStatus.CONFLICT,
                       location='/api/v1/data/{}'.format(existing_dataset.id))

    existing_dataset.temp = new_dataset.temp
    existing_dataset.humidity = new_dataset.humidity
    db.session.commit()
    current_app.logger.info('Updated dataset for time \'{}\' to the database'.format(existing_dataset.timepoint))

    response = base_station_schema.jsonify(existing_dataset)
    response.status_code = HTTPStatus.OK
    response.headers['location'] = '/api/v1/data/{}'.format(existing_dataset.id)

    return response


@weatherdata_blueprint.route('/<id>', methods=['DELETE'])
@access_level_required(Role.PUSH_USER)
@rollback_and_raise_exception
def delete_weather_dataset(id):
    existing_dataset = BaseStationData.query.get(id)
    if not existing_dataset:
        current_app.logger.info('Nothing to delete for dataset with id \'{}\' '.format(id))
        return '', HTTPStatus.NO_CONTENT

    db.session.delete(existing_dataset)
    db.session.commit()
    current_app.logger.info('Deleted dataset for time \'{}\' from the database'.format(existing_dataset.timepoint))

    response = base_station_schema.jsonify(existing_dataset)
    response.status_code = HTTPStatus.OK

    return response


@weatherdata_blueprint.route('/<id>', methods=['GET'])
@rollback_and_raise_exception
def get_one_weather_dataset(id):
    dataset = BaseStationData.query.get(id)
    if not dataset:
        raise APIError('No dataset with id \'{}\''.format(id), status_code=HTTPStatus.BAD_REQUEST)

    response = base_station_schema.jsonify(dataset)
    response.status_code = HTTPStatus.OK
    current_app.logger.info('Returned dataset for id \'{}\''.format(id))

    return response


@weatherdata_blueprint.route('/limits', methods=['GET'])
@rollback_and_raise_exception
def get_available_time_period():
    time_range = TimeRangeSchema()
    time_range.first = \
        db.session.query(BaseStationData.timepoint, db.func.min(BaseStationData.timepoint)).scalar()
    time_range.last = \
        db.session.query(BaseStationData.timepoint, db.func.max(BaseStationData.timepoint)).scalar()

    if not time_range.first or not time_range.last:
        raise APIError('No data in the database', status_code=HTTPStatus.NOT_FOUND)

    response = time_range_schema.jsonify(time_range)
    response.status_code = HTTPStatus.OK
    current_app.logger.info('Returned available time period: \'{}\'-\'{}\''.format(time_range.first, time_range.last))

    return response
