from dash import html
import dash_bootstrap_components as dbc
import dash

sidebar = dbc.Container([
	dbc.Row([
        dbc.Col([
            html.Div([
                html.I(className="fa-solid fa-wave-square")
                ],className='logo')
        ], width=3, style={"padding":"0px"}),
        dbc.Col([html.H1(['The Big One PH'], className='app-brand'),
                 ], width=9, style={"padding-right":"2px"})
	]),
	dbc.Row([
        dbc.Nav(
	        [dbc.NavLink(page["name"], 
                      active='exact', 
                      href=page["path"],
                      style={"color": "white"}) for page in dash.page_registry.values()],
	        vertical=True, 
            pills=True, 
            class_name='my-nav')
    ])
], class_name = 'my-sidebar')

