# RemoteWeatherAccess - Weather network connecting to remote stations
# Copyright(C) 2013-2016 Ralf Rettig (info@personalfme.de)
#
# This program is free software: you can redistribute it and / or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.If not, see <http://www.gnu.org/licenses/>


def a(builder):
    """
    Convenience wrapper for a test object builder factory

    :param builder:     builder factory
    :type builder:      some object builder exposing a build() method
    :return:            object created by the builder
    :rtype:             type of the builder object
    """
    return builder.build()


def some(builder):
    """
    Convenience wrapper for a test object builder factory

    :param builder:     builder factory
    :type builder:      some object builder exposing a build() method
    :return:            object created by the builder
    :rtype:             type of the builder object
    """
    return builder.build()


def an(builder):
    """
    Convenience wrapper for a test object builder factory

    :param builder:     builder factory
    :type builder:      some object builder exposing a build() method
    :return:            object created by the builder
    :rtype:             type of the builder object
    """
    return builder.build()