import streamlit as st
import json
import pandas as pd
from collections import defaultdict
from io import BytesIO

st.set_page_config(page_title="GSTR-1 Consolidator", layout="wide")
st.title("GSTR-1 Month-wise Consolidation")

# Financial Year Month Order as per Example Sheet
MONTH_ORDER = ["2024-04-01", "2024-05-01", "2024-06-01", "2024-07-01", "2024-08-01", "2024-09-01", 
               "2024-10-01", "2024-11-01", "2024-12-01", "2025-01-01", "2025-02-01", "2025-03-01"]

# Mapping display names to JSON keys
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
    month = fp[:2]
    year = fp[2:]
    return f"{year}-{month}-01"

# Nested dictionary to store totals: summary_data[table_key][tax_type][month_key]
summary_data = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))

uploaded_files = st.file_uploader("Upload Monthly GSTR-1 JSON files", type="json", accept_multiple_files=True)

if uploaded_files:
    for file in uploaded_files:
        data = json.load(file)
        month_key = get_month_key(data.get("fp", ""))
        
        if month_key not in MONTH_ORDER:
            continue

        for label, key in TABLES:
            sections = data.get(key, [])
            for entry in sections:
                # Different sections have different structures (inv, nt, or direct items)
                invoices = entry.get('inv', []) if 'inv' in entry else [entry]
                if key in ['b2cs', 'at', 'txpd']: invoices = [entry] # Direct items
                if key in ['cdnr', 'cdnur']: invoices = entry.get('nt', [])

                for inv in invoices:
                    items = inv.get('itms', [])
                    for item in items:
                        # Extract tax details from itm_det or direct item
                        det = item.get('itm_det', item)
                        summary_data[key]["Taxable Value"][month_key] += det.get("txval", 0)
                        summary_data[key]["IGST"][month_key] += det.get("iamt", 0)
                        summary_data[key]["CGST"][month_key] += det.get("camt", 0)
                        summary_data[key]["SGST"][month_key] += det.get("samt", 0)
                        summary_data[key]["Cess"][month_key] += det.get("csamt", 0)

    if st.button("Generate Consolidated Excel"):
        rows = []
        for tbl_name, key in TABLES:
            # Table Header Row
            rows.append({"Particulars": f"GSTR-1 Summary calculated by Govt. Portal:{tbl_name}"})
            
            for tax_type in ["Taxable Value", "IGST", "CGST", "SGST", "Cess"]:
                row = {"Particulars": tax_type}
                row_total = 0
                for m in MONTH_ORDER:
                    val = summary_data[key][tax_type][m]
                    row[m] = round(val, 2)
                    row_total += val
                row["Total"] = round(row_total, 2)
                rows.append(row)
            # Spacer row
            rows.append({"Particulars": ""})

        df = pd.DataFrame(rows)
        
        # Format Excel Output
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="GSTR-1 Summary")
        
        st.success("Consolidation Complete!")
        st.download_button(
            label="Download Excel",
            data=output.getvalue(),
            file_name="GSTR1_Consolidated_Summary.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )







