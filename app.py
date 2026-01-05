import streamlit as st
import json
import pandas as pd
from collections import defaultdict
from io import BytesIO

st.set_page_config(page_title="GSTR-1 Consolidator", layout="wide")
st.title("GSTR-1 Month-wise Consolidation")

# Headers as requested: Month names
MONTH_LABELS = ["Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar"]
# Mapping portal 'fp' to our month labels
FP_MAP = {
    "04": "Apr", "05": "May", "06": "Jun", "07": "Jul", "08": "Aug", "09": "Sep",
    "10": "Oct", "11": "Nov", "12": "Dec", "01": "Jan", "02": "Feb", "03": "Mar"
}

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

summary_data = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))

uploaded_files = st.file_uploader("Upload Monthly GSTR-1 JSON files", type="json", accept_multiple_files=True)

if uploaded_files:
    for file in uploaded_files:
        try:
            data = json.load(file)
            fp = data.get("fp", "")
            if not fp: continue
            m_label = FP_MAP.get(fp[:2])
            if not m_label: continue

            for _, key in TABLES:
                section = data.get(key)
                if not section: continue

                # SPECIAL HANDLING FOR TABLE 8 (NIL/EXEMPT)
                if key == "nil":
                    inv_list = section.get("inv", [])
                    for item in inv_list:
                        # Summing nil, exempt, and non-gst supplies into "Value"
                        val = item.get("nil_amt", 0) + item.get("expt_amt", 0) + item.get("ngsup_amt", 0)
                        summary_data[key]["Value"][m_label] += val

                # SPECIAL HANDLING FOR TABLE 11A & 11B (ADVANCES)
                elif key in ["at", "txpd"]:
                    for entry in section:
                        for itm in entry.get("itms", []):
                            summary_data[key]["Taxable Value"][m_label] += itm.get("ad_amt", 0)
                            summary_data[key]["IGST"][m_label] += itm.get("iamt", 0)
                            summary_data[key]["CGST"][m_label] += itm.get("camt", 0)
                            summary_data[key]["SGST"][m_label] += itm.get("samt", 0)
                            summary_data[key]["Cess"][m_label] += itm.get("csamt", 0)

                # STANDARD HANDLING FOR INVOICE BASED SECTIONS (B2B, B2CS, CDN, etc.)
                else:
                    for entry in section:
                        docs = entry.get('inv', []) if 'inv' in entry else (entry.get('nt', []) if 'nt' in entry else [entry])
                        for doc in docs:
                            for item in doc.get('itms', []):
                                det = item.get('itm_det', item)
                                summary_data[key]["Taxable Value"][m_label] += det.get("txval", 0)
                                summary_data[key]["IGST"][m_label] += det.get("iamt", 0)
                                summary_data[key]["CGST"][m_label] += det.get("camt", 0)
                                summary_data[key]["SGST"][m_label] += det.get("samt", 0)
                                summary_data[key]["Cess"][m_label] += det.get("csamt", 0)

        except Exception as e:
            st.error(f"Error in {file.name}: {str(e)}")

    if st.button("Generate Consolidated Excel"):
        final_rows = []
        for tbl_name, key in TABLES:
            final_rows.append({"Particulars": f"GSTR-1 Summary calculated by Govt. Portal: {tbl_name}"})
            
            # Use "Value" for Table 8, otherwise standard taxes
            tax_list = ["Value"] if key == "nil" else ["Taxable Value", "IGST", "CGST", "SGST", "Cess"]
            
            for tax in tax_list:
                row = {"Particulars": tax}
                total_year = 0
                for m in MONTH_LABELS:
                    val = summary_data[key][tax][m]
                    row[m] = round(val, 2)
                    total_year += val
                row["Total"] = round(total_year, 2)
                final_rows.append(row)
            
            final_rows.append({"Particulars": ""}) # Blank spacer row

        df = pd.DataFrame(final_rows)
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="GSTR-1 Summary")
        
        st.success("Consolidation Successful!")
        st.download_button("Download Consolidated Excel", output.getvalue(), "GSTR1_Summary.xlsx")







