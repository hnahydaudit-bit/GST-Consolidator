import streamlit as st
import json
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="GST Consolidator", layout="wide")
st.title("GST Consolidator")

uploaded_files = st.file_uploader(
    "Upload GSTR-1 JSON files",
    type="json",
    accept_multiple_files=True
)

generate = st.button("Generate Consolidated Excel", disabled=not uploaded_files)

MONTH_ORDER = ["Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec","Jan","Feb","Mar"]
MONTH_MAP = {
    "04":"Apr","05":"May","06":"Jun","07":"Jul",
    "08":"Aug","09":"Sep","10":"Oct","11":"Nov",
    "12":"Dec","01":"Jan","02":"Feb","03":"Mar"
}

TAXES = ["Taxable Value","IGST","CGST","SGST","CESS"]

TABLES = [
    ("Table 4 – B2B", "b2b"),
    ("Table 5A – B2C (Large)", "b2cl"),
    ("Table 5B – B2C (Others)", "b2cs"),
    ("Table 6A – Exports (With Tax)", ("exp","Y")),
    ("Table 6B – Exports (Without Tax)", ("exp","N")),
    ("Table 7 – HSN Summary", "hsn"),
    ("Table 8 – Nil / Exempt / Non-GST", "nil"),
    ("Table 9B – CDNR", "cdnr"),
    ("Table 9B – CDNUR", "cdnur"),
    ("Table 11A – B2B Amendments", "b2ba"),
    ("Table 11B – B2C Amendments", "b2csa")
]

def blank_tax():
    return dict.fromkeys(TAXES, 0)

def extract_inv(data):
    v = blank_tax()
    for e in data:
        for inv in e.get("inv", []):
            for it in inv.get("itms", []):
                d = it.get("itm_det", {})
                v["Taxable Value"] += d.get("txval",0)
                v["IGST"] += d.get("iamt",0)
                v["CGST"] += d.get("camt",0)
                v["SGST"] += d.get("samt",0)
                v["CESS"] += d.get("csamt",0)
    return v

def extract_cdn(data):
    v = blank_tax()
    for e in data:
        for nt in e.get("nt", []):
            for it in nt.get("itms", []):
                d = it.get("itm_det", {})
                v["Taxable Value"] += d.get("txval",0)
                v["IGST"] += d.get("iamt",0)
                v["CGST"] += d.get("camt",0)
                v["SGST"] += d.get("samt",0)
                v["CESS"] += d.get("csamt",0)
    return v

def extract_hsn(hsn):
    v = blank_tax()
    for r in hsn.get("data", []):
        v["Taxable Value"] += r.get("txval",0)
        v["IGST"] += r.get("iamt",0)
        v["CGST"] += r.get("camt",0)
        v["SGST"] += r.get("samt",0)
        v["CESS"] += r.get("csamt",0)
    return v

def extract_nil(nil):
    v = blank_tax()
    for k in ["expt_amt","nil_amt","ngsup_amt"]:
        b = nil.get("sup_details",{}).get(k,{})
        v["Taxable Value"] += b.get("txval",0)
        v["IGST"] += b.get("iamt",0)
        v["CGST"] += b.get("camt",0)
        v["SGST"] += b.get("samt",0)
        v["CESS"] += b.get("csamt",0)
    return v

if generate:
    data_map = {}

    for table,_ in TABLES:
        for tax in TAXES:
            data_map[(table,tax)] = dict.fromkeys(MONTH_ORDER, 0)

    for f in uploaded_files:
        j = json.load(f)
        month = MONTH_MAP.get(j.get("fp","")[:2])

        for table,key in TABLES:
            if key == "b2b":
                vals = extract_inv(j.get("b2b",[]))
            elif key == "b2cl":
                vals = extract_inv(j.get("b2cl",[]))
            elif key == "b2cs":
                vals = extract_inv(j.get("b2cs",[]))
            elif key == "cdnr":
                vals = extract_cdn(j.get("cdnr",[]))
            elif key == "cdnur":
                vals = extract_cdn(j.get("cdnur",[]))
            elif key == "b2ba":
                vals = extract_inv(j.get("b2ba",[]))
            elif key == "b2csa":
                vals = extract_inv(j.get("b2csa",[]))
            elif key == "hsn":
                vals = extract_hsn(j.get("hsn",{}))
            elif key == "nil":
                vals = extract_nil(j.get("nil",{}))
            elif isinstance(key, tuple):
                vals = extract_inv([e for e in j.get("exp",[]) if e.get("pay")==key[1]])
            else:
                continue

            for t in TAXES:
                data_map[(table,t)][month] += round(vals[t],2)

    rows = []
    for table,_ in TABLES:
        rows.append({"Particulars": table})
        for t in TAXES:
            r = {"Particulars": f"   {t}"}
            r.update(data_map[(table,t)])
            rows.append(r)

    df = pd.DataFrame(rows)

    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as w:
        df.to_excel(w, index=False, sheet_name="GSTR-1 Consolidated")

    st.download_button(
        "Download Consolidated Excel",
        output.getvalue(),
        "GSTR1_Consolidated.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )










