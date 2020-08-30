from http import HTTPStatus

from flask import Blueprint, jsonify, current_app

from ..exceptions import APIError
from ..extensions import db
from ..models import TempHumiditySensor
from ..utils import with_rollback_and_raise_exception, access_level_required, Role

temp_humidity_sensor_blueprint = Blueprint('temp_humidity_sensor', __name__, url_prefix='/api/v1/temp-humidity-sensor')


@temp_humidity_sensor_blueprint.route('', methods=['GET'])
@access_level_required(Role.GUEST)
@with_rollback_and_raise_exception
def get_all_temp_humidity_sensors():
    sensor_data = db.session.query(TempHumiditySensor).all()

    current_app.logger.info('Provided details of all {} temperature-humidity sensors'.format(len(sensor_data)))
    response = jsonify(sensor_data)
    response.status_code = HTTPStatus.OK
    return response


@temp_humidity_sensor_blueprint.route('/<sensor_id>', methods=['GET'])
@access_level_required(Role.GUEST)
@with_rollback_and_raise_exception
def get_a_temp_humidity_sensor(sensor_id):
    sensor_id = sensor_id.upper()
    sensor_data = (db.session
                   .query(TempHumiditySensor)
                   .filter(TempHumiditySensor.sensor_id == sensor_id)
                   .one_or_none())

    if not sensor_data:
        raise APIError('No such temperature-humidity sensor', status_code=HTTPStatus.BAD_REQUEST)
    else:
        current_app.logger.info('Provided details for temperature-humidity sensor \'{}\''.format(sensor_id))

        response = jsonify(sensor_data)
        response.status_code = HTTPStatus.OK
        return response
