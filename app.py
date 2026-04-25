import streamlit as st
import joblib
import numpy as np
import pandas as pd

# ----- Sidebar -----
with st.sidebar:
    st.header("About this project")
    st.markdown(
        "This dashboard predicts machine failure using a Random Forest "
        "classifier trained on the **AI4I 2020 Predictive Maintenance** dataset."
    )
    st.subheader("Model")
    st.markdown(
        "- Algorithm: **Random Forest** (200 trees)\n"
        "- Trained on: 8,000 machines\n"
        "- Tested on: 2,000 machines\n"
        "- Test recall: **73.5%**\n"
        "- Test precision: **56.2%**\n"
        "- Test F1: **63.7%**"
    )
    st.subheader("How to use")
    st.markdown(
        "1. Adjust the sliders to match a machine's current sensor readings\n"
        "2. The model predicts the probability of failure\n"
        "3. Use the threshold (40%) to decide whether to schedule maintenance"
    )
    st.divider()
    st.caption("Built by Shivansh Shukla | April 2026")
# ----- Page config -----
st.set_page_config(
    page_title="Predictive Maintenance",
    page_icon="⚙️",
    layout="wide"
)

# ----- Header -----
st.title("⚙️ Predictive Maintenance Dashboard")
st.markdown("Predict machine failure probability using sensor readings.")
st.divider()

# ----- Quick test -----
# ----- Load saved artifacts -----
@st.cache_resource
def load_artifacts():
    model         = joblib.load("models/random_forest_model.pkl")
    scaler        = joblib.load("models/scaler.pkl")
    threshold     = joblib.load("models/rf_threshold.pkl")
    feature_names = joblib.load("models/feature_names.pkl")
    return model, scaler, threshold, feature_names

model, scaler, threshold, feature_names = load_artifacts()

# ----- Input controls -----
st.subheader("📊 Machine Sensor Readings")
st.caption("Set values matching real-time sensor readings from a machine.")

# Two columns side by side for compact layout
col1, col2 = st.columns(2)

with col1:
    air_temp = st.slider(
        "Air temperature [K]",
        min_value=295.0, max_value=305.0, value=300.0, step=0.1
    )
    process_temp = st.slider(
        "Process temperature [K]",
        min_value=305.0, max_value=315.0, value=310.0, step=0.1
    )
    rotational_speed = st.slider(
        "Rotational speed [rpm]",
        min_value=1100, max_value=2900, value=1500, step=10
    )

with col2:
    torque = st.slider(
        "Torque [Nm]",
        min_value=3.0, max_value=80.0, value=40.0, step=0.5
    )
    tool_wear = st.slider(
        "Tool wear [min]",
        min_value=0, max_value=260, value=100, step=1
    )
    machine_type = st.selectbox(
        "Machine type",
        options=["L", "M", "H"],
        index=2,
        help="L = Low, M = Medium, H = High quality"
    )

st.divider()
# ----- Domain-aware warnings -----
warnings_list = []

if tool_wear > 200:
    warnings_list.append(
        f"⚠️ **Tool wear is high** ({tool_wear} min) — failures often occur in the 200–240 minute range."
    )

if torque > 65 and machine_type == "L":
    warnings_list.append(
        f"⚠️ **High torque on a low-quality machine** (Torque={torque} Nm, Type=L) — overstrain failure risk."
    )

if rotational_speed < 1300 and torque > 60:
    warnings_list.append(
        f"⚠️ **Low speed + high torque** ({rotational_speed} rpm, {torque} Nm) — power imbalance risk."
    )

temp_gap = process_temp - air_temp
if temp_gap < 8.6 and rotational_speed < 1380:
    warnings_list.append(
        f"⚠️ **Small air/process temperature gap** ({temp_gap:.1f} K) combined with low speed — heat dissipation risk."
    )

if warnings_list:
    with st.expander(f"🔍 {len(warnings_list)} domain-specific risk(s) detected", expanded=True):
        for w in warnings_list:
            st.markdown(w)
# ----- Build the input DataFrame -----
# Convert the dropdown choice into the same one-hot format the model expects
type_L = 1 if machine_type == "L" else 0
type_M = 1 if machine_type == "M" else 0

# Column order MUST match feature_names exactly
input_df = pd.DataFrame([{
    "Air temperature [K]":     air_temp,
    "Process temperature [K]": process_temp,
    "Rotational speed [rpm]":  rotational_speed,
    "Torque [Nm]":             torque,
    "Tool wear [min]":         tool_wear,
    "Type_L":                  type_L,
    "Type_M":                  type_M,
}])

# Reorder columns to match training-time order (just to be safe)
input_df = input_df[feature_names]

# ----- Scale the input -----
input_scaled = scaler.transform(input_df)

# ----- Predict -----
failure_proba = model.predict_proba(input_scaled)[0, 1]
st.write(f"DEBUG: raw probability = {failure_proba:.6f}")
prediction    = 1 if failure_proba >= threshold else 0

# ----- Display the result -----
st.subheader("🎯 Prediction")

result_col1, result_col2 = st.columns(2)

with result_col1:
    if prediction == 1:
        st.error(f"⚠️ FAILURE LIKELY")
    else:
        st.success(f"✅ HEALTHY")

with result_col2:
    if failure_proba < 0.2:
        proba_color = "green"
    elif failure_proba < 0.4:
        proba_color = "orange"
    else:
        proba_color = "red"

    st.markdown(
        f"### Failure probability: "
        f":{proba_color}[**{failure_proba * 100:.2f}%**]"
    )
    st.caption(f"Threshold for failure prediction: {threshold * 100:.0f}%")
# Probability bar
st.progress(float(failure_proba))

st.divider()

# ----- Feature importance display -----
st.subheader("🔍 Why this prediction?")
st.markdown("These are the features the model relies on most across all predictions:")

importance_df = pd.DataFrame({
    "Feature": feature_names,
    "Importance": model.feature_importances_
}).sort_values("Importance", ascending=True)  # ascending for horizontal bars (largest on top)

# Use Streamlit's built-in bar chart
st.bar_chart(
    importance_df.set_index("Feature"),
    horizontal=True,
    color="#4C72B0"
)

st.caption(
    "Feature importance is computed once during training — it shows the model's "
    "general decision-making, not an explanation specific to this single prediction."
)
st.divider()

# ----- What-if analysis -----
st.subheader("🧪 What-if analysis")
st.markdown(
    "Adjust these sliders to explore how changing operating conditions affects "
    "the predicted failure probability. The original prediction stays fixed for comparison."
)

wcol1, wcol2 = st.columns(2)

with wcol1:
    wif_air_temp = st.slider(
        "What-if Air temperature [K]",
        min_value=295.0, max_value=305.0, value=air_temp, step=0.1,
        key="wif_air"
    )
    wif_process_temp = st.slider(
        "What-if Process temperature [K]",
        min_value=305.0, max_value=315.0, value=process_temp, step=0.1,
        key="wif_proc"
    )
    wif_speed = st.slider(
        "What-if Rotational speed [rpm]",
        min_value=1100, max_value=2900, value=rotational_speed, step=10,
        key="wif_speed"
    )

with wcol2:
    wif_torque = st.slider(
        "What-if Torque [Nm]",
        min_value=3.0, max_value=80.0, value=torque, step=0.5,
        key="wif_torque"
    )
    wif_wear = st.slider(
        "What-if Tool wear [min]",
        min_value=0, max_value=260, value=tool_wear, step=1,
        key="wif_wear"
    )
    wif_type = st.selectbox(
        "What-if Machine type",
        options=["L", "M", "H"],
        index=["L", "M", "H"].index(machine_type),
        key="wif_type"
    )

# Build the what-if input
wif_type_L = 1 if wif_type == "L" else 0
wif_type_M = 1 if wif_type == "M" else 0

wif_input_df = pd.DataFrame([{
    "Air temperature [K]":     wif_air_temp,
    "Process temperature [K]": wif_process_temp,
    "Rotational speed [rpm]":  wif_speed,
    "Torque [Nm]":             wif_torque,
    "Tool wear [min]":         wif_wear,
    "Type_L":                  wif_type_L,
    "Type_M":                  wif_type_M,
}])[feature_names]

wif_scaled = scaler.transform(wif_input_df)
wif_proba = model.predict_proba(wif_scaled)[0, 1]
wif_prediction = 1 if wif_proba >= threshold else 0

# Display side-by-side comparison
st.markdown("#### Comparison")
ccol1, ccol2, ccol3 = st.columns(3)

with ccol1:
    st.metric("Original probability", f"{failure_proba * 100:.2f}%")
    if prediction == 1:
        st.error("FAILURE LIKELY")
    else:
        st.success("HEALTHY")

with ccol2:
    delta = (wif_proba - failure_proba) * 100
    st.metric(
        "What-if probability",
        f"{wif_proba * 100:.2f}%",
        delta=f"{delta:+.2f} pts",
        delta_color="inverse"  # red if delta is positive (worse), green if negative (better)
    )
    if wif_prediction == 1:
        st.error("FAILURE LIKELY")
    else:
        st.success("HEALTHY")

with ccol3:
    if wif_proba < failure_proba:
        st.success(f"Improvement: −{abs(delta):.2f} pts")
        st.caption("These changes would reduce failure risk.")
    elif wif_proba > failure_proba:
        st.warning(f"Worsening: +{delta:.2f} pts")
        st.caption("These changes would increase failure risk.")
    else:
        st.info("No change")