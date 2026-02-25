import streamlit as st
import pandas as pd
from datetime import datetime as dt
import csv
import re

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
    st.markdown(
        "<h1 style='color:#c62828;'>Citykart Revision Tool</h1>",
        unsafe_allow_html=True
    )
    st.markdown(
        "<h4 style='color:#2e7d32;'>Upload → Filter → Revise → Download</h4>",
        unsafe_allow_html=True
    )

st.markdown("---")

# ----------------------------
# File Upload
# ----------------------------
uploaded_file = st.file_uploader(
    "Upload File",
    type=["csv", "xlsx", "xls"]
)

if uploaded_file is None:
    st.stop()

# ----------------------------
# SAFE FILE READER
# ----------------------------
def read_file_safe(file):

    name = file.name.lower()

    # ---------- CSV ----------
    if name.endswith(".csv"):

        encodings = ["utf-8", "latin1", "cp1252"]
        seps = [",", ";", "\t", "|"]

        for enc in encodings:
            for sep in seps:
                try:
                    file.seek(0)
                    df = pd.read_csv(
                        file,
                        encoding=enc,
                        sep=sep,
                        engine="python"
                    )

                    if df.shape[1] > 1:
                        return df
                except:
                    continue

        st.error("CSV format not supported")
        st.stop()

    # ---------- Excel ----------
    else:
        excel = pd.ExcelFile(file)

        sheet = st.selectbox(
            "Select Sheet",
            excel.sheet_names
        )

        return excel.parse(sheet)


df = read_file_safe(uploaded_file)
st.success("File Uploaded Successfully")

# ------------------------------------------------
# SMART NUMERIC DETECTION
# Handles %, Currency, Float, Comma numbers
# ------------------------------------------------
def smart_numeric_convert(series):

    original = series.astype(str)

    cleaned = (
        original
        .str.replace(r"[₹$€,]", "", regex=True)
        .str.replace("%", "", regex=True)
        .str.replace(r"\s+", "", regex=True)
    )

    numeric = pd.to_numeric(cleaned, errors="coerce")

    # accept column if mostly numeric
    if numeric.notna().sum() > len(series) * 0.4:
        return numeric

    return series


for col in df.columns:
    if df[col].dtype == "object":
        df[col] = smart_numeric_convert(df[col])

# ----------------------------
# Column Detection
# ----------------------------
numeric_cols = df.select_dtypes(include="number").columns.tolist()
filter_columns = [c for c in df.columns if c not in numeric_cols]

# ----------------------------
# SESSION FILTER STORAGE
# ----------------------------
if "filters" not in st.session_state:
    st.session_state.filters = {c: [] for c in filter_columns}

user_filters = st.session_state.filters

# ----------------------------
# CASCADE FILTERS (FORWARD + REVERSE)
# ----------------------------
st.subheader("🔎 Select Filters")

cols = st.columns(3)

for i, col in enumerate(filter_columns):

    with cols[i % 3]:

        temp_df = df.copy()

        for other_col in filter_columns:

            if other_col == col:
                continue

            selected_vals = user_filters.get(other_col, [])

            if selected_vals:
                temp_df = temp_df[
                    temp_df[other_col]
                    .astype(str)
                    .isin(list(map(str, selected_vals)))
                ]

        options = sorted(temp_df[col].dropna().unique())

        selected = st.multiselect(
            col,
            options,
            default=user_filters.get(col, []),
            key=f"filter_{col}"
        )

        user_filters[col] = selected

# ----------------------------
# FILTERED DATA
# ----------------------------
filtered_df = df.copy()

for col, vals in user_filters.items():
    if vals:
        filtered_df = filtered_df[
            filtered_df[col].astype(str).isin(
                list(map(str, vals))
            )
        ]

c1, c2 = st.columns(2)
c1.metric("Total Rows", f"{len(df):,}")
c2.metric("Filtered Rows", f"{len(filtered_df):,}")

st.markdown("---")

# ----------------------------
# Numeric Column Selection
# ----------------------------
st.subheader("📊 Select Numeric Column For Calculation")

selected_numeric_cols = st.multiselect(
    "Choose Numeric Column(s)",
    numeric_cols
)

# ----------------------------
# Percentage Section
# ----------------------------
st.subheader("📈 Percentage Settings")

percent = st.number_input(
    "Enter Percentage",
    min_value=0.0,
    step=1.0
)

mode = st.radio(
    "Select Mode",
    ["Increase %", "Decrease %", "Direct %"]
)

# ----------------------------
# APPLY FUNCTION
# ----------------------------
def apply_percentage(df, filters, numeric_columns, percent, mode):

    df_result = df.copy()

    mask = pd.Series(True, index=df.index)
    filter_used = False

    for col, vals in filters.items():
        if vals:
            filter_used = True
            mask &= df_result[col].astype(str).isin(
                list(map(str, vals))
            )

    if not filter_used:
        mask[:] = True

    # multiplier
    if mode == "Increase %":
        mult = 1 + percent / 100
    elif mode == "Decrease %":
        mult = 1 - percent / 100
    else:
        mult = percent / 100

    for col in numeric_columns:

        new_col = f"{col}_REVISED"

        df_result[new_col] = df_result[col]
        df_result.loc[mask, new_col] = (
            df_result.loc[mask, col] * mult
        )

    df_result["NEW_STATUS"] = "SAME"
    df_result.loc[mask, "NEW_STATUS"] = "REVISED"

    return df_result


st.info(f"Rows Impacted After Apply: {len(filtered_df):,}")

# ----------------------------
# APPLY BUTTON
# ----------------------------
if st.button("🚀 Apply Changes"):

    if percent == 0:
        st.warning("Enter percentage > 0")
        st.stop()

    # If none selected → all numeric
    if not selected_numeric_cols:
        selected_numeric_cols = numeric_cols
        st.info(
            "No numeric column selected → Applying on ALL numeric columns"
        )

    active_filters = {
        k: v for k, v in user_filters.items() if v
    }

    result_df = apply_percentage(
        df,
        active_filters,
        selected_numeric_cols,
        percent,
        mode
    )

    st.success("Calculation Completed")

    st.dataframe(result_df, use_container_width=True)

    csv_out = result_df.to_csv(index=False).encode("utf-8")

    st.download_button(
        "⬇ Download Result",
        csv_out,
        file_name=f"output_{dt.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )
