import streamlit as st
import json
import pandas as pd
from collections import defaultdict
from io import BytesIO
from openpyxl.styles import Font, PatternFill

st.set_page_config(page_title="GSTR-1 Consolidator", layout="wide")
st.title("GSTR-1 Month-wise Consolidation")

# Month sequence for the final report
MONTH_LABELS = ["Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar"]
FP_MAP = {
    "04": "Apr", "05": "May", "06": "Jun", "07": "Jul", "08": "Aug", "09": "Sep",
    "10": "Oct", "11": "Nov", "12": "Dec", "01": "Jan", "02": "Feb", "03": "Mar"
}

# Table Definitions based on JSON keys
TABLES = [
    ("B2B Invoices - 4A, 4B, 4C, 6B, 6C", "b2b"),
    ("B2C Invoices - 5A, 5B (Large)", "b2cl"),
    ("B2C Invoices 7 - B2C (Others)", "b2cs"),
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
            fp = data.get("fp", "") # Fetch period
            if not fp: continue
            m_label = FP_MAP.get(fp[:2])
            if not m_label: continue

            for _, key in TABLES:
                section = data.get(key, [])
                if not section: continue

                # TABLE 8 Logic
                if key == "nil":
                    inv_list = section.get("inv", []) if isinstance(section, dict) else section
                    for item in inv_list:
                        summary_data[key]["Nil-rated Supply"][m_label] += item.get("nil_amt", 0)
                        summary_data[key]["Exempt Supply"][m_label] += item.get("expt_amt", 0)
                        summary_data[key]["Non-GST Supply"][m_label] += item.get("ngsup_amt", 0)

                # TABLE 7 (B2CS) Logic
                elif key == "b2cs":
                    for item in section:
                        summary_data[key]["Taxable Value"][m_label] += item.get("txval", 0)
                        summary_data[key]["IGST"][m_label] += item.get("iamt", 0)
                        summary_data[key]["CGST"][m_label] += item.get("camt", 0)
                        summary_data[key]["SGST"][m_label] += item.get("samt", 0)
                        summary_data[key]["Cess"][m_label] += item.get("csamt", 0)

                # TABLE 11 (Advances) Logic
                elif key in ["at", "txpd"]:
                    for entry in section:
                        for itm in entry.get("itms", []):
                            summary_data[key]["Taxable Value"][m_label] += itm.get("ad_amt", 0)
                            summary_data[key]["IGST"][m_label] += itm.get("iamt", 0)
                            summary_data[key]["CGST"][m_label] += itm.get("camt", 0)
                            summary_data[key]["SGST"][m_label] += itm.get("samt", 0)
                            summary_data[key]["Cess"][m_label] += itm.get("csamt", 0)

                # STANDARD Logic (B2B, CDNR)
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

    if st.button("Generate Formatted Excel"):
        final_rows = []
        header_indices = [] # To keep track of which rows are Table Names
        
        for tbl_name, key in TABLES:
            header_indices.append(len(final_rows) + 1) # +1 for Excel header
            final_rows.append({"Particulars": f"GSTR-1 Summary calculated by Govt. Portal: {tbl_name}"})
            
            tax_rows = ["Nil-rated Supply", "Exempt Supply", "Non-GST Supply"] if key == "nil" else ["Taxable Value", "IGST", "CGST", "SGST", "Cess"]
            
            for tax in tax_rows:
                row = {"Particulars": tax}
                total = 0
                for m in MONTH_LABELS:
                    val = summary_data[key][tax][m]
                    row[m] = round(val, 2)
                    total += val
                row["Total"] = round(total, 2)
                final_rows.append(row)
            
            final_rows.append({"Particulars": ""})

        df = pd.DataFrame(final_rows)
        output = BytesIO()
        
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="GSTR-1 Summary")
            workbook = writer.book
            worksheet = writer.sheets["GSTR-1 Summary"]
            
            # Styles
            cambria_11 = Font(name="Cambria", size=11)
            cambria_11_bold = Font(name="Cambria", size=11, bold=True)
            light_blue_fill = PatternFill(start_color="DDEBF7", end_color="DDEBF7", fill_type="solid")
            
            # Apply basic font to all cells
            for row in worksheet.iter_rows():
                for cell in row:
                    cell.font = cambria_11
            
            # Bold Month names (Header row)
            for cell in worksheet[1]:
                cell.font = cambria_11_bold
            
            # Format Table Name rows (Blue and Bold Particulars)
            for idx in header_indices:
                row_idx = idx + 1
                worksheet.cell(row=row_idx, column=1).font = cambria_11_bold
                for col in range(1, worksheet.max_column + 1):
                    worksheet.cell(row=row_idx, column=col).fill = light_blue_fill
            
            # Bold all "Particulars" column (Column A)
            for row in range(2, worksheet.max_column + 1):
                worksheet.cell(row=row, column=1).font = cambria_11_bold

        st.success("Consolidation Complete with Formatting!")
        st.download_button("Download Formatted Excel", output.getvalue(), "GSTR1_Consolidated_Formatted.xlsx")







