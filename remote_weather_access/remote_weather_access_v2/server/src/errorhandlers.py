from http import HTTPStatus

from flask import jsonify, current_app

from .exceptions import APIError


def handle_invalid_usage(error):
    response = jsonify(error.to_dict(hide_details=True))
    response.status_code = error.status_code
    if error.location:
        response.headers['location'] = error.location
    current_app.logger.error('HTTP-Statuscode {}: {}'.format(error.status_code, error.to_dict(hide_details=False)))

    return response


def unauthorized_response(callback):
    error = APIError('Missing Authorization header', status_code=HTTPStatus.UNAUTHORIZED)
    response = jsonify(error.to_dict(hide_details=False))
    response.status_code = error.status_code
    current_app.logger.error('HTTP-Statuscode {}: {}'.format(error.status_code, error.to_dict(hide_details=False)))
    return response
