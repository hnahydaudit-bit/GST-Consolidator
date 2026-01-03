import streamlit as st

st.set_page_config(
    page_title="GST Consolidator",
    layout="wide"
)

st.title("GST Consolidator")
st.caption("JSON based GST reports & reconciliation tool")

st.sidebar.header("Upload GST JSON Files")

uploaded_files = st.sidebar.file_uploader(
    "Upload monthly GSTR JSON files",
    type=["json"],
    accept_multiple_files=True
)

if uploaded_files:
    st.success(f"{len(uploaded_files)} files uploaded successfully")

st.info("This is a prototype UI. Processing logic will be added next.")
