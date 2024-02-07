from dash import Dash, html, dcc, Input, Output, ctx, callback
import dash
import pandas as pd
import geopandas as gpd
import plotly.express as px
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
import json
from access import Access
import os

#Register dash page
dash.register_page(__name__,
                   path='/accessibility-score',
                   title='Accessibility Scores',
                   name='Accessibility Scores',
                   order=6,
)

desc = "Currently, we understand the impact on each barangay in the event of liquefactions. The scarcity of beds will arise, requiring barangays additional time to reach at least one hospital of a certain level. To present a more summarized perspective, we used the Rational Agent Access Model (RAAM) framework to compute the accessibility score of each barangay. RAAM is designed to enhance the agent's (barangay) cost function by minimizing both travel time and congestion at supply sites (hospitals). The objective is to achieve a balance between hospital congestion and travel time for each barangay."
desc_2 = "Using RAAM (lower score is better), we can see that on the onset (i.e. no liquefaction has happened), the western and central parts of NCR have the highest accessibility scores in terms of healthcare. Unfortunately, the western area also has the highest risk of liquefaction."
desc_3 = "Through a comparison of accessibility scores considering liquefaction risk, we identified the top 20 barangays most significantly affected in terms of healthcare access. These particular barangays are likely to face heightened challenges in accessing the healthcare system if the liquefaction potential becomes a reality."
desc_4 = "In essence, the accessibility scores for each barangay condense three variables (population count, hospital bed capacity, and travel time) into a singular value. This value serves as a tool to pinpoint which barangays would experience the lowest healthcare accessibility in the event of \"The Big One.\""

ncr_hosp = gpd.read_file("../data/analytics/ncr_hosp.geojson", driver="GeoJSON")
liquefaction_map = gpd.read_file("../data/analytics/liquefaction_map.geojson",
                                 driver="GeoJSON")
travel_matrix = pd.read_csv("../data/analytics/travel_matrix.csv")
ncr_boundary_pop = gpd.read_file("../data/analytics/ncr_boundary_pop.geojson", driver="GeoJSON")

#Set api token
mapbox_token = os.environ.get('MAPBOX_TOKEN')
px.set_mapbox_access_token(mapbox_token)
token = mapbox_token


layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.Div([
                html.Span('Accessibility',
                          style={
                              "font-size":"3rem",
                              "font-family":"Cardo ,serif",
                              "font-weight":"400",
                              "line-height":"1.04",
                              "margin-bottom":"10px",
                          }),
                html.P([html.Br(), desc, html.Br(), html.Br(), desc_2, html.Br(), html.Br(), desc_3, html.Br(), html.Br(), desc_4],
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
                    dcc.Loading(id="map-loading",
                                type="circle",
                                children=dcc.Graph(id="accessi_map")),
                    html.Div(children="Travel time (min)"),
                    dcc.Slider(0,60,1,
                            value=30,
                            marks=None,
                            tooltip={"placement": "bottom", "always_visible": True},
                            id='my_slider'),
                ]),
                dbc.Col([
                    dcc.Loading(id="map2-loading",
                                type="circle",
                                children=dcc.Graph(id="liq_map_2"))
                ]),
            ]),
        ], width=9, className="custom-margin"),
    ])
], fluid=True, style = {'display': 'flex', 'flexDirection': 'column', 'height': '90vh',})


@callback(
    Output('liq_map_2', 'figure'),
    Output('accessi_map', 'figure'),
    Input('risk_type_dropdown', 'value'),
    Input('my_slider', 'value')
)
def display_map(risk_type_dropdown, my_slider):

    #access method for RAAM - all hospitals available
    all_hosp_access = Access(
        demand_df=ncr_boundary_pop,
        demand_index="brgy_index",
        demand_value="population",
        supply_df=ncr_hosp,
        supply_index="hospital_index",
        supply_value="bed_capacity",
        cost_df=travel_matrix,
        cost_origin="brgy_index",
        cost_dest="hospital_index",
        cost_name="duration", #duration is in seconds
        neighbor_cost_df=travel_matrix,
        neighbor_cost_origin="brgy_index",
        neighbor_cost_dest="hospital_index",
        neighbor_cost_name="duration"
    )

    #Run RAAM - all hospitals available
    all_hosp_access.raam(name="raam_all", tau=my_slider*60) #slider in minutes * 60

    #filter hospitals not in selected liquefaction potential
    brgy_hospital = travel_matrix.loc[~(travel_matrix['potential'].isin(risk_type_dropdown))]
    ncr_hosp_filtered = ncr_hosp.loc[ncr_hosp['hospital_index'].isin(brgy_hospital['hospital_index'].tolist())]

    #access method for RAAM - filtered hospitals
    filtered_hosp_access = Access(
        demand_df=ncr_boundary_pop,
        demand_index="brgy_index",
        demand_value="population",
        supply_df=ncr_hosp_filtered,
        supply_index="hospital_index",
        supply_value="bed_capacity",
        cost_df=travel_matrix,
        cost_origin="brgy_index",
        cost_dest="hospital_index",
        cost_name="duration", #duration is in seconds
        neighbor_cost_df=travel_matrix,
        neighbor_cost_origin="brgy_index",
        neighbor_cost_dest="hospital_index",
        neighbor_cost_name="duration"
    )

    #Run RAAM - filtered hospitals
    filtered_hosp_access.raam(name="raam_filtered", tau=my_slider*60) #slider in minutes * 60


    #Plot filtered hospitals
    map_fig  = px.choropleth_mapbox(filtered_hosp_access.access_df.reset_index(),
                                locations='brgy_index',
                                geojson=ncr_boundary_pop,
                                featureidkey="properties.brgy_index",
                                color='raam_filtered_bed_capacity',
                                color_continuous_scale='viridis_r',
                                range_color = [filtered_hosp_access.access_df["raam_filtered_bed_capacity"].quantile(0.05),
                                               filtered_hosp_access.access_df["raam_filtered_bed_capacity"].quantile(0.95)],
                                )

    customdata_df = ncr_boundary_pop[["barangay", "city"]]
    customdata_df['raam_filtered_bed_capacity'] = round(filtered_hosp_access.access_df['raam_filtered_bed_capacity'], 3)

    map_fig.update_traces(customdata= customdata_df,
                        hovertemplate=
                        'Barangay Name: %{customdata[0]}<br>' +
                        'Municipality: %{customdata[1]}<br>' + 
                        'Accesibility Score: %{customdata[2]}')



    map_fig.update_layout(
    margin={'l': 0, 't': 0, 'b': 0, 'r': 0},
    coloraxis_colorbar_title_text = 'RAAM',
    mapbox={
        'center': {'lon': 120.9967449, 'lat': 14.60785},
        'style': "dark",
        'zoom': 10},
    mapbox_accesstoken=token,
    showlegend=False,
    height=800
    )

    #Liquefaction Plot
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
        )
                        )
    liquefaction_fig = go.Figure()
    for trace in liqf_traces:
        liquefaction_fig.add_trace(trace)

    ncr_hosp_filtered = ncr_hosp.loc[ncr_hosp['potential'].isin(risk_type_dropdown)]

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

    #find top 20 affected barangays
    combined_hosp_access = pd.merge(all_hosp_access.access_df["raam_all_bed_capacity"],
                                    filtered_hosp_access.access_df["raam_filtered_bed_capacity"],
                                    how="inner",
                                    on="brgy_index")
    combined_hosp_access['raam_difference'] = combined_hosp_access["raam_filtered_bed_capacity"] - combined_hosp_access["raam_all_bed_capacity"]
    combined_hosp_access = combined_hosp_access.fillna(0)
    combined_hosp_access = combined_hosp_access.sort_values("raam_difference", ascending=False).head(20)

    #Plot top 20 affected barangays
    brgy_losers = pd.merge(ncr_boundary_pop[['barangay', 'brgy_index', 'city', 'geometry']],
                           combined_hosp_access,
                           on='brgy_index')
    ##Locating the barangay
    brgy_losers_traces = []
    
    for area in brgy_losers.iterrows():
        if area[1].geometry.geom_type == 'Polygon':
            lons = list(area[1].geometry.exterior.coords.xy[0])
            lats = list(area[1].geometry.exterior.coords.xy[1])
                           
            brgy_losers_traces.append(go.Scattermapbox(
                fill = "toself",
                lon = lons,
                lat = lats,
                marker = {'size': 1, 'color': '#FF0000'},
                customdata= pd.DataFrame(len(lons)*[area[1].loc[['barangay', 'city']]]),
                hovertemplate=
                'Barangay Name: %{customdata[0]}<br>' +
                'Municipality: %{customdata[1]}<br>' + 
                '<extra></extra>'
            )
                            )

        elif area[1].geometry.geom_type == 'MultiPolygon':
            poly_list = list(area[1].geometry.geoms)
            for poly_ind in poly_list:
                lons_multi = list(poly_ind.exterior.coords.xy[0])
                lats_multi = list(poly_ind.exterior.coords.xy[1])

                brgy_losers_traces.append(go.Scattermapbox(
                fill = "toself",
                lon = lons_multi,
                lat = lats_multi,
                marker = {'size': 1, 'color': '#FF0000'},
                customdata= pd.DataFrame(len(lons)*[area[1].loc[['barangay', 'city']]]),
                hovertemplate=
                'Barangay Name: %{customdata[0]}<br>' +
                'Municipality: %{customdata[1]}<br>' + 
                '<extra></extra>'
                )
                            )

    if brgy_losers.iloc[0]['raam_difference'] != 0:
        for trace in brgy_losers_traces:
            liquefaction_fig.add_trace(trace)

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

    return liquefaction_fig, map_fig
