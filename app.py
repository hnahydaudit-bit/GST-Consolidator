import streamlit as st
import json
import pandas as pd
from io import BytesIO

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="GST Consolidator", layout="wide")
st.title("GST Consolidator")
st.caption("Zen-style GSTR-1 Summary | Month-wise Consolidation")

# ---------------- MONTH CONFIG ----------------
MONTH_MAP = {
    "04": "Apr", "05": "May", "06": "Jun",
    "07": "Jul", "08": "Aug", "09": "Sep",
    "10": "Oct", "11": "Nov", "12": "Dec",
    "01": "Jan", "02": "Feb", "03": "Mar"
}
MONTH_ORDER = list(MONTH_MAP.values())

# ---------------- TABLE DEFINITIONS ----------------
TABLES = [
    ("4", "B2B Invoices - 4A, 4B, 4C, 6B, 6C", ["b2b"]),
    ("5A", "B2C Invoices - 5A, 5B (Large)", ["b2cl"]),
    ("7", "B2C Invoices - 7 (Others)", ["b2cs"]),
    ("6A", "Exports Invoices - 6A", ["exp"]),
    ("8", "Nil rated, exempted and non GST outward supplies - 8", ["nil"]),
    ("9BR", "Credit/Debit Notes (Registered) - 9B", ["cdnr"]),
    ("9BU", "Credit/Debit Notes (Unregistered) - 9B", ["cdnur"]),
    ("11A", "Tax Liability (Advances Received) - 11A", ["at"]),
    ("11B", "Adjustment of Advances - 11B", ["atadj"]),
]

# ---------------- FILE UPLOAD ----------------
files = st.file_uploader(
    "Upload GSTR-1 JSON files (Any number of months)",
    type="json",
    accept_multiple_files=True
)

generate = st.button("Generate Consolidated Excel", disabled=not files)

# ---------------- VALUE EXTRACTION ----------------
def extract_values(section):
    tx = ig = cg = sg = cs = 0

    if isinstance(section, list):
        for e in section:
            for inv in e.get("inv", []):
                for it in inv.get("itms", []):
                    d = it.get("itm_det", {})
                    tx += d.get("txval", 0)
                    ig += d.get("iamt", 0)
                    cg += d.get("camt", 0)
                    sg += d.get("samt", 0)
                    cs += d.get("csamt", 0)

    if isinstance(section, dict):
        for v in section.values():
            if isinstance(v, dict):
                tx += v.get("txval", 0)
                ig += v.get("iamt", 0)
                cg += v.get("camt", 0)
                sg += v.get("samt", 0)
                cs += v.get("csamt", 0)

    return round(tx,2), round(ig,2), round(cg,2), round(sg,2), round(cs,2)

# ---------------- PROCESS ----------------
if generate:
    rows = []

    for f in files:
        data = json.load(f)
        month = MONTH_MAP.get(data.get("fp","")[:2], data.get("fp",""))

        for _, table_name, keys in TABLES:
            tx = ig = cg = sg = cs = 0

            for k in keys:
                if k in data:
                    t = extract_values(data[k])
                    tx += t[0]
                    ig += t[1]
                    cg += t[2]
                    sg += t[3]
                    cs += t[4]

            rows.extend([
                {"Particulars": f"GSTR-1 Summary calculated by Govt. Portal:{table_name}", month: ""},
                {"Particulars": "Taxable Value", month: tx},
                {"Particulars": "IGST", month: ig},
                {"Particulars": "CGST", month: cg},
                {"Particulars": "SGST", month: sg},
                {"Particulars": "Cess", month: cs},
            ])

    # ---------------- DATAFRAME FIX ----------------
    df = pd.DataFrame(rows)

    # Ensure all months exist
    for m in MONTH_ORDER:
        if m not in df.columns:
            df[m] = 0

    df = df.fillna(0)
    df = df.groupby("Particulars", as_index=False).sum()

    df = df[["Particulars"] + MONTH_ORDER]

    # ---------------- EXCEL OUTPUT ----------------
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="GSTR-1 Summary")

    st.success("Zen-style consolidated Excel generated")

    st.download_button(
        "Download Consolidated Excel",
        output.getvalue(),
        "GSTR1_Zen_Summary.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

