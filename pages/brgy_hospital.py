from dash import Dash, html, dcc, Input, Output, ctx, callback
import dash
import pandas as pd
import geopandas as gpd
import plotly.express as px
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
import json

# Register dash page
dash.register_page(__name__,
                   path='/healthcare-access',
                   title='Healthcare Access',
                   name='Healthcare Access',
                   order=5,
)

desc = "Inherently, the healthcare accessibility across various barangays in Metro Manila differs because of the uneven distribution of hospitals in the region. The reality is that not all hospitals are equal; some possess greater capacity in terms of bed space, higher capabilities in terms of their level, and are more easily reachable with shorter travel times. In the presence of a liquefaction threat, impacted hospitals might become inaccessible, necessitating barangays to reach the nearest operational hospital, thereby complicating rescue efforts."
desc_2 = "With this in mind, this page functions as a resource to identify each barangay and determine the number and types of hospitals accessible within a specific travel time on a typical day. When exploring the impact of liquefaction in this project, we operate under the assumption that any liquefaction potential could result in the unavailability of all nearby hospitals, thereby impacting the range of hospitals accessible to barangays within a specified travel time."


#import data
ncr_hosp = gpd.read_file("data/analytics/ncr_hosp.geojson", driver="GeoJSON")
liquefaction_map = gpd.read_file("data/analytics/liquefaction_map.geojson", driver="GeoJSON")
travel_matrix = pd.read_csv("data/analytics/travel_matrix.csv")
ncr_boundary_pop = gpd.read_file("data/analytics/ncr_boundary_pop.geojson", driver="GeoJSON")

#Set api token
px.set_mapbox_access_token(open("assets/.mapbox_token").read())
token = open("assets/.mapbox_token").read()


layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.Div([
                html.Span('A Closer Look',
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
            dbc.Row([
                dbc.Checklist([
                    {"label": "High Potential", "value": "High Potential"},
                    {"label": "Moderate Potential", "value": "Moderate Potential"},
                    {"label": "Low Potential", "value": "Low Potential"},],
                    value =['High Potential'],
                    id='risk_type_dropdown',
                    switch=True,
                    inline=True,
                    input_checked_style={
                        "backgroundColor": "#1d1a1a",
                        "borderColor": "#1d1a1a",
                        "box-shadow": "0 0 1px #1d1a1a"},
                    className='mb-2'),
            ]),
            dbc.Row([
                dbc.Col([
                    dcc.Dropdown(options = ncr_boundary_pop['brgy_index_city'],
                                             value = 'Barangay 100 | (Caloocan)',
                                             id='barangay_dropdown',
                                             style={"backgroundColor": 'white'},
                                             optionHeight=50),
                    html.Div(children = ["Population:",
                                        dcc.Loading(id="pop_count_loading",
                                                    type="circle",
                                                    children=html.Div(id="pop_count"))
                                        ]),
                    html.Div(children=["Number of Hospitals:",
                                       dcc.Loading(id="hosp_count_loading",
                                                   type="circle",
                                                   children=html.Div(id="hosp_count"))]),
                    html.Div(children=["Number of Beds:",
                                       dcc.Loading(id="bed_count_loading",
                                                   type="circle",
                                                   children=html.Div(id="hosp_bed"))]),
                    html.Div(children="Number of Hospitals by level"),
                    dcc.Loading(id="pop-loading",
                                type="circle",
                                children=dcc.Graph(id="bar_chart")),
                    html.Div(children="Travel time (min)"),
                    dcc.Slider(0, 60, 1,
                                value=30,
                                marks=None,
                                tooltip={"placement": "bottom", "always_visible": True},
                                id='my_slider'
                                ),
                ], width=4),
                dbc.Col([
                    #plot
                    dcc.Loading(
                        id="map2-loading",
                        type="circle",
                        children=dcc.Graph(id="liq_map")),
                ], width=8)
            ]),
        ], width=9, className="custom-margin")
    ])
], fluid=True, style = {'display': 'flex', 'flexDirection': 'column', 'height': '90vh',})


@callback(
    Output('liq_map', 'figure'),
    Output('bar_chart', 'figure'),
    Output("pop_count", "children"),
    Output("hosp_bed", "children"),
    Output("hosp_count", "children"),
    Input('risk_type_dropdown', 'value'),
    Input('barangay_dropdown', 'value'),
    Input('my_slider', 'value')
)
def display_map(risk_type_dropdown, barangay_dropdown, my_slider):

    #liquefaction plot
    liqf_traces = []
    colors = {'HP':'#f03b20', 'MP':'#feb24c', 'LP':'#ffeda0'}

    liquefaction_map_filtered = liquefaction_map.loc[liquefaction_map['potential'].isin(risk_type_dropdown)]

    for area in liquefaction_map_filtered.iterrows():
        lons = list(area[1].geometry.exterior.coords.xy[0])
        lats = list(area[1].geometry.exterior.coords.xy[1])

        customdata_df = pd.DataFrame(len(lons)*[area[1].potential])

        liqf_traces.append(go.Scattermapbox(
            fill = "toself",
            lon = lons,
            lat = lats,
            marker = {'size': 1, 'color': colors[area[1].Name[:2]]},
            customdata=customdata_df,
            hovertemplate=
            'Liquefaction Potential: %{customdata[0]}<br>' +
            '<extra></extra>'
        ))

    liquefaction_fig = go.Figure()
    for trace in liqf_traces:
        liquefaction_fig.add_trace(trace)

    #brgy plot
    brgy_traces = []

    ncr_boundary_pop_filtered = ncr_boundary_pop.loc[ncr_boundary_pop['brgy_index_city'] == barangay_dropdown]
    area = ncr_boundary_pop_filtered.iloc[0]

    if area.geometry.geom_type == 'Polygon':
        lons = list(area.geometry.exterior.coords.xy[0])
        lats = list(area.geometry.exterior.coords.xy[1])

        brgy_traces.append(go.Scattermapbox(
            fill = "toself",
            lon = lons,
            lat = lats,
            marker = {'size': 1, 'color': '#FFFF00'},
            customdata= pd.DataFrame(len(lons)*[area[area.index != 'geometry']]),
            hovertemplate=
            'Barangay Name: %{customdata[2]}<br>' +
            'Municipality: %{customdata[1]}<br>' + 
            '<extra></extra>'
        ))

    if area.geometry.geom_type == 'MultiPolygon':
        poly_list = list(area.geometry.geoms)
        for poly_ind in poly_list:
            lons_multi = list(poly_ind.exterior.coords.xy[0])
            lats_multi = list(poly_ind.exterior.coords.xy[1])

            brgy_traces.append(go.Scattermapbox(
            fill = "toself",
            lon = lons_multi,
            lat = lats_multi,
            marker = {'size': 1, 'color': '#FFFF00'},
            customdata= pd.DataFrame(len(lons)*[area[area.index != 'geometry']]),
            hovertemplate=
            'Barangay Name: %{customdata[2]}<br>' +
            'Municipality: %{customdata[1]}<br>' + 
            '<extra></extra>'
            )
                              )

    for trace in brgy_traces:
        liquefaction_fig.add_trace(trace)


    #locating the accessible hospitals given a liquefaction potential and travel time

    brgy_hospital = travel_matrix.loc[~(travel_matrix['potential'].isin(risk_type_dropdown)) &
                                        (travel_matrix['brgy_index'].isin(ncr_boundary_pop_filtered['brgy_index'].tolist())) &
                                        (travel_matrix['duration']/60 < my_slider)]
    ncr_hosp_filtered = ncr_hosp.loc[ncr_hosp['hospital_index'].isin(brgy_hospital['hospital_index'].tolist())]

    hosp_data = ncr_hosp_filtered[['facility_name','service_capability','bed_capacity']]
    hosp_data['facility_name'] = hosp_data['facility_name'].str.title()

    lats_hosp = []
    lons_hosp = []

    for index, data in ncr_hosp_filtered.iterrows():
        lats_hosp.append(data.geometry.y)
        lons_hosp.append(data.geometry.x)

    liquefaction_fig.add_trace(go.Scattermapbox(
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

    liquefaction_fig.update_layout(
    margin ={'l':0,'t':0,'b':0,'r':0},
    mapbox = {
        'center': {'lon': 121.053728, 'lat': 14.5826},
        'style': "dark",
        'zoom': 9.5},
    mapbox_accesstoken=token,
    showlegend=False,
    height=800
    )

    #bar chart for hospital count per level
    bar_data = ncr_hosp_filtered.groupby('service_capability').count().reset_index()
    rem_hospital_by_level = px.bar(bar_data,
                                   x='facility_name',
                                   y="service_capability",
                                   color="service_capability",
                                   labels={
                                       "facility_name": "No. of Hospitals",
                                       "service_capability":"Service Capability"},
                                   color_discrete_map={'Level 3':'#006837', 'Level 2':'#31a354', 'Level 1':'#78c679'},
                                    height=300,
                              )

    rem_hospital_by_level.update_layout(plot_bgcolor='white', showlegend=False)

    population = ncr_boundary_pop_filtered['population']
    hospital_bed = ncr_hosp_filtered['bed_capacity'].sum()
    hospital_count = ncr_hosp_filtered['facility_name'].nunique()

    return liquefaction_fig, rem_hospital_by_level, population, hospital_bed, hospital_count
