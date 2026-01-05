import streamlit as st
import json
import pandas as pd
from collections import defaultdict
from io import BytesIO

st.set_page_config(page_title="GSTR-1 Consolidator", layout="wide")
st.title("GSTR-1 Month-wise Consolidation")

# Exactly matching the date columns in your Example Sheet
MONTH_ORDER = [
    "2024-04-01", "2024-05-01", "2024-06-01", "2024-07-01", "2024-08-01", "2024-09-01", 
    "2024-10-01", "2024-11-01", "2024-12-01", "2025-01-01", "2025-02-01", "2025-03-01"
]

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
    """Converts '082024' to '2024-08-01'"""
    if not fp or len(fp) != 6: return None
    return f"{fp[2:]}-{fp[:2]}-01"

# summary_data[table_key][tax_type][month_key]
summary_data = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))

uploaded_files = st.file_uploader("Upload Monthly GSTR-1 JSON files", type="json", accept_multiple_files=True)

if uploaded_files:
    for file in uploaded_files:
        try:
            data = json.load(file)
            m_key = get_month_key(data.get("fp", ""))
            
            if m_key not in MONTH_ORDER:
                continue

            for _, key in TABLES:
                section_data = data.get(key, [])
                
                for entry in section_data:
                    # Logic for B2B / B2CL / CDNR (Nested under ctin)
                    if isinstance(entry, dict) and ('inv' in entry or 'nt' in entry):
                        docs = entry.get('inv', []) or entry.get('nt', [])
                        for doc in docs:
                            for item in doc.get('itms', []):
                                det = item.get('itm_det', item)
                                summary_data[key]["Taxable Value"][m_key] += det.get("txval", 0)
                                summary_data[key]["IGST"][m_key] += det.get("iamt", 0)
                                summary_data[key]["CGST"][m_key] += det.get("camt", 0)
                                summary_data[key]["SGST"][m_key] += det.get("samt", 0)
                                summary_data[key]["Cess"][m_key] += det.get("csamt", 0)
                    
                    # Logic for B2CS / AT / TXPD (Flat list of items)
                    elif isinstance(entry, dict):
                        # Some sections like B2CS have a flat 'itms' list or direct fields
                        summary_data[key]["Taxable Value"][m_key] += entry.get("txval", 0)
                        summary_data[key]["IGST"][m_key] += entry.get("iamt", 0)
                        summary_data[key]["CGST"][m_key] += entry.get("camt", 0)
                        summary_data[key]["SGST"][m_key] += entry.get("samt", 0)
                        summary_data[key]["Cess"][m_key] += entry.get("csamt", 0)

        except Exception as e:
            st.warning(f"Skipped {file.name} due to format error: {e}")

    if st.button("Generate Consolidated Excel"):
        final_rows = []
        for tbl_name, key in TABLES:
            # Header row like in Example Sheet
            final_rows.append({"Particulars": f"GSTR-1 Summary calculated by Govt. Portal: {tbl_name}"})
            
            for tax in ["Taxable Value", "IGST", "CGST", "SGST", "Cess"]:
                row = {"Particulars": tax}
                total_val = 0
                for m in MONTH_ORDER:
                    val = summary_data[key][tax][m]
                    row[m] = round(val, 2)
                    total_val += val
                row["Total"] = round(total_val, 2)
                final_rows.append(row)
            
            # Add an empty row for spacing
            final_rows.append({"Particulars": None})

        df = pd.DataFrame(final_rows)
        
        # Prepare file for download
        output = BytesIO()
        # openpyxl is used here - ensure it is in requirements.txt
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="GSTR-1 Summary")
        
        st.success("Summary Generated Successfully!")
        st.download_button(
            label="Download Excel File",
            data=output.getvalue(),
            file_name="GSTR1_Consolidated_Report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )







