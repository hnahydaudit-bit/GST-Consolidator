import streamlit as st
import json
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="GST Consolidator", layout="wide")
st.title("GST Consolidator")
st.caption("GSTR-1 Summary exactly matching Govt Portal / Zen Report")

uploaded_files = st.file_uploader(
    "Upload GSTR-1 JSON files",
    type="json",
    accept_multiple_files=True
)

generate = st.button("Generate Consolidated Excel", disabled=not uploaded_files)

MONTH_ORDER = ["Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec","Jan","Feb","Mar"]

TABLES = [
    ("4", "B2B Invoices - 4A, 4B, 4C, 6B, 6C", "b2b"),
    ("5", "B2C Invoices - 5A, 5B (Large)", "b2cl"),
    ("7", "B2C Invoices 7 - B2C (Others)", "b2cs"),
    ("6A", "Exports Invoices - 6A", "exp"),
    ("8", "Nil rated, exempted and non GST outward supplies - 8", "nil"),
    ("9B-R", "Credit/Debit Notes - 9B (Registered)", "cdnr"),
    ("9B-U", "Credit/Debit Notes - 9B (Unregistered)", "cdnur"),
    ("11A", "Tax Liability (Advances Received) - 11A", "at"),
    ("11B", "Adjustment of Advances - 11B", "txpd"),
]

def month_from_fp(fp):
    return {
        "04":"Apr","05":"May","06":"Jun","07":"Jul",
        "08":"Aug","09":"Sep","10":"Oct","11":"Nov",
        "12":"Dec","01":"Jan","02":"Feb","03":"Mar"
    }.get(fp[:2], fp)

def sum_invoice_section(section):
    tx = ig = cg = sg = cs = 0
    for e in section:
        for inv in e.get("inv", []):
            for it in inv.get("itms", []):
                d = it.get("itm_det", {})
                tx += d.get("txval",0)
                ig += d.get("iamt",0)
                cg += d.get("camt",0)
                sg += d.get("samt",0)
                cs += d.get("csamt",0)
    return tx, ig, cg, sg, cs

def sum_summary_section(section):
    tx = ig = cg = sg = cs = 0
    for e in section:
        tx += e.get("txval",0)
        ig += e.get("iamt",0)
        cg += e.get("camt",0)
        sg += e.get("samt",0)
        cs += e.get("csamt",0)
    return tx, ig, cg, sg, cs

if generate:
    rows = []

    for tno, tname, key in TABLES:
        rows.append([f"GSTR-1 Summary calculated by Govt. Portal: {tname}"])
        for label in ["Taxable Value","IGST","CGST","SGST","Cess"]:
            rows.append([label])

    df = pd.DataFrame(rows, columns=["Particulars"])

    for m in MONTH_ORDER:
        df[m] = 0

    for file in uploaded_files:
        data = json.load(file)
        month = month_from_fp(data.get("fp",""))

        r = 0
        for _, tname, key in TABLES:
            if key in ["b2b","b2cl","b2cs","exp","cdnr","cdnur"]:
                tx, ig, cg, sg, cs = sum_invoice_section(data.get(key,[]))
            else:
                tx, ig, cg, sg, cs = sum_summary_section(data.get(key,[]))

            df.loc[r+1,month] += tx
            df.loc[r+2,month] += ig
            df.loc[r+3,month] += cg
            df.loc[r+4,month] += sg
            df.loc[r+5,month] += cs
            r += 6

    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="GSTR-1 Summary")

    st.success("Excel generated exactly like Zen / Govt Portal")

    st.download_button(
        "Download Consolidated Excel",
        output.getvalue(),
        file_name="GSTR1_Govt_Portal_Summary.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
















