import streamlit as st
import json
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="GST Consolidator", layout="wide")

# ------------------ UI ------------------
st.title("GST Consolidator")
st.caption("JSON based GST reports & consolidation tool")

uploaded_files = st.file_uploader(
    "Upload monthly GSTR-1 JSON files",
    type=["json"],
    accept_multiple_files=True
)

# ------------------ Helper Functions ------------------

def extract_month(json_data):
    """Extract return period month (Apr, May etc.)"""
    period = json_data.get("fp", "")
    month_map = {
        "04": "Apr", "05": "May", "06": "Jun",
        "07": "Jul", "08": "Aug", "09": "Sep",
        "10": "Oct", "11": "Nov", "12": "Dec",
        "01": "Jan", "02": "Feb", "03": "Mar"
    }
    return month_map.get(period[:2], period)

def extract_table_values(json_data):
    """Extract table-wise taxable value"""
    tables = {
        "B2B": json_data.get("b2b", []),
        "B2CL": json_data.get("b2cl", []),
        "B2CS": json_data.get("b2cs", []),
        "CDNR": json_data.get("cdnr", []),
        "CDNUR": json_data.get("cdnur", []),
        "EXP": json_data.get("exp", [])
    }

    summary = {}

    for table, entries in tables.items():
        taxable = 0
        for entry in entries:
            invs = entry.get("inv", [])
            for inv in invs:
                items = inv.get("itms", [])
                for item in items:
                    det = item.get("itm_det", {})
                    taxable += det.get("txval", 0)
        summary[table] = round(taxable, 2)

    return summary

# ------------------ Processing ------------------

if uploaded_files:
    st.success(f"{len(uploaded_files)} file(s) uploaded successfully")

    if st.button("Generate Consolidated Sheet"):
        st.success("Button clicked. Processing started.")

        consolidated = {}

        for file in uploaded_files:
            data = json.load(file)
            month = extract_month(data)
            table_data = extract_table_values(data)

            for table, value in table_data.items():
                if table not in consolidated:
                    consolidated[table] = {}
                consolidated[table][month] = value

        # Convert to DataFrame
        df = pd.DataFrame(consolidated).T.fillna(0)

        # Sort months Apr–Mar
        month_order = ["Apr","May","Jun","Jul","Aug","Sep",
                       "Oct","Nov","Dec","Jan","Feb","Mar"]
        df = df.reindex(columns=month_order, fill_value=0)

        df.insert(0, "Table", df.index)
        df.reset_index(drop=True, inplace=True)

        # Create Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="GSTR-1 Consolidated")

        st.success("Consolidated Excel generated successfully")

        st.download_button(
            label="Download Consolidated Excel",
            data=output.getvalue(),
            file_name="GSTR1_Consolidated.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )


