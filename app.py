import streamlit as st
import json
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="GST Consolidator", layout="wide")
st.title("GST Consolidator – Govt GSTR-1 Summary")

uploaded_files = st.file_uploader(
    "Upload GSTR-1 JSON files",
    type="json",
    accept_multiple_files=True
)

generate = st.button("Generate Consolidated Excel", disabled=not uploaded_files)

MONTHS = ["Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec","Jan","Feb","Mar"]
MONTH_MAP = {"04":"Apr","05":"May","06":"Jun","07":"Jul","08":"Aug","09":"Sep",
             "10":"Oct","11":"Nov","12":"Dec","01":"Jan","02":"Feb","03":"Mar"}

TAXES = ["Taxable Value","IGST","CGST","SGST","CESS"]

TABLES = [
    ("B2B Invoices – Table 4", "b2b"),
    ("B2C (Large) – Table 5", "b2cl"),
    ("B2C (Others) – Table 7", "b2cs"),
    ("Exports – Table 6A", "exp"),
    ("Nil / Exempt – Table 8", "nil"),
    ("CDNR – Table 9B", "cdnr"),
    ("CDNUR – Table 9B", "cdnur"),
    ("Amended B2B / B2CL / EXP – Table 9A", "b2ba"),
    ("Amended B2CS – Table 10", "b2csa"),
    ("Amended CDNR / CDNUR – Table 9C", "cdnra"),
    ("Advances Received – Table 11A", "at"),
    ("Adjustment of Advances – Table 11B", "txpd")
]

def zero():
    return dict.fromkeys(TAXES, 0)

def add_itm(v, d):
    v["Taxable Value"] += d.get("txval",0)
    v["IGST"] += d.get("iamt",0)
    v["CGST"] += d.get("camt",0)
    v["SGST"] += d.get("samt",0)
    v["CESS"] += d.get("csamt",0)

def extract_inv(data):
    v = zero()
    for e in data:
        for inv in e.get("inv",[]):
            for it in inv.get("itms",[]):
                add_itm(v, it.get("itm_det",{}))
    return v

def extract_nt(data):
    v = zero()
    for e in data:
        for nt in e.get("nt",[]):
            for it in nt.get("itms",[]):
                add_itm(v, it.get("itm_det",{}))
    return v

def extract_nil(nil):
    v = zero()
    for k in ["expt_amt","nil_amt","ngsup_amt"]:
        b = nil.get("sup_details",{}).get(k,{})
        add_itm(v, b)
    return v

def extract_adv(data):
    v = zero()
    for e in data:
        v["Taxable Value"] += e.get("ad_amt",0)
        v["IGST"] += e.get("iamt",0)
        v["CGST"] += e.get("camt",0)
        v["SGST"] += e.get("samt",0)
        v["CESS"] += e.get("csamt",0)
    return v

if generate:
    store = {(t,x): dict.fromkeys(MONTHS,0) for t,_ in TABLES for x in TAXES}

    for f in uploaded_files:
        j = json.load(f)
        m = MONTH_MAP.get(j.get("fp","")[:2])

        for table,key in TABLES:
            if key in ["b2b","b2cl","b2cs","exp","b2ba","b2csa"]:
                vals = extract_inv(j.get(key,[]))
            elif key in ["cdnr","cdnur","cdnra"]:
                vals = extract_nt(j.get(key,[]))
            elif key == "nil":
                vals = extract_nil(j.get("nil",{}))
            elif key in ["at","txpd"]:
                vals = extract_adv(j.get(key,[]))
            else:
                continue

            for t in TAXES:
                store[(table,t)][m] += round(vals[t],2)

    rows=[]
    for table,_ in TABLES:
        rows.append({"Particulars": table})
        for t in TAXES:
            r={"Particulars":"   "+t}
            r.update(store[(table,t)])
            rows.append(r)

    df=pd.DataFrame(rows)

    output=BytesIO()
    with pd.ExcelWriter(output,engine="xlsxwriter") as w:
        df.to_excel(w,index=False,sheet_name="GSTR-1 Summary")

    st.download_button(
        "Download GSTR-1 Summary Excel",
        output.getvalue(),
        "GSTR1_Govt_Summary.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )











