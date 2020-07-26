from http import HTTPStatus

from flask import Blueprint, jsonify

from ..exceptions import APIError
from ..extensions import db
from ..utils import with_rollback_and_raise_exception
from ..weatherdata.models import TempHumiditySensor

temp_humidity_sensor_blueprint = Blueprint('temp_humidity_sensor', __name__, url_prefix='/api/v1/temp-humidity-sensor')


@temp_humidity_sensor_blueprint.route('', methods=['GET'])
@with_rollback_and_raise_exception
def get_all_temp_humidity_sensors():
    sensor_ids = TempHumiditySensor.query.with_entities(TempHumiditySensor.sensor_id).all()
    sensor_ids = [sensor_id for sensor_id, in sensor_ids]

    response = jsonify(sensor_ids)
    response.status_code = HTTPStatus.OK
    return response


@temp_humidity_sensor_blueprint.route('/<sensor_id>', methods=['GET'])
@with_rollback_and_raise_exception
def get_a_temp_humidity_sensor(sensor_id):
    sensor_id = sensor_id.upper()
    sensor_data = (db.session
                   .query(TempHumiditySensor)
                   .filter(TempHumiditySensor.sensor_id == sensor_id)
                   .one_or_none())

    if not sensor_data:
        raise APIError('No temp_humidity_sensor with id \'{}\''.format(sensor_id), status_code=HTTPStatus.BAD_REQUEST)
    else:
        response = jsonify(sensor_data)
        response.status_code = HTTPStatus.OK
        return response
