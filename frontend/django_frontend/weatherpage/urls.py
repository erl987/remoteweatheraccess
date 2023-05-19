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

from django.urls import path, register_converter

from . import views
from .converters import StationIDConverter

register_converter(StationIDConverter, 'SSS')

app_name = 'weatherpage'
urlpatterns = [
    path('', views.main, name='index'),
    path('<SSS:station_id>/', views.main_for_station, name='index_station'),
    path('impress/', views.impress, name='impress'),
    path('policy/', views.policy, name='policy')
]