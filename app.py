import streamlit as st
import pandas as pd
from datetime import datetime as dt

# ----------------------------
# Page Config
# ----------------------------
st.set_page_config(
    page_title="Citykart Fixture Allocation Tool",
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
    st.markdown('<div class="big-title">Citykart Fixture Allocation Tool</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-text">Upload → Allocate → Download</div>', unsafe_allow_html=True)

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


