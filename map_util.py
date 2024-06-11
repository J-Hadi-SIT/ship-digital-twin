import numpy as np
import pandas as pd
import pydeck as pdk
import streamlit as st
from pydeck.types import String


def make_map(lat, lon):

    lat, lon = lat.astype(np.float64), lon.astype(np.float64)
    df_points = pd.DataFrame({'points': list(zip(lon, lat)), 
                              'text': [str(i) for i in range(len(lon))], })
    df_path = pd.DataFrame({'path': [df_points['points'].tolist()], 
                            'color': [[211, 33, 44],]*1, })

    layer_path = pdk.Layer(
        "PathLayer",
        data=df_path,
        get_path='path',
        get_color='color',
        width_scale=20,
        width_min_pixels=2,
        get_width=5,
    )

    layer_scatter = pdk.Layer(
        "ScatterplotLayer",
        data=df_points,
        opacity=1.0,
        stroked=True,
        filled=True,
        radius_scale=6,
        radius_min_pixels=1,
        radius_max_pixels=100,
        line_width_min_pixels=1,
        get_radius=20,
        get_position='points',
        get_fill_color=[255, 104, 30],
        get_line_color=[255, 104, 30],
    )

    layer_text = pdk.Layer(
        "TextLayer",
        data=df_points,
        get_position="points",
        get_text="text",
        get_size=24,
        get_color=[255, 152, 14],
        get_angle=0,
        get_text_anchor=String("middle"),
        get_alignment_baseline=String("bottom"),
    )

    try:
        lat_init = lat.min()+(lat.max()-lat.min())/2
        lon_init = lon.min()+(lon.max()-lon.min())/2
    except TypeError:
        print('Oops')
        lat_init = 1.25
        lon_init = 103.8
    view_state = pdk.ViewState(
            latitude=lat_init,
            longitude=lon_init,
            zoom=10,
            pitch=45,
            bearing=0,
        )

    return pdk.Deck(map_style=None,
                    initial_view_state=view_state,
                    layers=[layer_path, 
                            layer_scatter, 
                            layer_text, ], )
