import streamlit as st
import json
import pandas as pd
from io import BytesIO

st.set_page_config("GST Consolidator", layout="wide")
st.title("GST Consolidator – Zen Style Summary")

MONTH_ORDER = ["Apr","May","Jun","Jul","Aug","Sep",
               "Oct","Nov","Dec","Jan","Feb","Mar"]

TABLE_MAP = {
    "B2B Invoices (4A/4B/4C/6B/6C)": "b2b",
    "B2C Large (5A/5B)": "b2cl",
    "B2C Others (7)": "b2cs",
    "Exports (6A)": "exp",
    "Nil/Exempt/Non-GST (8)": "nil",
    "CDN Registered (9B)": "cdnr",
    "CDN Unregistered (9B)": "cdnur",
    "Advances Received (11A)": "at",
    "Adjustment of Advances (11B)": "txpd",
    "Amended Supplies (9A/9C/10)": "b2ba"
}

def get_month(fp):
    return {
        "04":"Apr","05":"May","06":"Jun","07":"Jul",
        "08":"Aug","09":"Sep","10":"Oct","11":"Nov",
        "12":"Dec","01":"Jan","02":"Feb","03":"Mar"
    }.get(fp[:2], "NA")

def extract_values(section, key):
    tx = ig = cg = sg = cs = 0

    # B2B / B2CL / CDN / EXP
    if key in ["b2b","b2cl","cdnr","cdnur","exp","b2ba"]:
        for e in section:
            for inv in e.get("inv", []):
                for it in inv.get("itms", []):
                    d = it.get("itm_det", {})
                    tx += d.get("txval",0)
                    ig += d.get("iamt",0)
                    cg += d.get("camt",0)
                    sg += d.get("samt",0)
                    cs += d.get("csamt",0)

    # B2CS – Table 7
    elif key == "b2cs":
        for e in section:
            tx += e.get("txval",0)
            ig += e.get("iamt",0)
            cg += e.get("camt",0)
            sg += e.get("samt",0)
            cs += e.get("csamt",0)

    # NIL – Table 8
    elif key == "nil":
        for e in section:
            tx += (
                e.get("nil_amt",0) +
                e.get("expt_amt",0) +
                e.get("ngsup_amt",0)
            )

    # Advances – 11A & 11B
    elif key in ["at","txpd"]:
        for e in section:
            tx += e.get("ad_amt",0)
            ig += e.get("iamt",0)
            cg += e.get("camt",0)
            sg += e.get("samt",0)
            cs += e.get("csamt",0)

    return round(tx,2), round(ig,2), round(cg,2), round(sg,2), round(cs,2)

files = st.file_uploader(
    "Upload GSTR-1 JSON files",
    type="json",
    accept_multiple_files=True
)

if st.button("Generate Consolidated Excel") and files:
    rows = []

    for file in files:
        j = json.load(file)
        month = get_month(j.get("fp",""))

        for table, key in TABLE_MAP.items():
            section = j.get(key, [])
            tx, ig, cg, sg, cs = extract_values(section, key)

            for label, value in zip(
                ["Taxable Value","IGST","CGST","SGST","CESS"],
                [tx, ig, cg, sg, cs]
            ):
                row = {"Table": table, "Particulars": label}
                for m in MONTH_ORDER:
                    row[m] = 0
                row[month] = value
                rows.append(row)

    df = pd.DataFrame(rows)
    df = df.groupby(["Table","Particulars"], as_index=False).sum()
    df = df[["Table","Particulars"] + MONTH_ORDER]

    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="GSTR-1 Summary")

    st.success("Zen-style GSTR-1 Summary Generated")
    st.download_button(
        "Download Consolidated Excel",
        output.getvalue(),
        "GSTR1_Zen_Style_Summary.xlsx"
    )













