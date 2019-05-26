import os
from functools import wraps
from http import HTTPStatus
from logging.config import dictConfig

import pytz
from flask import Flask, request, jsonify
from flask_marshmallow import Marshmallow, fields, Schema
from flask_marshmallow.sqla import ModelSchema
from flask_sqlalchemy import SQLAlchemy

dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://flask.logging.wsgi_errors_stream',
        'formatter': 'default'
    }},
    'root': {
        'level': 'INFO',
        'handlers': ['wsgi']
    }
})

app = Flask(__name__)

if 'BASEDIR' in os.environ:
    basedir = os.environ['BASEDIR']
else:
    basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'crud.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
ma = Marshmallow(app)


class BaseStationData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timepoint = db.Column(db.DateTime, unique=True)
    temp = db.Column(db.Float)
    humidity = db.Column(db.Float)

    def __init__(self, timepoint, temp, humidity):
        self.timepoint = timepoint
        self.temp = temp
        self.humidity = humidity


class BaseStationDataSchema(ModelSchema):
    class Meta:
        strict = True
        model = BaseStationData


base_station_schema = BaseStationDataSchema()
base_stations_schema = BaseStationDataSchema(many=True)


class TimeRangeSchema(Schema):
    first = fields.fields.DateTime(required=True)
    last = fields.fields.DateTime(required=True)

    class Meta:
        strict = True


time_range_schema = TimeRangeSchema()


class APIError(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None, location=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload
        self.location = location

    def to_dict(self, hide_details=True):
        if hide_details and 500 <= self.status_code < 600:
            rv = {'error': '500 INTERNAL SERVER ERROR'}
        else:
            rv = dict(self.payload or ())
            rv['error'] = self.message

        return rv

    def __str__(self):
        return self.message


@app.before_first_request
def setup():
    db.create_all()


@app.errorhandler(APIError)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict(hide_details=True))
    response.status_code = error.status_code
    if error.location:
        response.headers['location'] = error.location
    app.logger.error('HTTP-Statuscode {}: {}'.format(error.status_code, error.to_dict(hide_details=False)))
    return response


def formatted_exception_str(e):
    error_type = type(e).__name__
    error_message_list = []
    for item in e.args:
        error_message_list.append(str(item))
    error_message = '. '.join(error_message_list)
    if not error_message:
        error_message = str(e)
        if not error_message:
            return error_type
    return error_type + ': ' + error_message


def deserialize_base_station_dataset(json):
    if not json:
        raise APIError('Required Content-Type is `application/json`', status_code=HTTPStatus.BAD_REQUEST)

    request_object = base_station_schema.load(json)
    return request_object.data


def to_utc(dt):
    if dt.tzinfo:
        timepoint = dt.astimezone(pytz.utc)
    else:
        timepoint = dt
    timepoint = timepoint.replace(tzinfo=None)

    return timepoint


def raise_api_error(e, status_code):
    if isinstance(e, APIError):
        raise e
    else:
        raise APIError(formatted_exception_str(e), status_code=status_code)


def rollback_and_raise_exception(func):
    @wraps(func)
    def wrapper(*args, **kwds):
        try:
            return func(*args, **kwds)
        except Exception as e:
            db.session.rollback()
            raise raise_api_error(e, status_code=HTTPStatus.INTERNAL_SERVER_ERROR)
        finally:
            db.session.close()
    return wrapper


@app.route('/api/v1/data', methods=['POST'])
@rollback_and_raise_exception
def add_weather_dataset():
    try:
        new_dataset = deserialize_base_station_dataset(request.json)
    except Exception as e:
        raise raise_api_error(e, status_code=HTTPStatus.BAD_REQUEST)

    existing_dataset = BaseStationData.query.filter_by(timepoint=new_dataset.timepoint).first()
    if not existing_dataset:
        db.session.add(new_dataset)
        db.session.commit()

        response = base_station_schema.jsonify(new_dataset)
        app.logger.info('Added new dataset for time \'{}\' to the database'.format(new_dataset.timepoint))
        response.status_code = HTTPStatus.CREATED
    else:
        raise APIError('Dataset for time \'{}\' already in the database'.format(new_dataset.timepoint),
                       status_code=HTTPStatus.CONFLICT, location='/api/v1/data/{}'.format(existing_dataset.id))

    response.headers['location'] = '/api/v1/data/{}'.format(new_dataset.id)

    return response


@app.route('/api/v1/data/<id>', methods=['PUT'])
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
    app.logger.info('Updated dataset for time \'{}\' to the database'.format(existing_dataset.timepoint))

    response = base_station_schema.jsonify(existing_dataset)
    response.status_code = HTTPStatus.OK
    response.headers['location'] = '/api/v1/data/{}'.format(existing_dataset.id)

    return response


@app.route('/api/v1/data/<id>', methods=['DELETE'])
@rollback_and_raise_exception
def delete_weather_dataset(id):
    existing_dataset = BaseStationData.query.get(id)
    if not existing_dataset:
        app.logger.info('Nothing to delete for dataset with id \'{}\' '.format(id))
        return '', HTTPStatus.NO_CONTENT

    db.session.delete(existing_dataset)
    db.session.commit()
    app.logger.info('Deleted dataset for time \'{}\' from the database'.format(existing_dataset.timepoint))

    response = base_station_schema.jsonify(existing_dataset)
    response.status_code = HTTPStatus.OK

    return response


@app.route('/api/v1/data', methods=['GET'])
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
    app.logger.info('Returned {} datasets from \'{}\'-\'{}\''.format(len(matching_datasets), first, last))

    return response


@app.route('/api/v1/data/<id>', methods=['GET'])
@rollback_and_raise_exception
def get_one_weather_dataset(id):
    dataset = BaseStationData.query.get(id)
    if not dataset:
        raise APIError('No dataset with id \'{}\''.format(id), status_code=HTTPStatus.BAD_REQUEST)

    response = base_station_schema.jsonify(dataset)
    response.status_code = HTTPStatus.OK
    app.logger.info('Returned dataset for id \'{}\''.format(id))

    return response


@app.route('/api/v1/data/limits', methods=['GET'])
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
    app.logger.info('Returned available time period: \'{}\'-\'{}\''.format(time_range.first, time_range.last))

    return response


# will only be executed if running directly with Python
if __name__ == '__main__':
    db.create_all()
    app.run(host='0.0.0.0')
