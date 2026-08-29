#  Remote Weather Access - Client/server solution for distributed weather networks
#   Copyright (C) 2013-2023 Ralf Rettig (info@personalfme.de)
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.

from django.apps import AppConfig


class WeatherpageConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'weatherpage'

    def ready(self):
        _provide_a_secret_key_to_the_dash_apps()


def _provide_a_secret_key_to_the_dash_apps():
    """Dash signs its callback handles with the `secret_key` of the server it runs on. The `PseudoFlask` server
    provided by django-plotly-dash does not initialize the Flask configuration, so that reading the key raises a
    `KeyError` instead of returning `None` and rendering any page fails. Setting the key on the class provides it
    to all instances, as django-plotly-dash creates one server per Dash app when handling a request."""
    from django.conf import settings
    from django_plotly_dash.dash_wrapper import PseudoFlask

    PseudoFlask.secret_key = settings.SECRET_KEY
