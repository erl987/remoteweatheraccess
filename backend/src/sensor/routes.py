from http import HTTPStatus

from flask import Blueprint, jsonify

from .models import Sensor
from ..exceptions import APIError
from ..extensions import db
from ..utils import with_rollback_and_raise_exception

sensor_blueprint = Blueprint('sensor', __name__, url_prefix='/api/v1/sensor')


@sensor_blueprint.route('', methods=['GET'])
@with_rollback_and_raise_exception
def get_all_temp_humidity_sensors():
    sensor_ids = Sensor.query.with_entities(Sensor.sensor_id).all()
    sensor_ids = [sensor_id for sensor_id, in sensor_ids]

    response = jsonify(sensor_ids)
    response.status_code = HTTPStatus.OK
    return response


@sensor_blueprint.route('/<sensor_id>', methods=['GET'])
@with_rollback_and_raise_exception
def get_a_temp_humidity_sensor(sensor_id):
    sensor_id = sensor_id.lower()
    sensor_data = (db.session
                   .query(Sensor)
                   .filter(Sensor.sensor_id == sensor_id)
                   .one_or_none())

    if not sensor_data:
        raise APIError('No sensor with id \'{}\''.format(sensor_id), status_code=HTTPStatus.BAD_REQUEST)
    else:
        response = jsonify(sensor_data)
        response.status_code = HTTPStatus.OK
        return response
