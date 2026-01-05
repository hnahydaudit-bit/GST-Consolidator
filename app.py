import streamlit as st
import json
import pandas as pd
from collections import defaultdict
from io import BytesIO

st.set_page_config(page_title="GSTR-1 Consolidator", layout="wide")
st.title("GSTR-1 Month-wise Consolidation")

# Order of months as per Example Sheet
MONTH_ORDER = ["2024-04-01", "2024-05-01", "2024-06-01", "2024-07-01", "2024-08-01", "2024-09-01", 
               "2024-10-01", "2024-11-01", "2024-12-01", "2025-01-01", "2025-02-01", "2025-03-01"]

TABLES = [
    ("B2B Invoices - 4A, 4B, 4C, 6B, 6C", "b2b"),
    ("B2C Invoices - 5A, 5B (Large)", "b2cl"),
    ("B2C Invoices - 7 (Others)", "b2cs"),
    ("Exports Invoices - 6A", "exp"),
    ("Nil rated, exempted and non GST outward supplies - 8", "nil"),
    ("Credit/Debit Notes (Registered) - 9B", "cdnr"),
    ("Credit/Debit Notes (Unregistered) - 9B", "cdnur"),
    ("Tax Liability (Advances Received) - 11A", "at"),
    ("Adjustment of Advances - 11B", "txpd")
]

def get_month_key(fp):
    """Converts portal 'fp' (MMYYYY) to the date format in Example Sheet."""
    if not fp or len(fp) != 6: return None
    return f"{fp[2:]}-{fp[:2]}-01"

# summary_data[table_key][tax_type][month_key]
summary_data = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))

uploaded_files = st.file_uploader("Upload Monthly GSTR-1 JSON files", type="json", accept_multiple_files=True)

if uploaded_files:
    for file in uploaded_files:
        try:
            data = json.load(file)
            month_key = get_month_key(data.get("fp", ""))
            if month_key not in MONTH_ORDER: continue

            for label, key in TABLES:
                section_data = data.get(key, [])
                
                for entry in section_data:
                    # Identify the list of documents based on section type
                    docs = []
                    if key in ['b2b', 'b2cl']:
                        docs = entry.get('inv', [])
                    elif key in ['cdnr', 'cdnur']:
                        docs = entry.get('nt', [])
                    else:
                        docs = [entry] # Direct items like B2CS

                    for doc in docs:
                        items = doc.get('itms', [])
                        for item in items:
                            # Tax details are usually in 'itm_det'
                            det = item.get('itm_det', item)
                            summary_data[key]["Taxable Value"][month_key] += det.get("txval", 0)
                            summary_data[key]["IGST"][month_key] += det.get("iamt", 0)
                            summary_data[key]["CGST"][month_key] += det.get("camt", 0)
                            summary_data[key]["SGST"][month_key] += det.get("samt", 0)
                            summary_data[key]["Cess"][month_key] += det.get("csamt", 0)
        except Exception as e:
            st.error(f"Error processing {file.name}: {e}")

    if st.button("Generate Consolidated Excel"):
        rows = []
        for tbl_name, key in TABLES:
            rows.append({"Particulars": f"GSTR-1 Summary calculated by Govt. Portal: {tbl_name}"})
            for tax_type in ["Taxable Value", "IGST", "CGST", "SGST", "Cess"]:
                row = {"Particulars": tax_type}
                total = 0
                for m in MONTH_ORDER:
                    val = summary_data[key][tax_type][m]
                    row[m] = round(val, 2)
                    total += val
                row["Total"] = round(total, 2)
                rows.append(row)
            rows.append({"Particulars": ""}) # Spacer

        df = pd.DataFrame(rows)
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="GSTR-1 Summary")
        
        st.success("Consolidated GSTR-1 Summary Generated")
        st.download_button("Download Excel", data=output.getvalue(), 
                           file_name="GSTR1_Consolidated.xlsx", 
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")







