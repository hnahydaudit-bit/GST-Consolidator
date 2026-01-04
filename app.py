import streamlit as st
import json
import pandas as pd
from io import BytesIO

st.set_page_config("GST Consolidator", layout="wide")
st.title("GST Consolidator – Zen Style Summary")

MONTH_ORDER = ["Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec","Jan","Feb","Mar"]

TABLE_MAP = {
    "B2B Invoices (4A/4B/4C/6B/6C)": ["b2b"],
    "B2C Large (5A/5B)": ["b2cl"],
    "B2C Others (7)": ["b2cs"],
    "Exports (6A)": ["exp"],
    "Nil/Exempt/Non-GST (8)": ["nil"],
    "CDN Registered (9B)": ["cdnr"],
    "CDN Unregistered (9B)": ["cdnur"],
    "Advances Received (11A)": ["at"],
    "Adjustment of Advances (11B)": ["txpd"],
    "Amended B2B/B2C/Exports/CDN": ["b2ba","b2cla","b2csa","expa","cdnra","cdnura"]
}

def get_month(fp):
    return {"04":"Apr","05":"May","06":"Jun","07":"Jul","08":"Aug","09":"Sep",
            "10":"Oct","11":"Nov","12":"Dec","01":"Jan","02":"Feb","03":"Mar"}.get(fp[:2],"NA")

def sum_section(data):
    tx = ig = cg = sg = cs = 0
    for e in data:
        for inv in e.get("inv", []):
            for it in inv.get("itms", []):
                d = it.get("itm_det", {})
                tx += d.get("txval",0)
                ig += d.get("iamt",0)
                cg += d.get("camt",0)
                sg += d.get("samt",0)
                cs += d.get("csamt",0)
    return tx, ig, cg, sg, cs

files = st.file_uploader("Upload GSTR-1 JSON files", type="json", accept_multiple_files=True)

if st.button("Generate Consolidated Excel") and files:
    rows = []

    for file in files:
        j = json.load(file)
        month = get_month(j.get("fp",""))

        for table, keys in TABLE_MAP.items():
            totals = [0,0,0,0,0]
            for k in keys:
                if k in j:
                    t = sum_section(j[k])
                    totals = [totals[i]+t[i] for i in range(5)]

            labels = ["Taxable Value","IGST","CGST","SGST","CESS"]
            for i,l in enumerate(labels):
                row = {"Table":table,"Particulars":l}
                for m in MONTH_ORDER:
                    row[m]=0
                row[month]=round(totals[i],2)
                rows.append(row)

    df = pd.DataFrame(rows)
    df = df.groupby(["Table","Particulars"],as_index=False).sum()
    df = df[["Table","Particulars"]+MONTH_ORDER]

    output = BytesIO()
    with pd.ExcelWriter(output,engine="xlsxwriter") as writer:
        df.to_excel(writer,index=False,sheet_name="GSTR-1 Summary")

    st.success("Zen-style Summary Generated")
    st.download_button("Download Excel",output.getvalue(),
                       "GSTR1_Zen_Style_Summary.xlsx")












