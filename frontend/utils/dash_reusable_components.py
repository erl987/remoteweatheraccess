import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc


def NamedDropdown(name, **kwargs):
    return html.Div(
        style={"margin": "10px 0px"},
        children=[
            html.P(className="label", children="{}".format(name), style={"margin-left": "3px"}),
            dcc.Dropdown(**kwargs),
        ],
    )


def NamedInput(name, **kwargs):
    return html.Div(
        style={"margin": "10px 0px"},
        children=[
            html.P(className="label", children="{}".format(name), style={"margin-left": "3px"}),
            dcc.Input(**kwargs)
        ]
    )


def NamedDatePickerRange(name, **kwargs):
    return html.Div(
        style={"margin": "10px 0 px"},
        children=[
            html.P(className="label", children="{}".format(name), style={"margin-left": "3px"}),
            dcc.DatePickerRange(**kwargs)
        ]
    )


def NamedTabs(name, **kwargs):
    return html.Div(
        className="named-tab",
        style={"margin": "10px 0 px"},
        children=[
            html.P(className="label", children="{}".format(name), style={"margin-left": "3px"}),
            dcc.Tabs(**kwargs)
        ]
    )


def ModalDialog(id, button_text, dialog_content, className):
    return html.Div(
        children=[
            dbc.Button(
                button_text,
                id="open-{}".format(id),
                className=className),
            dbc.Modal(
                id="{}-dialog".format(id),
                size="xl",
                children=[
                    dbc.ModalBody(
                        dcc.Markdown(dialog_content),
                        className="modal-dialog-content"),
                    dbc.ModalFooter(
                        dbc.Button(
                            "Schließen",
                            id="close-{}".format(id),
                            className="ml-auto")
                    ),
                ]
            )
        ]
    )
