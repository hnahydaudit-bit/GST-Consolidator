import streamlit as st
import json
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="GST Consolidator", layout="wide")
st.title("GST Consolidator")
st.caption("GSTR-1 JSON → Table-wise & Month-wise Consolidated Excel")

uploaded_files = st.file_uploader(
    "Upload GSTR-1 JSON files",
    type="json",
    accept_multiple_files=True
)

generate = st.button("Generate Consolidated Excel", disabled=not uploaded_files)

MONTH_MAP = {
    "04": "Apr","05": "May","06": "Jun","07": "Jul",
    "08": "Aug","09": "Sep","10": "Oct","11": "Nov",
    "12": "Dec","01": "Jan","02": "Feb","03": "Mar"
}
MONTH_ORDER = list(MONTH_MAP.values())

TABLES = [
    ("Table 4 – B2B", "b2b"),
    ("Table 5A – B2C (Large)", "b2cl"),
    ("Table 5B – B2C (Others)", "b2cs"),
    ("Table 6A – Exports (With Tax)", ("exp","Y")),
    ("Table 6B – Exports (Without Tax)", ("exp","N")),
    ("Table 8 – Nil / Exempt / Non-GST", "nil"),
    ("Table 9B – CDNR", "cdnr"),
    ("Table 9B – CDNUR", "cdnur"),
    ("Table 11A – B2B Amendments", "b2ba"),
    ("Table 11B – B2C Amendments", "b2csa")
]

def extract_invoice_values(data, pay_flag=None):
    vals = dict.fromkeys(["Taxable Value","IGST","CGST","SGST","CESS"],0)
    for e in data:
        if pay_flag and e.get("pay") != pay_flag:
            continue
        for inv in e.get("inv", []):
            for it in inv.get("itms", []):
                d = it.get("itm_det", {})
                vals["Taxable Value"] += d.get("txval",0)
                vals["IGST"] += d.get("iamt",0)
                vals["CGST"] += d.get("camt",0)
                vals["SGST"] += d.get("samt",0)
                vals["CESS"] += d.get("csamt",0)
    return vals

def extract_table8(nil):
    vals = dict.fromkeys(["Taxable Value","IGST","CGST","SGST","CESS"],0)
    sd = nil.get("sup_details",{})
    for k in ["expt_amt","nil_amt","ngsup_amt"]:
        for tax in vals:
            vals[tax] += sd.get(k,{}).get(tax.lower().replace(" ","_"),0)
    return vals

if generate:
    final = {}

    for f in uploaded_files:
        data = json.load(f)
        month = MONTH_MAP.get(data.get("fp","")[:2])

        for table_name, key in TABLES:
            if table_name not in final:
                final[table_name] = {}

            if key == "nil":
                vals = extract_table8(data.get("nil",{}))
            elif isinstance(key, tuple):
                vals = extract_invoice_values(data.get(key[0],[]), key[1])
            else:
                vals = extract_invoice_values(data.get(key,[]))

            for tax,val in vals.items():
                final.setdefault((table_name,tax),{})[month] = round(val,2)

    rows = []
    for table,_ in TABLES:
        rows.append({ "Particulars": table })
        for tax in ["Taxable Value","IGST","CGST","SGST","CESS"]:
            row = { "Particulars": f"   {tax}" }
            row.update(final.get((table,tax),{}))
            rows.append(row)

    df = pd.DataFrame(rows).fillna(0)
    df = df[["Particulars"] + MONTH_ORDER]

    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="GSTR-1 Consolidated")

    st.download_button(
        "Download Consolidated Excel",
        output.getvalue(),
        "GSTR1_Consolidated.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )








