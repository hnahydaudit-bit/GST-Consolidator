import streamlit as st
import json
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="GSTR-1 Consolidator", layout="wide")
st.title("GSTR-1 Consolidator")
st.caption("Zen-style GSTR-1 Summary using GST Portal calculated data")

uploaded_files = st.file_uploader(
    "Upload monthly GSTR-1 JSON files",
    type="json",
    accept_multiple_files=True
)

MONTH_ORDER = ["Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec","Jan","Feb","Mar"]

def get_month(fp):
    return {
        "04":"Apr","05":"May","06":"Jun","07":"Jul","08":"Aug","09":"Sep",
        "10":"Oct","11":"Nov","12":"Dec","01":"Jan","02":"Feb","03":"Mar"
    }.get(fp[:2], fp)

# Table mapping exactly like GST portal / Zen
TABLE_MAP = [
    ("4 B2B Invoices", "b2b"),
    ("5A B2C (Large)", "b2cl"),
    ("5B B2C (Others)", "b2cs"),
    ("6A Exports", "exp"),
    ("8 Nil / Exempt / Non-GST", "nil"),
    ("9B CDNR (Registered)", "cdnr"),
    ("9B CDNUR (Unregistered)", "cdnur"),
    ("11A Advances Received", "at"),
    ("11B Adjustment of Advances", "atadj"),
]

TAX_KEYS = [
    ("Taxable Value", "txval"),
    ("IGST", "igst"),
    ("CGST", "cgst"),
    ("SGST", "sgst"),
    ("CESS", "cess"),
]

if st.button("Generate Consolidated Excel", disabled=not uploaded_files):

    rows = []

    for file in uploaded_files:
        data = json.load(file)
        month = get_month(data.get("fp",""))

        sec_sum = data.get("sec_sum", {})

        for table_name, key in TABLE_MAP:
            section = sec_sum.get(key, {})

            for label, tax_key in TAX_KEYS:
                rows.append({
                    "Particulars": f"{table_name} - {label}",
                    "Month": month,
                    "Value": section.get(tax_key, 0)
                })

    df = pd.DataFrame(rows)

    pivot = (
        df.pivot_table(
            index="Particulars",
            columns="Month",
            values="Value",
            aggfunc="sum",
            fill_value=0
        )
        .reindex(columns=MONTH_ORDER, fill_value=0)
    )

    pivot["TOTAL"] = pivot.sum(axis=1)
    pivot.reset_index(inplace=True)

    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        pivot.to_excel(writer, index=False, sheet_name="GSTR-1 Summary")

    output.seek(0)

    st.success("Consolidated GSTR-1 summary ready")

    st.download_button(
        "⬇ Download Consolidated Excel",
        data=output,
        file_name="GSTR1_Zen_Style_Summary.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )




