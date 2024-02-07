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
import os

#Register dash page
dash.register_page(__name__,
                   path='/liquefaction-potential',
                   title='Liquefaction Potential',
                   name='Liquefaction Potential',
                   order=4,
)

desc = "Soil liquefaction is a geologic hazard that results when soil loses its density, turning it into a liquid-like state. The ground deformations can significantly damage roads, pipes, and critical infrastructures, hindering emergency response efforts and recovery. The liquefaction map of Metro Manila shows the areas more susceptible to ground subsidence at varying degrees (Low, Moderate, and High Potential). Metro Manila's western and eastern regions are expected to have difficulties accessing critical services due to the liquefaction-induced damage to transport networks."
desc_2 = "Out of 155 hospitals, 74 are lying in liquefiable areas, with 11,919 beds at risk of not being accessible to the population. "

#import files
liquefaction_map = gpd.read_file("../data/analytics/liquefaction_map.geojson", driver='GeoJSON')
liqf_roadways_gdf = gpd.read_file("../data/analytics/liqf_roadways_gdf.geojson", driver='GeoJSON')
ncr_hosp = gpd.read_file('../data/analytics/ncr_hosp.geojson', driver='GeoJSON')
liqf_potential_hosp =pd.read_csv("../data/analytics/liquefaction_potential_hospital.csv")
liqf_potential_capacity = pd.read_csv("../data/analytics/liquefaction_potential_capacity.csv")

#Set api token
mapbox_token = os.environ.get('MAPBOX_TOKEN')
px.set_mapbox_access_token(mapbox_token)
token = mapbox_token

#Liquefaction map with hospitals
liqf_traces = []
lats_hosp = []
lons_hosp = []

colors = {'HP':'#f03b20', 'MP':'#feb24c', 'LP':'#ffeda0'}
legendgroup = {'HP':'High Potential', 'MP':'Moderate Potential', 'LP':'Low Potential'}

for area in liquefaction_map.iterrows():
    lons = list(area[1].geometry.exterior.coords.xy[0])
    lats = list(area[1].geometry.exterior.coords.xy[1])

    customdata_df = pd.DataFrame(len(lons)*[area[1].potential])

    liqf_traces.append(go.Scattermapbox(
        fill = "toself",
        lon = lons,
        lat = lats,
        marker = {'size': 5, 'color': colors[area[1].Name[:2]]},
        legendgroup= legendgroup[area[1].Name[:2]],
        legendgrouptitle_text= legendgroup[area[1].Name[:2]],
        name=area[1].Name,
        customdata=customdata_df,
        hovertemplate=
        'Liquefaction Potential: %{customdata[0]}<br>' +
        '<extra></extra>')
                    )

liquefaction_fig = go.Figure()
for trace in liqf_traces:
    liquefaction_fig.add_trace(trace)

hosp_data = ncr_hosp[['facility_name','service_capability','bed_capacity']]
hosp_data['facility_name'] = hosp_data['facility_name'].str.title()

for index, data in ncr_hosp.iterrows():
    lats_hosp.append(data.geometry.y)
    lons_hosp.append(data.geometry.x)

liquefaction_fig.add_trace(go.Scattermapbox(
        lat=lats_hosp,
        lon=lons_hosp,
        mode="markers",
        marker = {'size': 15, 'symbol': "hospital", "color":"green"},
        name='Hospitals',
        customdata=hosp_data,
        hovertemplate=
        'Hospital Name: %{customdata[0]}<br>' +
        'Service Capability: %{customdata[1]}<br>' +
        'Bed Capacity: %{customdata[2]}<br>' + 
        '<extra></extra>'
    ))


liquefaction_fig.update_layout(
    margin ={'l':0,'t':0,'b':0,'r':0},
    mapbox = {
        'center': {'lon': 120.9787, 'lat': 14.5826},
        'style': "dark",
        'zoom': 9.5},
    mapbox_accesstoken=token,
    height=800,
    legend_title_text='Liquefaction Potential')

#grouped bar chart of hospitals on liquefiable areas
liqf_hosp_fig = px.bar(liqf_potential_hosp, 
                       x="facility_name", 
                       y="service_capability",
                       color="type", barmode="group",
                       labels={
                           "type": "Liquefaction Potential",
                           "facility_name": "No. of Hospitals",
                           "service_capability":"Service Capability"},
                       color_discrete_map={'High Potential':'#f03b20',
                                           'Moderate Potential':'#feb24c', 
                                           'Low Potential':'#ffeda0'},
                       title="Hospitals Lying on Liquefiable Areas",
                       height=400)
liqf_hosp_fig.update_yaxes(autorange="reversed")
liqf_hosp_fig.update_layout(plot_bgcolor='white', showlegend=False)

#bar chart for bed capacity on liquefiable areas
liqf_bed_fig = px.bar(liqf_potential_capacity,
                      x="bed_capacity",
                      y="type",
                      color="type",
                      labels={
                          "type": "Liquefaction Potential",
                          "bed_capacity": "Bed Capacity",},
                      color_discrete_map={'High Potential':'#f03b20',
                                          'Moderate Potential':'#feb24c', 
                                          'Low Potential':'#ffeda0'},
                      title="Bed Capacities Lying on Liquefiable Areas",
                      height=400)
liqf_bed_fig.update_layout(plot_bgcolor='white', showlegend=False)

#Road ways affected 
colors = {"motorway":"#33a02c", "trunk":"#e31a1c", "primary":"#1f78b4", "secondary":"#fdbf6f", 
          "tertiary":"#fb9a99", "unclassified":"#b2df8a", "residential":"#a6cee3"}
traces = []

for highway_type in liqf_roadways_gdf['type'].unique():
    gdf_by_type = liqf_roadways_gdf[liqf_roadways_gdf['type'] == highway_type]

    lats = []
    lons = []
    names = []

    for feature, name in zip(gdf_by_type.geometry, gdf_by_type['@osmId']):

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

    traces.append(go.Scattermapbox(
        mode = "lines",
        lon = lons,
        lat = lats,
        marker={'size':5, "color":colors[highway_type]},
        name=highway_type,
    ))

roadways_fig = go.Figure()
for trace in traces:
    roadways_fig.add_trace(trace)

roadways_fig.update_layout(
    margin ={'l':0,'t':0,'b':0,'r':0},
    mapbox = {
        'center': {'lon': 120.9787, 'lat': 14.5826},
        'style': "dark",
        'zoom': 10},
    mapbox_accesstoken=token,
    height=800,
    legend_title_text='Roadway Type',
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1,
        xanchor="left",
        x=0),
        )

#liquefaction page layout
liquefaction_page = dbc.Container([
    dbc.Row([
        dbc.Col([
            dbc.Row([
                dcc.Graph(figure=liqf_hosp_fig)
            ]),
            dbc.Row([
                dcc.Graph(figure=liqf_bed_fig)
            ]),
        ], width=5),
        dbc.Col([
            dbc.Row([
                dcc.Graph(figure = liquefaction_fig)
            ]),
        ], width=7, className="custom-margin"),
    ])
], fluid=True)


#roadways affected page layout
roadways_page = html.Div([
    dbc.Container([
        dbc.Row([
            dbc.Col([
                dcc.Graph(figure=roadways_fig)
            ], align='center', className="custom-margin")
        ]),
    ], fluid=True)
])


#Tabs format
layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.Div([
                html.Span('Soil Liquefaction',
                            style={
                                "font-size":"3rem",
                                "font-family":"Cardo ,serif",
                                "font-weight":"400",
                                "line-height":"1.04",
                                "margin-bottom":"10px",
                        }),
                html.P([html.Br(), 
                        desc, 
                        html.Br(), 
                        html.Br(),
                        desc_2,
                        html.Br(),
                        html.Br(),],
                        style={
                            "font-size":"1rem",
                            "font-family":"Josefin Sans,,sans-serif",
                            "font-weight":"400",
                            "line-height":"1.46429em",
                            "text-align":"justify"}),
                        html.Img(src="./assets/liquefaction.jpg", style={"width":"350px",}),
                        ], style={"margin-top":"15px"})
            ], width=3),
        dbc.Col([
            dbc.Tabs([
                dbc.Tab(label="Liquefaction Map", tab_id="tab-1"),
                dbc.Tab(label="Transport Networks Affected", tab_id="tab-2"),
            ], id="tabs", active_tab="tab-1",),
                html.Div(id="content"),
        ], width=9, className="custom-margin")
    ])
], fluid=True, style = {'display': 'flex', 'flexDirection': 'column', 'height': '90vh',})

@callback(
        Output("content", "children"),
        Input("tabs", "active_tab"),
)
def switch_tab(at):
    if at == "tab-1":
        return liquefaction_page
    elif at == "tab-2":
        return roadways_page
    