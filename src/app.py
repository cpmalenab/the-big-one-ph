import dash
from dash import html, dcc
import dash_bootstrap_components as dbc

app = dash.Dash(__name__, 
                use_pages=True, 
                external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.FONT_AWESOME],
                assets_folder='assets',
                suppress_callback_exceptions=True)
server = app.server

from assets.nav import sidebar

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            sidebar
            ], width=2, style={"padding-left": "0px"}),
    dbc.Col([
            dbc.Row([
                    dash.page_container
                ])
        ], width=10)
])
], fluid=True)

if __name__ == "__main__":
    app.run(debug=False)