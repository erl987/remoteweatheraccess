#!/usr/bin/env python
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
import sys

try:
    if len(sys.argv) == 2 and sys.argv[1] == '-v':
        print('TE923 weather station mock')
    elif len(sys.argv) == 2 and sys.argv[1] == '-b':
        raise AssertionError('The mock failed intentionally')
    elif len(sys.argv) == 1:
        raise AssertionError('The mock failed intentionally')
    else:
        raise SyntaxError('Invalid syntax: {}'.format(sys.argv))
except Exception as e:
    print(str(e) + '\n', file=sys.stderr)
    sys.exit(1)
