import dash
from dash import Dash, html, dcc, Input, Output, ctx, callback
import pandas as pd
import geopandas as gpd
import numpy as np
import shapely.geometry
import plotly.express as px
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
import json



#Register dash page
dash.register_page(__name__,
                   path='/population-healthcare',
                   title='Population and Healthcare',
                   name='Population and Healthcare',
                   order=2,
)


desc = "The current population of NCR is 13,484,462, accounting for about 12.37% of the Philippine population based on the 2020 Census of Population and Housing (2020 CPH). The population is higher by 607,209 from the 2015 census, with Quezon City, Manila, and Caloocan having the highest number of inhabitants. The LGUs constantly remind barangays near the WVF to move out of the fault line as they risk receiving catastrophic damages."
desc_2 = "Access to health facilities is crucial in a post-earthquake situation. The total number of hospitals in Metro Manila is 155, divided into three levels according to their functional capacity. Level 1 is general hospitals, including operating and recovery rooms; Level 2 has available ICU and respiratory services, and Level 3 has physical rehabilitation units and a blood bank. The surge of critical care demand after an earthquake will be a significant challenge to our healthcare system, in addition to continuing their baseline services to their current patients."

ncr_hosp = gpd.read_file('../data/analytics/ncr_hosp.geojson',driver='GeoJSON')
fault_lines_ph = gpd.read_file('../data/analytics/fault_lines_ph.geojson', driver='GeoJSON')
population_ncr = gpd.read_file('../data/analytics/ncr_boundary_pop.geojson', driver='GeoJSON')

hosp_data = ncr_hosp[['facility_name','service_capability','bed_capacity']]
hosp_data['facility_name'] = hosp_data['facility_name'].str.title()

#Set api token
px.set_mapbox_access_token(open("assets/.mapbox_token").read())
token = open("assets/.mapbox_token").read()

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

fault_fig = px.line_mapbox(
    lat=lats,
    lon=lons,
    hover_name=names,
    color=len(names)*["fault line"],
    color_discrete_map={"fault line":"#FF0000"},
)

fault_fig.update_traces(customdata= pd.DataFrame(names),
                        hovertemplate='Fault Name: %{customdata[0]}<extra></extra>')


#population plot
pop_fig = px.choropleth_mapbox(
    data_frame=population_ncr,
    geojson=population_ncr.geometry,
    locations=population_ncr.index,
    color='population',
)

pop_fig.update_traces(customdata= population_ncr[["barangay", "city", "population"]],
                      hovertemplate=
                      'Barangay Name: %{customdata[0]}<br>' +
                      'Municipality: %{customdata[1]}<br>' + 
                      'Population: %{customdata[2]}')

#Hospital Plot
lats_hosp = []
lons_hosp = []

for index, data in ncr_hosp.iterrows():
    lats_hosp.append(data.geometry.y)
    lons_hosp.append(data.geometry.x)

hosp_fig = go.Figure(go.Scattermapbox(
    lat=lats_hosp,
    lon=lons_hosp,
    mode="markers",
    marker = {'size': 15, 'symbol': "hospital", "color":"yellow"},
    customdata=hosp_data,
    hovertemplate=
    'Hospital Name: %{customdata[0]}<br>' +
    'Service Capability: %{customdata[1]}<br>' +
    'Bed Capacity: %{customdata[2]}<br>' + 
    '<extra></extra>'
))


layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.Div([
                html.Span('Growing Population and Healthcare Dynamics',
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
                            "text-align": "justify"
                        })
            ], style={"margin-top":"15px"})         
        ], width=3),
        dbc.Col([
            dbc.Row([
                dbc.Checklist(
                    options=[
                        {"label": "Barangay Population", "value": "Population"},
                        {"label": "Hospitals", "value": "Hospitals"},
                        {"label": "Fault Lines", "value": "Fault Lines"},
                    ],
                    value=["Population", "Hospitals", "Fault Lines"],
                    id="switches-input",
                    switch=True,
                    inline=True,
                    input_checked_style={
                        "backgroundColor": "#1d1a1a",
                        "borderColor": "#1d1a1a",
                        "box-shadow": "0 0 1px #1d1a1a"}
                ),
            ]),
            dbc.Row([
                dcc.Graph(id='map-plot')
            ]),
        ], width=9, className="custom-margin"),
    ]),
], fluid=True, style = {'display': 'flex', 'flexDirection': 'column', 'height': '90vh',})

@callback(
        Output("map-plot", "figure"),
        Input("switches-input", "value"),
)
def update_map(selected_maps):
    fig = go.Figure()

    if "Population" in selected_maps:
        fig.add_trace(pop_fig.data[0])
        fig.update_coloraxes(colorscale="Viridis",
                             cmin=population_ncr['population'].quantile(0.05),
                             cmax=population_ncr['population'].quantile(0.99),)
    if "Hospitals" in selected_maps:
        fig.add_trace(hosp_fig.data[0])
    if "Fault Lines" in selected_maps:
        fig.add_trace(fault_fig.data[0])

    fig.update_layout(
    margin={'l': 0, 't': 0, 'b': 0, 'r': 0},
    mapbox={
        'center': {'lon': 120.9967449, 'lat': 14.60785},
        'style': "dark",
        'zoom': 10},
    mapbox_accesstoken=token,
    showlegend=False,
    height=800
    )

    return fig
