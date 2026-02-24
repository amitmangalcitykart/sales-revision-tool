import streamlit as st
import pandas as pd
from datetime import datetime as dt

# ----------------------------
# Page Config
# ----------------------------
st.set_page_config(
    page_title="Citykart Revision Tool",
    layout="wide"
)

# ----------------------------
# Header
# ----------------------------
col1, col2 = st.columns([1,5])

with col1:
    try:
        st.image("logo.png.webp", width=130)
    except:
        pass

with col2:
    st.markdown("<h1 style='color:#c62828;'>Citykart Revision Tool</h1>", unsafe_allow_html=True)
    st.markdown("<h4 style='color:#2e7d32;'>Upload → Filter → Revise → Download</h4>", unsafe_allow_html=True)

st.markdown("---")

# ----------------------------
# Upload CSV
# ----------------------------
uploaded_file = st.file_uploader("Upload CSV File", type=["csv"])

if uploaded_file is None:
    st.info("Please upload a CSV file to continue.")
    st.stop()

df = pd.read_csv(uploaded_file)

# Reset filters when new file uploaded
if "last_file" not in st.session_state:
    st.session_state.last_file = uploaded_file.name

if st.session_state.last_file != uploaded_file.name:
    st.session_state.filters = {}
    st.session_state.last_file = uploaded_file.name
st.success("File Uploaded Successfully")

# Try converting comma-separated numbers to numeric
for col in df.columns:

    if df[col].dtype == "object":

        cleaned_col = (
            df[col]
            .astype(str)
            .str.replace(",", "", regex=False)
        )

        converted = pd.to_numeric(cleaned_col, errors="coerce")

        # If majority values numeric → convert column
        if converted.notna().sum() > len(df) * 0.5:
            df[col] = converted

# ----------------------------
# Detect Columns
# ----------------------------
numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
non_numeric_cols = df.select_dtypes(exclude=["number"]).columns.tolist()

# ----------------------------
# Dynamic Filters (All Non Numeric)
# ----------------------------
st.subheader("🔎 Select Filters")

# Non numeric columns
numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
filter_columns = [col for col in df.columns if col not in numeric_cols]

# Session state store selections
if "filters" not in st.session_state or \
   set(st.session_state.filters.keys()) != set(filter_columns):

    st.session_state.filters = {col: [] for col in filter_columns}

user_filters = st.session_state.filters

cols = st.columns(3)

for i, col in enumerate(filter_columns):

    with cols[i % 3]:

        # Apply OTHER filters except current column
        temp_df = df

        for other_col, values in user_filters.items():
            if other_col != col and values:
                temp_df = temp_df[temp_df[other_col].isin(values)]

        options = sorted(temp_df[col].dropna().unique())

        selected = st.multiselect(
            col,
            options,
            default=user_filters[col],
            key=f"filter_{col}"
        )

        user_filters[col] = selected

# -------------------------------
# Build Final Filtered Dataset
# -------------------------------
filtered_df = df.copy()

for col, values in user_filters.items():
    if values:
        filtered_df = filtered_df[filtered_df[col].isin(values)]

c1, c2 = st.columns(2)

c1.metric("Total Rows", f"{len(df):,}")
c2.metric("Filtered Rows", f"{len(filtered_df):,}")

st.markdown("---")

# ----------------------------
# Numeric Column Selection
# ----------------------------
st.subheader("📊 Select Numeric Column For Calculation")

if not numeric_cols:
    st.error("No numeric columns found in file.")
    st.stop()

selected_numeric_cols = st.multiselect(
    "Choose Numeric Column(s)",
    numeric_cols
)

# ----------------------------
# Percentage Section
# ----------------------------
st.subheader("📈 Percentage Settings")

percent = st.number_input("Enter Percentage", min_value=0.0, step=1.0)

mode = st.radio(
    "Select Mode",
    ["Increase %", "Decrease %", "Direct %"]
)

# ----------------------------
# Apply Function
# ----------------------------
def apply_percentage(df, filters, numeric_columns, percent, mode):

    df_result = df.copy()
    mask = pd.Series(True, index=df_result.index)

    # Apply filters
    for col, values in filters.items():
        mask &= df_result[col].astype(str).isin(values)

    # Multiplier logic
    if mode == "Increase %":
        multiplier = 1 + percent / 100
    elif mode == "Decrease %":
        multiplier = 1 - percent / 100
    else:
        multiplier = percent / 100

    # Apply calculation to selected numeric columns
    for numeric_column in numeric_columns:

        new_col_name = f"{numeric_column}_REVISED"

        df_result[new_col_name] = df_result[numeric_column]
        df_result.loc[mask, new_col_name] = (
            df_result.loc[mask, numeric_column] * multiplier
        )

    df_result["NEW_STATUS"] = "SAME"
    df_result.loc[mask, "NEW_STATUS"] = "REVISED"

    return df_result

st.info(
    f"Rows Impacted After Apply: {len(filtered_df):,}"
)

# ----------------------------
# Apply Button
# ----------------------------
if st.button("🚀 Apply Changes"):

    if percent == 0:
        st.warning("Please enter percentage greater than 0")
        st.stop()

    if not selected_numeric_cols:
        st.warning("Please select at least one numeric column")
        st.stop()

    result_df = apply_percentage(
        df,
        user_filters,
        selected_numeric_cols,
        percent,
        mode
    )

    st.success("Calculation Completed")

    st.dataframe(result_df, use_container_width=True)

    csv = result_df.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="⬇ Download Result CSV",
        data=csv,
        file_name=f"output_{dt.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )
