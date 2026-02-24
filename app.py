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
# Custom Styling
# ----------------------------
st.markdown("""
<style>
.big-title {
    font-size:48px !important;
    font-weight:800;
    color:#c62828;
}
.sub-text {
    font-size:20px;
    color:#2e7d32;
}
.section-divider {
    border-top: 1px solid #ddd;
    margin-top: 20px;
    margin-bottom: 30px;
}
</style>
""", unsafe_allow_html=True)

# ----------------------------
# Header Layout
# ----------------------------
col1, col2 = st.columns([1,5])

with col1:
    st.image("logo.png.webp", width=140)

with col2:
    st.markdown('<div class="big-title">Citykart Sales Revision Tool</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-text">Upload → Revised → Download</div>', unsafe_allow_html=True)

st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

# ----------------------------
# Upload Section
# ----------------------------
st.subheader("Upload CSV File")

uploaded_file = st.file_uploader(
    "Drag and drop file here or browse",
    type=["csv"]
)

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.success("File Uploaded Successfully")
else:
    st.info("Please upload a CSV file to continue.")
    st.stop()

# -------------------------------
# Filter Section
# -------------------------------
st.subheader("🔎 Select Filters")

# Start with full dataset
filtered_df = df.copy()

col1, col2, col3 = st.columns(3)

# ------------------------
# STORE
# ------------------------
with col1:
    store_options = sorted(filtered_df["STORE"].dropna().unique())
    selected_store = st.multiselect("STORE", store_options)

if selected_store:
    filtered_df = filtered_df[filtered_df["STORE"].isin(selected_store)]

# ------------------------
# DIVISION
# ------------------------
with col2:
    division_options = sorted(filtered_df["DIVISION"].dropna().unique())
    selected_division = st.multiselect("DIVISION", division_options)

if selected_division:
    filtered_df = filtered_df[filtered_df["DIVISION"].isin(selected_division)]

# ------------------------
# SECTION
# ------------------------
with col3:
    section_options = sorted(filtered_df["SECTION"].dropna().unique())
    selected_section = st.multiselect("SECTION", section_options)

if selected_section:
    filtered_df = filtered_df[filtered_df["SECTION"].isin(selected_section)]

# ------------------------
# Next Row Filters
# ------------------------
col4, col5, col6 = st.columns(3)

with col4:
    dept_options = sorted(filtered_df["DEPARTMENT"].dropna().unique())
    selected_dept = st.multiselect("DEPARTMENT", dept_options)

if selected_dept:
    filtered_df = filtered_df[filtered_df["DEPARTMENT"].isin(selected_dept)]

with col5:
    article_options = sorted(filtered_df["ARTICLE_NAME"].dropna().unique())
    selected_article = st.multiselect("ARTICLE_NAME", article_options)

if selected_article:
    filtered_df = filtered_df[filtered_df["ARTICLE_NAME"].isin(selected_article)]

with col6:
    concept_options = sorted(filtered_df["CONCEPT"].dropna().unique())
    selected_concept = st.multiselect("CONCEPT", concept_options)

if selected_concept:
    filtered_df = filtered_df[filtered_df["CONCEPT"].isin(selected_concept)]

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
# Prepare Filter Dictionary
# -------------------------------
user_filters = {}

if selected_store:
    user_filters["STORE"] = selected_store

if selected_division:
    user_filters["DIVISION"] = selected_division

if selected_section:
    user_filters["SECTION"] = selected_section

if selected_dept:
    user_filters["DEPARTMENT"] = selected_dept

if selected_article:
    user_filters["ARTICLE_NAME"] = selected_article

if selected_concept:
    user_filters["CONCEPT"] = selected_concept


st.write(f"Rows Selected For Revision: {len(filtered_df)}")

# -------------------------------
# Button Action
# -------------------------------
if st.button("🚀 Apply Changes"):

    if percent == 0:
        st.warning("Please enter percentage greater than 0")
        st.stop()

    result_df = apply_percentage(df, user_filters, percent, mode)

    st.success("Calculation Completed")

    st.dataframe(result_df, use_container_width=True)

    csv = result_df.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="⬇ Download Result CSV",
        data=csv,
        file_name=f"output_{dt.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )
