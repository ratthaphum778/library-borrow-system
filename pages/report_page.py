import streamlit as st
import model
from datetime import date
import pandas as pd
import plotly.express as px
import io


# =====================================================
# Utility Functions
# =====================================================

def safe_df(df):
    return df if isinstance(df, pd.DataFrame) else pd.DataFrame()


def find_col(df, keywords):
    for c in df.columns:
        for k in keywords:
            if k.lower() in c.lower():
                return c
    return None


def map_status_th(df):
    df = df.copy()
    for col in df.columns:
        if "status" in col.lower() or "สถานะ" in col:
            df[col] = df[col].map({
                "borrowed": "ยังไม่คืน",
                "returned": "คืนแล้ว"
            }).fillna(df[col])
    return df


def df_to_pdf_bytes(df):
    html = f"""
    <html>
    <head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial; }}
        table {{ border-collapse: collapse; width:100%; }}
        th,td {{
            border:1px solid black;
            padding:4px;
            font-size:10px;
            text-align:center;
        }}
        th {{ background:#eee; }}
    </style>
    </head>
    <body>
    <h3>Borrow Report</h3>
    {df.to_html(index=False)}
    </body>
    </html>
    """
    return html.encode("utf-8")


# =====================================================
# MAIN PAGE
# =====================================================

def render_report():

    st.subheader("📊 รายงานสรุประบบยืม-คืนหนังสือ")

    # =================================================
    # 1) Pie Chart : Book Status
    # =================================================
    status_df = safe_df(model.get_book_status_summary())

    if not status_df.empty:
        name_col = find_col(status_df, ["สถานะ"])
        value_col = find_col(status_df, ["จำนวน"])

        if name_col and value_col:
            fig = px.pie(
                status_df,
                names=name_col,
                values=value_col,
                hole=0.4,
                title="สัดส่วนสถานะหนังสือ"
            )
            st.plotly_chart(fig, use_container_width=True)

        st.dataframe(status_df, use_container_width=True)
    else:
        st.info("ไม่มีข้อมูลสถานะหนังสือ")

    st.divider()

    # =================================================
    # 2) Monthly Borrow Chart
    # =================================================
    col1, col2 = st.columns(2)

    with col1:
        start = st.date_input("เริ่ม", date(2025, 6, 1))

    with col2:
        end = st.date_input("สิ้นสุด", date.today())

    if start <= end:

        monthly_df = safe_df(
            model.get_borrow_summary_by_month(
                start.isoformat(),
                end.isoformat()
            )
        )

        if not monthly_df.empty:
            mcol = find_col(monthly_df, ["เดือน"])
            ccol = find_col(monthly_df, ["จำนวน"])

            if mcol and ccol:
                st.bar_chart(monthly_df.set_index(mcol)[ccol])

            st.dataframe(monthly_df, use_container_width=True)
        else:
            st.info("ไม่มีข้อมูลรายเดือน")

    st.divider()

    # =================================================
    # 3) Borrow Report Table
    # =================================================
    c1, c2, c3 = st.columns(3)

    with c1:
        rs = st.date_input("เริ่มรายงาน", date(2025, 6, 1))
    with c2:
        re = st.date_input("จบรายงาน", date.today())
    with c3:
        label = st.selectbox(
            "สถานะ",
            ["ทั้งหมด", "ยังไม่คืน", "คืนแล้ว"]
        )

    status_map = {
        "ทั้งหมด": "all",
        "ยังไม่คืน": "borrowed",
        "คืนแล้ว": "returned"
    }

    report_df = safe_df(
        model.get_borrow_report(
            rs.isoformat(),
            re.isoformat(),
            status_map[label]
        )
    )

    if report_df.empty:
        st.warning("ไม่พบข้อมูลรายงาน")
        return

    report_df = map_status_th(report_df)

    st.dataframe(report_df, use_container_width=True)

    # =================================================
    # 4) DOWNLOAD SECTION (CSV + XLSX + PDF)
    # =================================================
    st.markdown("## ⬇️ ดาวน์โหลดรายงาน")

    col1, col2, col3 = st.columns(3)

    # CSV
    with col1:
        csv_bytes = report_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ CSV",
            data=csv_bytes,
            file_name="report.csv",
            mime="text/csv"
        )

    # XLSX
    with col2:
        excel_buffer = io.BytesIO()
        report_df.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)

        st.download_button(
            "⬇️ XLSX",
            data=excel_buffer,
            file_name="report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    # PDF
    with col3:
        pdf_bytes = df_to_pdf_bytes(report_df)

        st.download_button(
            "⬇️ PDF",
            data=pdf_bytes,
            file_name="report.pdf",
            mime="application/pdf"
        )