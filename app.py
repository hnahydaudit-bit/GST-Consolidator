import streamlit as st
import json
import pandas as pd
from collections import defaultdict
from io import BytesIO

st.set_page_config(page_title="GSTR-1 Consolidator", layout="wide")
st.title("GSTR-1 Month-wise Consolidation (Zen Style)")

MONTH_ORDER = ["Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec","Jan","Feb","Mar"]

TABLES = [
    ("4",  "B2B Invoices - 4A, 4B, 4C, 6B, 6C", "b2b"),
    ("5A", "B2C Invoices - 5A, 5B (Large)", "b2cl"),
    ("7",  "B2C Invoices - 7 (Others)", "b2cs"),
    ("6A", "Exports Invoices - 6A", "exp"),
    ("8",  "Nil rated, exempted and non GST outward supplies - 8", "nil"),
    ("9B-R", "Credit/Debit Notes (Registered) - 9B", "cdnr"),
    ("9B-U", "Credit/Debit Notes (Unregistered) - 9B", "cdnur"),
    ("11A", "Tax Liability (Advances Received) - 11A", "at"),
    ("11B", "Adjustment of Advances - 11B", "txpd")
]

def empty_month_dict():
    return {m: 0 for m in MONTH_ORDER}

summary_data = defaultdict(lambda: {
    "Taxable Value": empty_month_dict(),
    "IGST": empty_month_dict(),
    "CGST": empty_month_dict(),
    "SGST": empty_month_dict(),
    "Cess": empty_month_dict()
})

uploaded_files = st.file_uploader(
    "Upload Monthly GSTR-1 JSON files",
    type="json",
    accept_multiple_files=True
)

if uploaded_files:
    for file in uploaded_files:
        data = json.load(file)

        fp = data.get("fp", "")
        month = MONTH_ORDER[int(fp.split("")[0]) - 1] if fp[:2].isdigit() else None
        if month not in MONTH_ORDER:
            continue

        sec_sum = data.get("summary", {}).get("sec_sum", {})

        for _, _, key in TABLES:
            sec = sec_sum.get(key, {})
            summary_data[key]["Taxable Value"][month] += sec.get("txval", 0)
            summary_data[key]["IGST"][month] += sec.get("igst", 0)
            summary_data[key]["CGST"][month] += sec.get("cgst", 0)
            summary_data[key]["SGST"][month] += sec.get("sgst", 0)
            summary_data[key]["Cess"][month] += sec.get("cess", 0)

if st.button("Generate Consolidated Excel"):
    rows = []

    for tbl_no, tbl_name, key in TABLES:
        heading = f"GSTR-1 Summary calculated by Govt. Portal: {tbl_name}"
        rows.append({"Particulars": heading})

        for tax in ["Taxable Value", "IGST", "CGST", "SGST", "Cess"]:
            row = {"Particulars": tax}
            total = 0
            for m in MONTH_ORDER:
                val = summary_data[key][tax][m]
                row[m] = val
                total += val
            row["TOTAL"] = total
            rows.append(row)

    df = pd.DataFrame(rows).fillna(0)

    for col in MONTH_ORDER + ["TOTAL"]:
        if col not in df.columns:
            df[col] = 0

    df = df[["Particulars"] + MONTH_ORDER + ["TOTAL"]]

    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="GSTR-1 Summary")

    st.success("Consolidated GSTR-1 Summary Generated")
    st.download_button(
        "Download Excel",
        data=output.getvalue(),
        file_name="GSTR1_Consolidated_Zen_Style.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )







