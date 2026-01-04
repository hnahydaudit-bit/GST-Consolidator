import json
import pandas as pd
import streamlit as st
from io import BytesIO

st.set_page_config(page_title="GST Consolidator", layout="wide")

st.title("GST Consolidator")
st.caption("Month-wise consolidated GSTR-1 summary from JSON files")

uploaded_files = st.file_uploader(
    "Upload monthly GSTR-1 JSON files",
    type=["json"],
    accept_multiple_files=True
)

def get_month(fp):
    return pd.to_datetime(fp, format="%m%Y").strftime("%b-%y")

def empty_bucket():
    return {"Taxable Value": 0, "IGST": 0, "CGST": 0, "SGST": 0, "CESS": 0}

def add_tax(bucket, item):
    bucket["Taxable Value"] += item.get("txval", 0)
    for tax in item.get("itms", []):
        det = tax.get("itm_det", {})
        bucket["IGST"] += det.get("iamt", 0)
        bucket["CGST"] += det.get("camt", 0)
        bucket["SGST"] += det.get("samt", 0)
        bucket["CESS"] += det.get("csamt", 0)

if uploaded_files and st.button("Generate Consolidated Excel"):
    data = {}

    for file in uploaded_files:
        j = json.load(file)
        month = get_month(j["fp"])
        data.setdefault(month, {})

        tables = {
            "B2B": j.get("b2b", []),
            "B2C": j.get("b2cl", []) + j.get("b2cs", []),
            "CDNR": j.get("cdnr", []) + j.get("cdnur", []),
            "EXP": j.get("exp", [])
        }

        for table, entries in tables.items():
            bucket = empty_bucket()

            for e in entries:
                for inv in e.get("inv", []):
                    add_tax(bucket, inv)

            data[month][table] = bucket

    # Convert to pivot format
    rows = []
    for month, tables in data.items():
        for table, vals in tables.items():
            for k, v in vals.items():
                rows.append({
                    "Row": f"{table} - {k}",
                    "Month": month,
                    "Value": v
                })

    df = pd.DataFrame(rows)
    final_df = df.pivot(index="Row", columns="Month", values="Value").fillna(0)

    # Excel output
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        final_df.to_excel(writer, sheet_name="GSTR-1 Summary")

    st.success("Excel generated successfully")
    st.download_button(
        "Download Consolidated Excel",
        buffer.getvalue(),
        file_name="GST_Consolidated_GSTR1.xlsx"
    )

