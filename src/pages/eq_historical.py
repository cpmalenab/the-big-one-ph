import os
import dash
from dash import Dash, html, dcc, Input, Output, ctx, callback
import geopandas as gpd
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import shapely.geometry
import dash_bootstrap_components as dbc
import json


#Register dash page
dash.register_page(__name__,
                   path='/',
                   title='Seismicity of Metro Manila',
                   name='Seismicity of Metro Manila',
                   order=1,
)

desc = "Located along the “Pacific Ring of Fire,” the Philippines experiences an average of 100-150 earthquakes yearly with a magnitude of 4.0 and above. Within 500km radius of Metro Manila, the average number of significant earthquakes(M≥5.0) per year is eight based on an earthquake catalog for the past 123 years. Some of the most devastating earthquakes were the 2022 Luzon Earthquake (M7.0), the 1990 Panay Earthquake (M7.1), and the 1990 Luzon earthquake (M7.7), leaving 2,412 people dead and an estimated $369 million worth of damages."
desc_2 = "The country has at least 175 active faults and the West Valley Fault (WVF), spanning Bulacan, Rizal, Metro Manila, Cavite, and Laguna, is projected to trigger an earthquake exceeding 7.2 in magnitude, commonly called \"The Big One\". PHIVOLCS claims that the WVF has a movement interval of 400 to 600 years, with the last movement recorded in 1658. Thus, it is impending that \"The Big One\" can happen in our generation."

#Import files
earthquake_history = pd.read_csv("../data/analytics/earthquake_data.csv", parse_dates=['time'])
fault_lines_ph = gpd.read_file("../data/analytics/fault_lines_ph.geojson", driver="GeoJSON")
eq_rate_df = pd.read_csv("../data/analytics/eq_rate_df.csv")

#Set api token
mapbox_token = os.environ.get('MAPBOX_TOKEN')
px.set_mapbox_access_token(mapbox_token)
token = mapbox_token

#earthquake rate
rate_fig = px.bar(eq_rate_df,
    x="no_eq",
    y="p",
    color="p",
    color_continuous_scale="Oranges",
    range_color=(0, eq_rate_df.p.max()),
    labels={"no_eq": "No. of Significant Earthquakes(M≥5.0) per Year"},
    width =350,
    height=250
  )

rate_fig.update_layout(coloraxis_showscale=False,
                       plot_bgcolor='white',
                       margin ={'l':0,'t':0,'b':0,'r':0})
rate_fig.update_layout(yaxis_visible=False,
                       yaxis_showticklabels=False,
                       xaxis=dict(dtick=2))

#Fault Line Plot
lats = []
lons = []
names = []


for feature, name in zip(fault_lines_ph.geometry, fault_lines_ph.name):
    if isinstance(feature, shapely.geometry.linestring.LineString):
        linestrings = [feature]
    elif isinstance(feature, shapely.geometry.multilinestring.MultiLineString):
        linestrings = feature.geoms
    else:
        continue
    for linestring in linestrings:
        x, y = linestring.xy
        lats = np.append(lats, y)
        lons = np.append(lons, x)
        names = np.append(names, [name]*len(y))
        lats = np.append(lats, None)
        lons = np.append(lons, None)
        names = np.append(names, None)

eq_fig = px.line_mapbox(
    lat=lats,
    lon=lons,
    hover_name=names,
    color=len(names)*["fault line"],
    color_discrete_map={"fault line":"#FF0000"},
)
eq_fig.update_traces(customdata= pd.DataFrame(names),
                     hovertemplate='Fault Name: %{customdata[0]}<extra></extra>')

layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.Div([
                html.Span('Seismic Story',
                          style={
                              "font-size":"3rem",
                              "font-family":"Cardo ,serif",
                              "font-weight":"400",
                              "line-height":"1.04",
                              "margin-bottom":"10px",
                          }),
                html.P([html.Br(),
                        desc,
                        html.Br(), html.Br(),
                        dcc.Graph(figure=rate_fig),
                        html.Br(), html.Br(),
                        desc_2,],
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
            dbc.Row([
                dcc.Graph(id='map-graph')
            ]),
            dbc.Row([
                dcc.RangeSlider(
                    id='slider-year',
                    min=1900,
                    max=2023,
                    step=3,
                    value=[1900, 2023],
                    marks={str(yr): str(yr) for yr in range(1900, 2023, 10)},
                )
            ], style={"padding-top":"25px"}),
        ], width=9, className="custom-margin"),
    ]),
], fluid=True, style = {'display': 'flex', 'flexDirection': 'column', 'height': '90vh',})

@callback(
        Output("map-graph", "figure"),
        Input("slider-year", "value"),
)
def update_map(slider_year):

    filtered_df = earthquake_history[earthquake_history['time'].dt.year.between(slider_year[0], slider_year[1])]

    eq_fig.data = [eq_fig.data[0]]

    color_bin = {'7.0-7.9':'#f03b20', '6.0-6.9':'#feb24c', '5.0-5.9':'#ffeda0'}

    for group, data in filtered_df.groupby('mag_group'):
        eq_fig.add_trace(go.Scattermapbox(
            lat=data['latitude'],
            lon=data['longitude'],
            mode="markers",
            name=group,
            marker={'size':7, "color":color_bin[group]},
            customdata=data,
            hovertemplate=
            'Magnitude: %{customdata[2]}<br>' +
            'Magnitude Type: %{customdata[3]}<br>' +
            'Time: %{customdata[8]}<br>' + 
            'Location: %{customdata[5]}<br>' +
            'Depth: %{customdata[6]} km'
            '<extra></extra>'
        ))

    eq_fig.update_layout(
    margin ={'l':0,'t':0,'b':0,'r':0},
    mapbox = {
        'center': {'lat': 14.5826, 'lon': 120.9787},
        'style': "dark",
        'zoom': 5},
    mapbox_accesstoken=token,
    showlegend=True,
    legend_title_text='Magnitude',
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1,
        xanchor="left",
        x=0),
    height=800
)

    return eq_fig
