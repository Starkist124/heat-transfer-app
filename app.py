import streamlit as st
import numpy as np
import CoolProp.CoolProp as CP

# --- Conversion Dictionaries ---
P_CONV = {"kPa": 1000.0, "Pa": 1.0, "bar": 100000.0, "psi": 6894.76, "atm": 101325.0}
L_CONV = {"m": 1.0, "cm": 0.01, "mm": 0.001, "inches": 0.0254, "ft": 0.3048}
V_CONV = {"m/s": 1.0, "cm/s": 0.01, "ft/s": 0.3048} 

# Output Volumetric/Mass Conversions
VOL_OUT_CONV = {"m³/s": 1.0, "L/s": 1000.0, "mL/s": 1000000.0, "L/min": 60000.0, "mL/min": 60000000.0, "ft³/s": 35.3147, "gpm": 15850.32}
MASS_OUT_CONV = {"kg/s": 1.0, "g/s": 1000.0, "kg/h": 3600.0, "lb/s": 2.20462, "lb/h": 7936.64}

# --- NEW: Bucket Test Conversions ---
# Multiply to get to Base SI (Cubic Meters and Seconds)
STATIC_VOL_CONV = {"gallons": 0.00378541, "L": 0.001, "mL": 0.000001, "m³": 1.0, "ft³": 0.0283168}
TIME_CONV = {"seconds": 1.0, "minutes": 60.0, "hours": 3600.0}

# --- App Setup ---
st.set_page_config(page_title="Heat Transfer Pro", page_icon="🔥", layout="centered")
st.title("Flow Rate Calculator")
st.write("Mix and match your input units! The app handles all conversions behind the scenes.")

# --- Section 1: Fluid & State Variables ---
st.header("1. Fluid Properties")
fluid = st.selectbox("Select Fluid", ["Water", "Air", "R134a", "Nitrogen", "Ammonia"])

col1, col2 = st.columns([3, 1])
with col1:
    t_val = st.number_input("Temperature", value=25.0)
with col2:
    t_unit = st.selectbox("Unit", ["°C", "°F", "K"], key="t_unit", label_visibility="hidden")

if t_unit == "°C":
    temp_k = t_val + 273.15
elif t_unit == "°F":
    temp_k = (t_val - 32) * 5.0 / 9.0 + 273.15
else:
    temp_k = t_val

col3, col4 = st.columns([3, 1])
with col3:
    p_val = st.number_input("Pressure", value=101.325)
with col4:
    p_unit = st.selectbox("Unit", list(P_CONV.keys()), key="p_unit", label_visibility="hidden")

press_pa = p_val * P_CONV[p_unit]

# --- Section 2: Pipe Geometry ---
st.header("2. Pipe Geometry")
shape = st.selectbox("Cross-section", ["Circular", "Rectangular"])

if shape == "Circular":
    col5, col6 = st.columns([3, 1])
    with col5:
        d_val = st.number_input("Diameter", value=0.05, format="%.3f")
    with col6:
        d_unit = st.selectbox("Unit", list(L_CONV.keys()), key="d_unit", label_visibility="hidden")
    
    d_m = d_val * L_CONV[d_unit]
    area_m2 = (np.pi / 4) * (d_m ** 2)
else:
    col7, col8, col9, col10 = st.columns([2, 1, 2, 1])
    with col7:
        w_val = st.number_input("Width", value=0.05, format="%.3f")
    with col8:
        w_unit = st.selectbox("Unit", list(L_CONV.keys()), key="w_unit", label_visibility="hidden")
    with col9:
        h_val = st.number_input("Height", value=0.05, format="%.3f")
    with col10:
        h_unit = st.selectbox("Unit", list(L_CONV.keys()), key="h_unit", label_visibility="hidden")
        
    w_m = w_val * L_CONV[w_unit]
    h_m = h_val * L_CONV[h_unit]
    area_m2 = w_m * h_m

# --- Section 3: Flow Conditions ---
st.header("3. Flow Conditions")
known_param = st.selectbox("What do you know?", ["Average Velocity", "Volumetric Flow Rate", "Mass Flow Rate", "Volume collected over Time"])

if known_param != "Volume collected over Time":
    col11, col12 = st.columns([3, 1])
    with col11:
        flow_val = st.number_input(f"Enter {known_param}", value=1.5, format="%.4g")
    with col12:
        if known_param == "Average Velocity":
            flow_unit = st.selectbox("Unit", list(V_CONV.keys()), key="flow_unit", label_visibility="hidden")
        elif known_param == "Volumetric Flow Rate":
            flow_unit = st.selectbox("Unit", list(VOL_OUT_CONV.keys()), key="flow_unit", label_visibility="hidden")
        else:
            flow_unit = st.selectbox("Unit", list(MASS_OUT_CONV.keys()), key="flow_unit", label_visibility="hidden")
else:
    # New Bucket Test Inputs
    st.write("Enter your bucket test data:")
    b_col1, b_col2 = st.columns([3, 1])
    with b_col1:
        vol_val = st.number_input("Volume Collected", value=5.0)
    with b_col2:
        vol_unit = st.selectbox("Unit", list(STATIC_VOL_CONV.keys()), key="vol_unit", label_visibility="hidden")
        
    t_col1, t_col2 = st.columns([3, 1])
    with t_col1:
        time_val = st.number_input("Time Taken", value=3.0)
    with t_col2:
        time_unit = st.selectbox("Unit", list(TIME_CONV.keys()), key="time_unit", label_visibility="hidden")

st.divider()

# --- Section 4: Output Customization & Results ---
st.header("4. Results")

out_col1, out_col2, out_col3 = st.columns(3)
with out_col1:
    v_out_unit = st.selectbox("Velocity Output", list(V_CONV.keys()))
with out_col2:
    vol_out_unit = st.selectbox("Volumetric Output", list(VOL_OUT_CONV.keys()))
with out_col3:
    mass_out_unit = st.selectbox("Mass Output", list(MASS_OUT_CONV.keys()))

try:
    # 1. Get Density FIRST
    density_si = CP.PropsSI('D', 'T', temp_k, 'P', press_pa, fluid)
    
    # 2. Sort out the Base SI values
    if known_param == "Average Velocity":
        vel_ms = flow_val * V_CONV[flow_unit]
        v_dot_si = area_m2 * vel_ms
        m_dot_si = density_si * v_dot_si
        
    elif known_param == "Volumetric Flow Rate":
        v_dot_si = flow_val / VOL_OUT_CONV[flow_unit]
        vel_ms = v_dot_si / area_m2
        m_dot_si = density_si * v_dot_si
        
    elif known_param == "Mass Flow Rate":
        m_dot_si = flow_val / MASS_OUT_CONV[flow_unit]
        v_dot_si = m_dot_si / density_si
        vel_ms = v_dot_si / area_m2
        
    elif known_param == "Volume collected over Time":
        if time_val == 0:
            st.error("Time taken cannot be zero!")
            v_dot_si = 0
            vel_ms = 0
            m_dot_si = 0
        else:
            vol_m3 = vol_val * STATIC_VOL_CONV[vol_unit]
            time_s = time_val * TIME_CONV[time_unit]
            
            v_dot_si = vol_m3 / time_s
            vel_ms = v_dot_si / area_m2
            m_dot_si = density_si * v_dot_si

    # 3. Apply chosen output conversions
    final_vel = vel_ms / V_CONV[v_out_unit] 
    final_v_dot = v_dot_si * VOL_OUT_CONV[vol_out_unit]
    final_m_dot = m_dot_si * MASS_OUT_CONV[mass_out_unit]
    
    # 4. Display the results!
    st.info(f"Calculated Fluid Density: **{density_si:.2f} kg/m³**")
    
    res_col1, res_col2, res_col3 = st.columns(3)
    with res_col1:
        st.metric(label=f"Velocity ({v_out_unit})", value=f"{final_vel:.4g}")
    with res_col2:
        st.metric(label=f"Volumetric Flow ({vol_out_unit})", value=f"{final_v_dot:.4g}")
    with res_col3:
        st.metric(label=f"Mass Flow ({mass_out_unit})", value=f"{final_m_dot:.4g}")

except Exception as e:
    st.error("⚠️ Error calculating properties. Please check if your temperature and pressure inputs make physical sense for the selected fluid state.")