import streamlit as st
import json
import pandas as pd
from io import BytesIO

# ---------------- Page Config ----------------
st.set_page_config(
    page_title="GST Consolidator",
    layout="wide"
)

st.title("GST Consolidator")
st.caption("GSTR-1 JSON → Month-wise & Table-wise Consolidated Excel")

# ---------------- File Upload ----------------
uploaded_files = st.file_uploader(
    "Upload GSTR-1 JSON files (Upload 1 to 12 months)",
    type="json",
    accept_multiple_files=True
)

st.divider()

# ---------------- Generate Button (ALWAYS VISIBLE) ----------------
generate = st.button("Generate Consolidated Excel")

# ---------------- Helper Functions ----------------
def get_month(fp):
    month_map = {
        "04": "Apr", "05": "May", "06": "Jun",
        "07": "Jul", "08": "Aug", "09": "Sep",
        "10": "Oct", "11": "Nov", "12": "Dec",
        "01": "Jan", "02": "Feb", "03": "Mar"
    }
    return month_map.get(fp[:2], fp)

def extract_txval(table_data):
    total = 0
    for entry in table_data:
        for inv in entry.get("inv", []):
            for item in inv.get("itms", []):
                total += item.get("itm_det", {}).get("txval", 0)
    return round(total, 2)

# ---------------- Processing ----------------
if generate:

    if not uploaded_files:
        st.error("Please upload at least one GSTR-1 JSON file.")
        st.stop()

    st.success("Processing JSON files...")

    consolidated = {}

    for file in uploaded_files:
        data = json.load(file)

        month = get_month(data.get("fp", ""))

        tables = {
            "B2B": data.get("b2b", []),
            "B2CL": data.get("b2cl", []),
            "B2CS": data.get("b2cs", []),
            "CDNR": data.get("cdnr", []),
            "CDNUR": data.get("cdnur", []),
            "EXP": data.get("exp", [])
        }

        for table, table_data in tables.items():
            value = extract_txval(table_data)

            if table not in consolidated:
                consolidated[table] = {}

            consolidated[table][month] = value

    # ---------------- Create DataFrame ----------------
    df = pd.DataFrame(consolidated).T.fillna(0)

    month_order = [
        "Apr", "May", "Jun", "Jul", "Aug", "Sep",
        "Oct", "Nov", "Dec", "Jan", "Feb", "Mar"
    ]

    df = df.reindex(columns=month_order, fill_value=0)
    df.insert(0, "Table", df.index)
    df.reset_index(drop=True, inplace=True)

    # ---------------- Excel Output ----------------
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="GSTR-1 Consolidated")

    st.success("Consolidated Excel ready")

    st.download_button(
        label="Download Consolidated Excel",
        data=output.getvalue(),
        file_name="GSTR1_Consolidated.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )






