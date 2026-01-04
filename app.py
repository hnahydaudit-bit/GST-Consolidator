import streamlit as st
import json
import pandas as pd
from io import BytesIO

# ---------------- Page Config ----------------
st.set_page_config(page_title="GST Consolidator", layout="wide")
st.title("GST Consolidator")
st.caption("GSTR-1 JSON → Table-wise & Month-wise Consolidated Excel")

# ---------------- Upload ----------------
uploaded_files = st.file_uploader(
    "Upload GSTR-1 JSON files (Any number of months)",
    type="json",
    accept_multiple_files=True
)

generate = st.button(
    "Generate Consolidated Excel",
    disabled=not uploaded_files
)

# ---------------- Helpers ----------------
MONTH_MAP = {
    "04": "Apr", "05": "May", "06": "Jun",
    "07": "Jul", "08": "Aug", "09": "Sep",
    "10": "Oct", "11": "Nov", "12": "Dec",
    "01": "Jan", "02": "Feb", "03": "Mar"
}

MONTH_ORDER = ["Apr","May","Jun","Jul","Aug","Sep",
               "Oct","Nov","Dec","Jan","Feb","Mar"]

TABLE_MAP = {
    "Table 4 - B2B": "b2b",
    "Table 5A - B2C (Large)": "b2cl",
    "Table 5B - B2C (Others)": "b2cs",
    "Table 6A - Exports (With Tax)": ("exp", "Y"),
    "Table 6B - Exports (Without Tax)": ("exp", "N"),
    "Table 9B - CDNR": "cdnr",
    "Table 9B - CDNUR": "cdnur",
    "Table 11A - B2B Amendments": "b2ba",
    "Table 11B - B2C Amendments": "b2csa"
}

def get_month(fp):
    return MONTH_MAP.get(fp[:2], fp)

def extract_values(data, export_flag=None):
    txval = igst = cgst = sgst = cess = 0

    for entry in data:
        if export_flag is not None and entry.get("pay") != export_flag:
            continue

        for inv in entry.get("inv", []):
            for item in inv.get("itms", []):
                det = item.get("itm_det", {})
                txval += det.get("txval", 0)
                igst += det.get("iamt", 0)
                cgst += det.get("camt", 0)
                sgst += det.get("samt", 0)
                cess += det.get("csamt", 0)

    return {
        "Taxable Value": round(txval, 2),
        "IGST": round(igst, 2),
        "CGST": round(cgst, 2),
        "SGST": round(sgst, 2),
        "CESS": round(cess, 2)
    }

# ---------------- Processing ----------------
if generate:
    st.success("Processing JSON files...")

    result = {}

    for file in uploaded_files:
        data = json.load(file)
        month = get_month(data.get("fp", ""))

        for table_name, key in TABLE_MAP.items():
            if isinstance(key, tuple):
                table_key, flag = key
                values = extract_values(data.get(table_key, []), flag)
            else:
                values = extract_values(data.get(key, []))

            for tax_type, amount in values.items():
                row = f"{table_name} - {tax_type}"
                if row not in result:
                    result[row] = {}
                result[row][month] = amount

    df = pd.DataFrame(result).T.fillna(0)
    df = df.reindex(columns=MONTH_ORDER, fill_value=0)
    df.insert(0, "Particulars", df.index)
    df.reset_index(drop=True, inplace=True)

    # ---------------- Excel ----------------
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="GSTR-1 Consolidated")

    st.success("Consolidated Excel Ready")

    st.download_button(
        "Download Consolidated Excel",
        output.getvalue(),
        "GSTR1_Consolidated.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )







