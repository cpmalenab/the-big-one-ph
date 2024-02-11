import dash
from dash import Dash, html, dcc, Input, Output, ctx, callback
import pandas as pd
import geopandas as gpd
import plotly.express as px
import dash_bootstrap_components as dbc
import json
import os

#Register dash page
dash.register_page(__name__,
                   path='/earthquake-impact',
                   title='Earthquake Impact',
                   name='Earthquake Impact',
                   order=3,
)

desc = "A potential Magnitude 7.2 earthquake along the West Valley Fault System could have devasting effects, including destruction of the built environment, casualties, and economic losses. \"The Big One\" can paralyze the Philippine economy as Metro Manila contributes to about 32% of the national GDP. World Bank estimates the number of fatalities to be 48,000 and $48 billion in financial losses. Quezon City, Manila, and Pasig are among the municipalities that will be severely affected by the aftermath of \"The Big One\"."
desc_2 = "For disaster mitigation priorities, PHIVOLCS stated that the normalized proportional damage (per square km) is a better indicator of regions with the highest consequence regarding the number of people affected. Las Pinas, Pasay, and Caloocan are the top candidates for prioritizing emergency response and mitigation programs. The approach for disaster management response in the graphs is appropriate for residential areas only, and engineers should evaluate the damage to critical facilities (airports, hospitals, schools, etc) on a case-by-case basis."

#Import data
earthquake_impact_total_gdf = gpd.read_file('../data/analytics/earthquake_impact_total_gdf.geojson',
                                            driver='GeoJSON')
earthquake_impact_total = pd.read_csv('../data/analytics/earthquake_impact_total.csv')
earthquake_impact = pd.read_csv('../data/analytics/earthquake_impact.csv')

#Set index for choropleth maps
earthquake_impact_total_gdf = earthquake_impact_total_gdf.set_index('municipality')

#Set api token using environment variables
mapbox_token = os.environ.get('MAPBOX_TOKEN')
px.set_mapbox_access_token(mapbox_token)

#Set api token using .mapbox_token in assets folder
# px.set_mapbox_access_token(open("assets/.mapbox_token").read())

#Dash App Layout
layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.Div([
                html.Span('Bracing for the Worst',
                            style={
                                "font-size":"3rem",
                                "font-family":"Cardo ,serif",
                                "font-weight":"400",
                                "line-height":"1.04",
                                "margin-bottom":"10px",
                        }),
                html.P([html.Br(), desc, html.Br(), html.Br(), desc_2],
                        style={
                            "font-size":"1rem",
                            "font-family":"Josefin Sans,,sans-serif",
                            "font-weight":"400",
                            "line-height":"1.46429em",
                            "text-align":"justify"
                        })
            ], style={"margin-top":"15px"})
        ], width=3),
        dbc.Col([
            html.Div([
                dbc.RadioItems(
                    id="impact-radios",
                    className="btn-group",
                    inputClassName="btn-check",
                    labelClassName="btn btn-outline-dark",
                    labelCheckedClassName="active",
                    options=[
                        {"label": "Building Damage", "value": "Building Damage"},
                        {"label": "Casualties", "value": "Casualties"},
                        {"label": "Economic Loss", "value": "Economic Loss"},
                    ],
                    value="Building Damage",
                ),
            ], className="radio-group"),
            html.Div([
                dbc.Row([
                    html.H4(id="total-title"),
                    dcc.Loading(id='total_title_loading',
                                type='circle',
                                children=dcc.Graph(id="bar-chart-total"))
                ]),
                dbc.Row([
                    dcc.Loading(id='damage_states_loading',
                                type='circle',
                                children=dbc.Col(id="damage-states")),
                ])
            ], style={"margin-top":"15px"})
        ], width=4, className="custom-margin"),
        dbc.Col([
            html.Div([
                dbc.RadioItems(
                    id="rate-radios",
                    className="btn-group",
                    inputClassName="btn-check",
                    labelClassName="btn btn-outline-dark",
                    labelCheckedClassName="active",
                    options=[
                        {"label": "Total", "value": "total"},
                        {"label": "Per Square KM", "value": "normalized"},
                    ],
                    value="total",
                ),
            ], className="radio-group"),
            html.Div([
                dbc.Row([
                    dcc.Loading(id='choroplth_map_loading',
                                type='circle',
                                children=dcc.Graph(id="choropleth-map"))
                ])
            ], style={"margin-top":"15px"})
        ], width=5, className="custom-margin"),
    ])
], fluid=True, style = {'display': 'flex', 'flexDirection': 'column', 'height': '90vh',})

#callback from buttons
@callback(
        Output('choropleth-map', 'figure'),
        Output('bar-chart-total', 'figure'),
        Output('total-title', 'children'),
        Input('impact-radios', 'value'),
        Input('rate-radios', 'value'),
)
def create_graph(impact_type, rate):

    impact_df = earthquake_impact_total_gdf[(earthquake_impact_total_gdf['impact_type'] == impact_type) &
                                            (earthquake_impact_total_gdf['rate'] == rate)]

    impact_fig = px.choropleth_mapbox(impact_df,
                                      geojson=impact_df.geometry,
                                      locations=impact_df.index,
                                      color_continuous_scale="Reds",
                                      color='value',
                                      range_color=(0,impact_df.value.max()),
                                      center={'lat': 14.5826, 'lon': 120.9787},
                                      opacity=0.5,
                                      zoom=9.5,
                                      mapbox_style="dark",
                                      title = f"{impact_type}",
                                      height=800)
    impact_fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})

    impact_bar_df = earthquake_impact_total[(earthquake_impact_total['impact_type'] == impact_type) &
                                            (earthquake_impact_total['rate'] == rate)]
    sorted_df = impact_bar_df.sort_values('value')

    impact_bar_fig = px.bar(sorted_df,
                            x="value",
                            y="municipality",
                            color="value",
                            color_continuous_scale="Reds",
                            range_color=(0, sorted_df.value.max()),
                            labels={
                                "municipality": "Municipality",
                                "value":"Value"}, 
                            # title=f"{impact_type} per LGU",
                            height=400)
    impact_bar_fig.update_layout(coloraxis_showscale=False, plot_bgcolor='white')

    return impact_fig, impact_bar_fig, f"{impact_type} per Municipality"

# call back for damage states
@callback(
    Output('damage-states', 'children'),
    Input('bar-chart-total', 'clickData'),
    Input('choropleth-map', 'clickData'),
    Input('impact-radios', 'value'),
    Input('rate-radios', 'value'),
)
def select_municipality(bar_click, map_click, impact_type, rate):
    triggered_id = ctx.triggered_id

    municipality = 'Manila'
    if triggered_id == 'bar-chart-total':
        municipality = bar_click['points'][0]['y']
    elif triggered_id == 'choropleth-map':
        municipality = map_click['points'][0]['location']

    municipality_df = earthquake_impact[(earthquake_impact['municipality'] == municipality) &
                                        (earthquake_impact['impact_type'] == impact_type) &
                                        (earthquake_impact['rate'] == rate)]

    municipality_fig = px.bar(municipality_df,
                              x="value",
                              y="state",
                              color="value",
                              color_continuous_scale="blugrn",
                              range_color=(0,municipality_df['value'].max()),
                              labels={
                                "state": "Damage States",
                                "value":"Value"},
                              height=400)
    municipality_fig.update_layout(coloraxis_showscale=False,
                                   plot_bgcolor='white')

    if impact_type != 'Economic Loss':
        display = html.Div([
            html.H4(f"{impact_type} States of {municipality}"),
            dcc.Graph(figure=municipality_fig)
        ])
    else:
        economic_loss = int(municipality_df[municipality_df['municipality'] == municipality]['value'])
        display = html.Div([
            html.H4(f"Economic Loss of {municipality}"),
            html.H5(f"₱{economic_loss} Million", className="economic-loss")
        ])

    return display
