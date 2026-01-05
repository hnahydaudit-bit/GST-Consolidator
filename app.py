import streamlit as st
import json
import pandas as pd
from collections import defaultdict

st.set_page_config(page_title="GSTR-3B Consolidator", layout="wide")
st.title("GSTR-3B Month-wise Consolidation (Zen Style)")

MONTH_ORDER = ["Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec","Jan","Feb","Mar"]

# -------------------- Helpers --------------------

def get_month_from_json(data):
    """
    Extract return period month safely
    """
    period = data.get("ret_period", "")
    if len(period) != 6:
        return None
    month_map = {
        "04":"Apr","05":"May","06":"Jun","07":"Jul","08":"Aug","09":"Sep",
        "10":"Oct","11":"Nov","12":"Dec","01":"Jan","02":"Feb","03":"Mar"
    }
    return month_map.get(period[4:6])

def safe_sum(items, key):
    return sum(float(i.get(key, 0) or 0) for i in items)

def extract_3b_values(data):
    """
    Extract Zen-style values from GSTR-3B
    """
    out = defaultdict(lambda: {"Taxable Value":0,"IGST":0,"CGST":0,"SGST":0,"Cess":0})

    sup = data.get("sup_details", {})

    sections = {
        "Outward taxable supplies (other than zero rated, nil rated and exempted)": "osup_det",
        "Outward taxable supplies (zero rated)": "osup_zero",
        "Other outward supplies (nil rated, exempted)": "osup_nil_exmp",
        "Inward supplies liable to reverse charge": "isup_rev",
        "Non-GST outward supplies": "non_gst_sup"
    }

    for name, key in sections.items():
        sec = sup.get(key, {})
        out[name]["Taxable Value"] += float(sec.get("txval",0) or 0)
        out[name]["IGST"] += float(sec.get("igst",0) or 0)
        out[name]["CGST"] += float(sec.get("cgst",0) or 0)
        out[name]["SGST"] += float(sec.get("sgst",0) or 0)
        out[name]["Cess"] += float(sec.get("cess",0) or 0)

    # ITC Section
    itc = data.get("itc_elg", {})
    for k in ["itc_avl","itc_rev","itc_net","itc_inelg"]:
        rows = itc.get(k, [])
        for r in rows:
            out[f"ITC – {k.upper()}"]["IGST"] += float(r.get("igst",0) or 0)
            out[f"ITC – {k.upper()}"]["CGST"] += float(r.get("cgst",0) or 0)
            out[f"ITC – {k.upper()}"]["SGST"] += float(r.get("sgst",0) or 0)
            out[f"ITC – {k.upper()}"]["Cess"] += float(r.get("cess",0) or 0)

    # Tax payment
    tax = data.get("tax_paid", {})
    for k in ["igst","cgst","sgst","cess"]:
        out["Tax Paid"][k.upper()] += float(tax.get(k,0) or 0)

    return out

# -------------------- Upload --------------------

files = st.file_uploader(
    "Upload GSTR-3B JSON files",
    type="json",
    accept_multiple_files=True
)

if files:
    final = defaultdict(lambda: {m:0 for m in MONTH_ORDER})

    for f in files:
        data = json.load(f)
        month = get_month_from_json(data)
        if not month:
            continue

        extracted = extract_3b_values(data)

        for part, vals in extracted.items():
            for k,v in vals.items():
                final[f"{part} – {k}"][month] += v

    df = pd.DataFrame(final).T.reset_index()
    df.rename(columns={"index":"Particulars"}, inplace=True)

    for m in MONTH_ORDER:
        if m not in df.columns:
            df[m] = 0

    df = df[["Particulars"] + MONTH_ORDER]

    st.success("✅ Consolidation completed")
    st.dataframe(df, use_container_width=True)

    st.download_button(
        "⬇ Download Excel",
        df.to_excel(index=False, engine="openpyxl"),
        "GSTR3B_Zen_Summary.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )



