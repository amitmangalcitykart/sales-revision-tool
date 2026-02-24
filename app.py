import streamlit as st
import pandas as pd
from datetime import datetime as dt
import os

# -------------------------------
# Page Config
# -------------------------------
st.set_page_config(page_title="Sales Revision Tool", layout="wide")

st.title("📊 Sales Revision Tool")

st.image("logo.png.webp", width=200)
st.title("Sales Revision Tool")

# -------------------------------
# Load Data
# -------------------------------
@st.cache_data
def load_data():
    return pd.read_csv(r"D:\Input.csv")

df = load_data()

st.success("Data Loaded Successfully")

# -------------------------------
# Filter Section
# -------------------------------
st.subheader("🔎 Select Filters")

filter_columns = [col for col in df.columns if col not in ["SL_Q", "SL_V"]]

user_filters = {}

cols = st.columns(3)

for i, col in enumerate(filter_columns):
    with cols[i % 3]:
        options = sorted(df[col].dropna().astype(str).unique())
        selected = st.multiselect(f"{col}", options)
        if selected:
            user_filters[col] = selected

# -------------------------------
# Percentage Section
# -------------------------------
st.subheader("📈 Percentage Settings")

percent = st.number_input("Enter Percentage", min_value=0.0, step=1.0)

mode = st.radio(
    "Select Mode",
    ["Increase %", "Decrease %", "Direct %"]
)

# -------------------------------
# Apply Function
# -------------------------------
def apply_percentage(df, filters: dict, percent: float, mode):

    df_result = df.copy()
    mask = pd.Series(True, index=df_result.index)

    for col, values in filters.items():
        mask &= df_result[col].astype(str).isin(values)

    # Multiplier logic
    if mode == "Increase %":
        multiplier = 1 + percent / 100
    elif mode == "Decrease %":
        multiplier = 1 - percent / 100
    else:  # Direct %
        multiplier = percent / 100

    df_result["SL_Q_NEW"] = df_result["SL_Q"]
    df_result["SL_V_NEW"] = df_result["SL_V"]

    df_result.loc[mask, "SL_Q_NEW"] = df_result.loc[mask, "SL_Q"] * multiplier
    df_result.loc[mask, "SL_V_NEW"] = df_result.loc[mask, "SL_V"] * multiplier

    df_result["STATUS"] = "SAME"
    df_result.loc[mask, "STATUS"] = "REVISED"

    return df_result

# -------------------------------
# Button Action
# -------------------------------
if st.button("🚀 Apply Changes"):

    result_df = apply_percentage(df, user_filters, percent, mode)

    st.success("Calculation Completed")

    st.dataframe(result_df, use_container_width=True)

    # Download Option
    csv = result_df.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="⬇ Download Result CSV",
        data=csv,
        file_name=f"output_{dt.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"

    )
