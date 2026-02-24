import streamlit as st
import pandas as pd
from datetime import datetime as dt

# ----------------------------
# Page Config
# ----------------------------
st.set_page_config(
    page_title="Citykart Sales Revision Tool",
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
    st.markdown("<h1 style='color:#c62828;'>Citykart Sales Revision Tool</h1>", unsafe_allow_html=True)
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
st.success("File Uploaded Successfully")

# ----------------------------
# Detect Columns
# ----------------------------
numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
non_numeric_cols = df.select_dtypes(exclude=["number"]).columns.tolist()

# ----------------------------
# Dynamic Filters (All Non Numeric)
# ----------------------------
st.subheader("🔎 Select Filters")

filtered_df = df.copy()
user_filters = {}

cols = st.columns(3)

for i, col in enumerate(non_numeric_cols):

    with cols[i % 3]:
        options = sorted(filtered_df[col].dropna().unique())
        selected = st.multiselect(col, options)

        if selected:
            filtered_df = filtered_df[filtered_df[col].isin(selected)]
            user_filters[col] = selected

st.write(f"Rows Selected: {len(filtered_df)}")

st.markdown("---")

# ----------------------------
# Numeric Column Selection
# ----------------------------
st.subheader("📊 Select Numeric Column For Calculation")

if not numeric_cols:
    st.error("No numeric columns found in file.")
    st.stop()

selected_numeric_col = st.selectbox(
    "Choose Numeric Column",
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
def apply_percentage(df, filters, numeric_column, percent, mode):

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

    # Create revised column
    new_col_name = f"{numeric_column}_REVISED"

    df_result[new_col_name] = df_result[numeric_column]
    df_result.loc[mask, new_col_name] = (
        df_result.loc[mask, numeric_column] * multiplier
    )

    df_result["STATUS"] = "SAME"
    df_result.loc[mask, "STATUS"] = "REVISED"

    return df_result

# ----------------------------
# Apply Button
# ----------------------------
if st.button("🚀 Apply Changes"):

    if percent == 0:
        st.warning("Please enter percentage greater than 0")
        st.stop()

    result_df = apply_percentage(
        df,
        user_filters,
        selected_numeric_col,
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
