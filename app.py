df = pd.DataFrame(rows).fillna(0)

available_months = [m for m in MONTH_ORDER if m in df.columns]
df = df[["Particulars"] + available_months]

output = BytesIO()
with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
    df.to_excel(writer, index=False, sheet_name="GSTR-1 Consolidated")

st.download_button(
    "Download Consolidated Excel",
    output.getvalue(),
    "GSTR1_Consolidated.xlsx",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)









