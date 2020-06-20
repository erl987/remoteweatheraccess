import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc


def ModalDialog(id, button_text, dialog_content, className):
    return html.Div(
        [
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
