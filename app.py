import streamlit as st
import json
import pandas as pd
from io import BytesIO

# ---------------- PAGE CONFIG ----------------
st.set_page_config("GST Consolidator", layout="wide")
st.title("GST Consolidator")
st.caption("Zen-style GSTR-1 Summary | Month-wise Consolidation")

# ---------------- MONTH MAP ----------------
MONTH_MAP = {
    "04":"Apr","05":"May","06":"Jun","07":"Jul","08":"Aug","09":"Sep",
    "10":"Oct","11":"Nov","12":"Dec","01":"Jan","02":"Feb","03":"Mar"
}
MONTH_ORDER = list(MONTH_MAP.values())

# ---------------- TABLE DEFINITIONS ----------------
TABLES = [
    ("4", "B2B Invoices - 4A, 4B, 4C, 6B, 6C", ["b2b"]),
    ("5A", "B2C Invoices - 5A, 5B (Large)", ["b2cl"]),
    ("7", "B2C Invoices - 7 (Others)", ["b2cs"]),
    ("6A", "Exports Invoices - 6A", ["exp"]),
    ("8", "Nil Rated / Exempt / Non-GST Supplies - 8", ["nil"]),
    ("9B-R", "Credit/Debit Notes (Registered) - 9B", ["cdnr"]),
    ("9B-U", "Credit/Debit Notes (Unregistered) - 9B", ["cdnur"]),
    ("11A", "Tax Liability (Advances Received) - 11A", ["at"]),
    ("11B", "Adjustment of Advances - 11B", ["atadj"]),
    ("9A", "Amended Invoices - 9A", ["b2ba","b2cla","expa"]),
    ("10", "Amended B2C (Others) - 10", ["b2csa"]),
    ("9C-R", "Amended Credit/Debit Notes (Reg) - 9C", ["cdnra"]),
    ("9C-U", "Amended Credit/Debit Notes (Unreg) - 9C", ["cdnura"]),
]

# ---------------- FILE UPLOAD ----------------
files = st.file_uploader(
    "Upload GSTR-1 JSON files",
    type="json",
    accept_multiple_files=True
)

# ---------------- BUTTON ----------------
generate = st.button(
    "Generate Consolidated Excel",
    disabled=not files
)

# ---------------- CORE EXTRACTION LOGIC ----------------
def extract_section(section):
    tx = ig = cg = sg = cs = 0

    if isinstance(section, dict):
        for v in section.values():
            if isinstance(v, dict):
                tx += v.get("txval", 0)
                ig += v.get("iamt", 0)
                cg += v.get("camt", 0)
                sg += v.get("samt", 0)
                cs += v.get("csamt", 0)

    elif isinstance(section, list):
        for e in section:
            if isinstance(e, dict):
                tx += e.get("txval", 0)
                ig += e.get("iamt", 0)
                cg += e.get("camt", 0)
                sg += e.get("samt", 0)
                cs += e.get("csamt", 0)

                for inv in e.get("inv", []):
                    for it in inv.get("itms", []):
                        d = it.get("itm_det", {})
                        tx += d.get("txval", 0)
                        ig += d.get("iamt", 0)
                        cg += d.get("camt", 0)
                        sg += d.get("samt", 0)
                        cs += d.get("csamt", 0)

    return round(tx,2), round(ig,2), round(cg,2), round(sg,2), round(cs,2)

# ---------------- PROCESS ----------------
if generate:
    rows = []

    for file in files:
        j = json.load(file)
        month = MONTH_MAP.get(j.get("fp","")[:2], j.get("fp",""))

        for no, name, keys in TABLES:
            tx = ig = cg = sg = cs = 0

            for k in keys:
                if k in j:
                    t = extract_section(j[k])
                    tx += t[0]; ig += t[1]; cg += t[2]; sg += t[3]; cs += t[4]

            rows.extend([
                {"Particulars": f"GSTR-1 Summary calculated by Govt. Portal:{name}", month: ""},
                {"Particulars": "Taxable Value", month: tx},
                {"Particulars": "IGST", month: ig},
                {"Particulars": "CGST", month: cg},
                {"Particulars": "SGST", month: sg},
                {"Particulars": "Cess", month: cs},
            ])

    # ---------------- DATAFRAME ----------------
    df = pd.DataFrame(rows).fillna(0)
    df = df.groupby("Particulars", as_index=False).sum(numeric_only=True)
    df = df[["Particulars"] + MONTH_ORDER]

    # ---------------- EXCEL ----------------
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="GSTR-1 Summary")

    st.success("Zen-style consolidated report ready")

    st.download_button(
        "Download Consolidated Excel",
        output.getvalue(),
        "GSTR1_Zen_Style_Consolidated.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
