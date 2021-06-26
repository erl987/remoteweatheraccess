#  Remote Weather Access - Client/server solution for distributed weather networks
#   Copyright (C) 2013-2020 Ralf Rettig (info@personalfme.de)
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

import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html


def ModalDialog(the_id, dialog_content):
    return html.Div(
        [
            dbc.Modal(
                id='{}-dialog'.format(the_id),
                size='xl',
                children=[
                    dbc.ModalBody(
                        dcc.Markdown(dialog_content),
                        className='modal-dialog-content'),
                    dbc.ModalFooter(
                        dbc.Button(
                            'Schließen',
                            id='close-{}'.format(the_id),
                            className='ml-auto')
                    ),
                ]
            )
        ]
    )
