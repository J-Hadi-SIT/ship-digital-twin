import stqdm
import geopy.distance
import streamlit as st
import plotly.graph_objects as go
from map_util import make_map
from physics_engine import *


# Title
st.title("The Digital Twin Demonstrator - Prime Mover & Mass Dynamic Interactions")

# Simulation Settings
with st.container(border=True):
    st.subheader('Simulation Settings')
    labels = ["Ship Mass (tons):", "Time Step (s):", ]
    mass, timestep = [st.number_input(lab, ) for lab in labels]

# Set Waypoints
@st.cache_data
def waypoints_n_thrust(df_waypoints):
    st.pydeck_chart(make_map(*df_waypoints[['Latitude (deg)', 'Longitude (deg)']].to_numpy().T))
with st.container(border=True):
    st.subheader("Waypoints & Prime Mover's Thrust")
    if st.radio("Set Waypoints & Thrusts", ['Input manually', 'Upload file']) == 'Input manually':
        df_waypoints = st.data_editor(pd.DataFrame(columns=['Latitude (deg)', 'Longitude (deg)', 'Thrust (N)']), 
                                      num_rows='dynamic', use_container_width=True)
    else:
        waypoints_csv = st.file_uploader('0', label_visibility='hidden', type="csv")
        if waypoints_csv is not None:
            df_waypoints = st.data_editor(pd.read_csv(waypoints_csv), num_rows='dynamic', use_container_width=True)
        else:
            df_waypoints = pd.DataFrame()
    if not df_waypoints.empty:
        waypoints_n_thrust(df_waypoints)

# Set Resistance/Friction
@st.cache_data
def hydrodynamics_resistance(friction_csv):
    if friction_csv is not None:
        df_friction = pd.read_csv(friction_csv)
        xf, yf = df_friction.columns.to_numpy()
        st.line_chart(df_friction, x=xf, y=yf)
    else:
        # st.warning("Please upload the CSV friction/resistance file.")
        df_friction = pd.DataFrame()
    return df_friction
with st.container(border=True):
    st.subheader('Resistance (Drag) Force')
    friction_csv = st.file_uploader("Upload a resistance file", type="csv")
    df_friction = hydrodynamics_resistance(friction_csv)

result = pd.DataFrame()
# Execute button
if st.button("Execute"):

    # Check numerical inputs
    if not mass*timestep or df_friction.empty:
        st.warning("Please ensure that **Mass** and **Time Step** not zero, and **Hydrodynamics Resistance** file is uploaded")
    else:

        # Initialize components
        prime_mover_model = PrimeMover()
        mass_model = Mass(mass*1000)        # tons to kg
        df_friction.iloc[:,0] *= 0.514444   # knots to m/s
        resistance_model = Resistance(df_friction)
        digital_twin = DigitalTwin(timestep, mass_model, prime_mover_model, resistance_model)

        # End condition
        to_meters = lambda row: geopy.distance.geodesic(row[:2], row[2:]).meters
        legs = pd.concat([df_waypoints[['Latitude (deg)', 'Longitude (deg)']].copy().shift(1), 
                          df_waypoints[['Latitude (deg)', 'Longitude (deg)']].copy()], axis=1).iloc[1:].apply(to_meters, axis=1)
        
        # Simulation loop
        n_step = 0
        waypoint_changes = []
        for leg_num, leg_distance in enumerate(stqdm.stqdm(np.cumsum(legs), total=len(legs))):
            waypoint_changes.append(n_step)
            digital_twin.prime_mover_model.force_current = df_waypoints['Thrust (N)'].iloc[leg_num]
            while digital_twin.mass_model.position_current < leg_distance:
                digital_twin.update()
                sim_position, sim_velocity, sim_acceleration = digital_twin.mass_model.get_state()
                n_step += 1
        else:
            waypoint_changes.append(n_step)

        result = pd.DataFrame({'Time Elapsed (min)': digital_twin.xtime,
                                'Travel Distance (m)': digital_twin.mass_model.position_history, 
                                'Velocity (m/s)': digital_twin.mass_model.velocity_history})
        
if result.shape[0] > 0:
    res = result.copy()
    res /= (60, 1852, 0.514444)
    res.columns = ['Time Elapsed (min)', 'Travel Distance (nmi)', 'Velocity (knot)']

    # Display the final output chart 
    with st.container(border=True):
        st.subheader("Simulation Results")
        titles = ['', 'Time Elapsed vs Travel Distance', 'Time Elapsed vs Velocity']
        for i in range(1,3):
            with st.container(border=True):
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=res.iloc[:,0], 
                                            y=res.iloc[:,i], 
                                        #  mode='lines+markers', 
                                            name=res.columns[i], ))
                annotations = []
                for j, txt in enumerate(waypoint_changes):
                    annotations.append(dict(
                        x=res.iloc[txt,0],
                        y=res.iloc[txt,i],
                        xref="x",
                        yref="y",
                        text=f"{j}",
                        showarrow=True,
                        arrowhead=5,
                        ax=-15,
                        ay=-30,
                        font=dict(size=18,
                                    color='#FF980E', ),
                    ))
                fig.update_layout(
                    title=titles[i],
                    xaxis_title=res.columns[0],
                    yaxis_title=res.columns[i],
                    annotations=annotations
                )
                st.plotly_chart(fig)
