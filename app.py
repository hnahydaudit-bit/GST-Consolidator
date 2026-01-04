import streamlit as st
import json
import pandas as pd
from io import BytesIO

# ---------------- Page Setup ----------------
st.set_page_config("GST Consolidator", layout="wide")
st.title("GST Consolidator – Zen Style GSTR-1 Summary")

MONTHS = ["Apr","May","Jun","Jul","Aug","Sep",
          "Oct","Nov","Dec","Jan","Feb","Mar"]

TABLES = {
    "Table 4 – B2B Invoices (4A/4B/4C/6B/6C)": "b2b",
    "Table 5 – B2C (Large)": "b2cl",
    "Table 7 – B2C (Others)": "b2cs",
    "Table 6 – Exports": "exp",
    "Table 8 – Nil / Exempt / Non-GST": "nil",
    "Table 9 – CDNR": "cdnr",
    "Table 9 – CDNUR": "cdnur",
    "Table 11A – Advances Received": "at",
    "Table 11B – Adjustment of Advances": "txpd",
    "Table 9A/9C/10 – Amendments": "b2ba"
}

def get_month(fp):
    return {
        "04":"Apr","05":"May","06":"Jun","07":"Jul",
        "08":"Aug","09":"Sep","10":"Oct","11":"Nov",
        "12":"Dec","01":"Jan","02":"Feb","03":"Mar"
    }.get(fp[:2], "NA")

def extract_values(j, key):
    tx = ig = cg = sg = cs = 0

    if key in ["b2b","b2cl","cdnr","cdnur","exp","b2ba"]:
        for e in j.get(key, []):
            for inv in e.get("inv", []):
                for it in inv.get("itms", []):
                    d = it.get("itm_det", {})
                    tx += d.get("txval",0)
                    ig += d.get("iamt",0)
                    cg += d.get("camt",0)
                    sg += d.get("samt",0)
                    cs += d.get("csamt",0)

    elif key == "b2cs":
        for e in j.get("b2cs", []):
            tx += e.get("txval",0)
            ig += e.get("iamt",0)
            cg += e.get("camt",0)
            sg += e.get("samt",0)
            cs += e.get("csamt",0)

    elif key == "nil":
        nil_data = j.get("nil", {})
        for e in nil_data.get("inv", []):
            tx += (
                e.get("nil_amt",0) +
                e.get("expt_amt",0) +
                e.get("ngsup_amt",0)
            )

    elif key in ["at","txpd"]:
        for e in j.get(key, []):
            tx += e.get("ad_amt",0)
            ig += e.get("iamt",0)
            cg += e.get("camt",0)
            sg += e.get("samt",0)
            cs += e.get("csamt",0)

    return round(tx,2), round(ig,2), round(cg,2), round(sg,2), round(cs,2)

# ---------------- Upload ----------------
files = st.file_uploader(
    "Upload GSTR-1 JSON files (any months)",
    type="json",
    accept_multiple_files=True
)

# ---------------- Generate ----------------
if st.button("Generate Consolidated Excel") and files:
    raw_rows = []

    for file in files:
        j = json.load(file)
        month = get_month(j.get("fp",""))

        for table, key in TABLES.items():
            tx, ig, cg, sg, cs = extract_values(j, key)

            for label, value in zip(
                ["Taxable Value","IGST","CGST","SGST","CESS"],
                [tx, ig, cg, sg, cs]
            ):
                row = {"Table": table, "Particulars": label}
                for m in MONTHS:
                    row[m] = 0
                row[month] = value
                raw_rows.append(row)

    df = pd.DataFrame(raw_rows)
    df = df.groupby(["Table","Particulars"], as_index=False).sum()
    df = df[["Table","Particulars"] + MONTHS]

    # -------- Zen-style visual layout --------
    final_blocks = []

    for table in df["Table"].unique():
        temp = df[df["Table"] == table].copy()
        temp.insert(0, "Table Name", [""] * len(temp))
        temp.iloc[0, 0] = table
        final_blocks.append(temp)

    final_df = pd.concat(final_blocks, ignore_index=True)
    final_df.drop(columns=["Table"], inplace=True)

    # ---------------- Excel ----------------
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        final_df.to_excel(writer, index=False, sheet_name="GSTR-1 Summary")

    st.success("Zen-style consolidated summary generated")
    st.download_button(
        "Download Consolidated Excel",
        output.getvalue(),
        "GSTR1_Zen_Style_Summary.xlsx"
    )















