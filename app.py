import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import sys, os

sys.path.insert(0, os.path.dirname(__file__))
from utils.data_loader import load_all_data, get_kpis, get_monthly_collection_trend, fmt_inr

st.set_page_config(
    page_title="CUAP Finance & Accounts",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
.metric-card {
    background: linear-gradient(135deg, #1e3a5f 0%, #2d6a9f 100%);
    border-radius: 12px;
    padding: 20px;
    color: white;
    text-align: center;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}
.metric-value { font-size: 1.8rem; font-weight: 700; margin: 8px 0; }
.metric-label { font-size: 0.85rem; opacity: 0.85; text-transform: uppercase; letter-spacing: 1px; }
.metric-card.green { background: linear-gradient(135deg, #1a6b3a 0%, #27a85f 100%); }
.metric-card.orange { background: linear-gradient(135deg, #7a3a00 0%, #d4700a 100%); }
.metric-card.red { background: linear-gradient(135deg, #6b1a1a 0%, #c0392b 100%); }
.metric-card.purple { background: linear-gradient(135deg, #3a1a6b 0%, #7d3ac1 100%); }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ────────────────────────────────────────────────────────────────
CUAP_LOGO = "https://cuap.ac.in/wp-content/uploads/2025/05/cu_logo_mod.png"
CUAP_NAME = "Central University of Andhra Pradesh"
CUAP_SHORT = "CUAP"
CUAP_ADDR = "'Jnana Seema', Ananthapuramu, AP – 515701"

with st.sidebar:
    st.image(CUAP_LOGO, width=80)
    st.markdown(f"### {CUAP_NAME}")
    st.markdown(f"<small style='color:#aaa'>{CUAP_ADDR}</small>", unsafe_allow_html=True)
    st.markdown("---")

    # ── File Upload ──────────────────────────────────────────────────────
    st.markdown("### 📂 Import Tally Excel to Database")
    uploaded_file = st.file_uploader(
        "📂 Import Tally Excel to Database",
        type=["xlsx", "xls"],
        help="Upload the Excel file exported from Tally ERP. Required sheets: Student_Master, Fee_Collection, Outstanding_Fees, Fee_Structure, Balance_Sheet, Income_Expenditure, Ledger_Summary"
    )

    if uploaded_file:
        import tempfile
        import sqlite3
        import json
        from database.db_init import seed_from_excel, DEFAULT_DB_PATH
        # Save uploaded file to a temp path for seeding
        if "uploaded_file_name" not in st.session_state or st.session_state.uploaded_file_name != uploaded_file.name:
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
            tmp.write(uploaded_file.read())
            tmp.close()
            with st.spinner("Importing into database..."):
                counts = seed_from_excel(
                    excel_path=tmp.name,
                    db_path=DEFAULT_DB_PATH,
                    imported_by="web_upload",
                )
            st.session_state.uploaded_file_name = uploaded_file.name
            load_all_data.clear()
            st.success(
                f"✅ Imported: {counts.get('students', 0)} students, "
                f"{counts.get('fee_collection', 0)} fee records, "
                f"{counts.get('outstanding_fees', 0)} outstanding"
            )
        # Show last import info
        try:
            conn = sqlite3.connect(DEFAULT_DB_PATH)
            row = conn.execute(
                "SELECT filename, imported_at FROM tally_imports ORDER BY id DESC LIMIT 1"
            ).fetchone()
            conn.close()
            if row:
                st.caption(f"Last import: **{row[0]}** on {row[1]}")
        except Exception:
            pass
    else:
        st.caption("Data is loaded from the local SQLite database. Upload a new Tally export to refresh.")

    st.markdown("---")
    st.markdown("**Navigation**")
    st.markdown("- 💰 Fee Collection\n- ⚠️ Outstanding Fees\n- 📊 Balance Sheet\n- 📈 Income & Expenditure\n- 🤖 AI Agent")
    st.markdown("---")
    st.markdown(f"**Data as of:** June 2026")
    st.markdown("**Academic Year:** 2025–26")
    st.markdown("---")
    st.markdown("<small>VC: Prof. S A Kori<br>cuap.ac.in</small>", unsafe_allow_html=True)

# ── Load data ──────────────────────────────────────────────────────────────
with st.spinner("Loading financial data..."):
    data = load_all_data()

kpis = get_kpis(data)

# ── Title ──────────────────────────────────────────────────────────────────
col_logo, col_title = st.columns([1, 8])
with col_logo:
    st.image(CUAP_LOGO, width=80)
with col_title:
    st.title("Central University of Andhra Pradesh")
    st.markdown("#### Finance & Accounts Dashboard — Academic Year 2025–26")
st.markdown("**VC:** Prof. S A Kori &nbsp;|&nbsp; **Campus:** 'Jnana Seema', Ananthapuramu, AP – 515701 &nbsp;|&nbsp; **Est.:** 2018")
st.markdown("---")

# ── KPI Cards ─────────────────────────────────────────────────────────────
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Total Students Enrolled</div>
        <div class="metric-value">{kpis['total_students']:,}</div>
    </div>""", unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="metric-card green">
        <div class="metric-label">Total Fees Collected (AY 2025-26)</div>
        <div class="metric-value">{fmt_inr(kpis['total_collected'])}</div>
    </div>""", unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="metric-card red">
        <div class="metric-label">Total Outstanding Dues</div>
        <div class="metric-value">{fmt_inr(kpis['total_outstanding'])}</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

col4, col5, col6 = st.columns(3)
with col4:
    eff = kpis['collection_efficiency']
    color = "green" if eff >= 80 else ("orange" if eff >= 60 else "red")
    st.markdown(f"""
    <div class="metric-card {color}">
        <div class="metric-label">Collection Efficiency %</div>
        <div class="metric-value">{eff:.1f}%</div>
    </div>""", unsafe_allow_html=True)

with col5:
    st.markdown(f"""
    <div class="metric-card orange">
        <div class="metric-label">Number of Defaulters (&gt;30 days)</div>
        <div class="metric-value">{kpis['defaulters']}</div>
    </div>""", unsafe_allow_html=True)

with col6:
    st.markdown(f"""
    <div class="metric-card purple">
        <div class="metric-label">Monthly Collection (Current)</div>
        <div class="metric-value">{fmt_inr(kpis['monthly_collection'])}</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Charts Row ─────────────────────────────────────────────────────────────
col_left, col_right = st.columns([2, 1])

with col_left:
    st.subheader("📅 Monthly Fee Collection Trend (Last 12 Months)")
    monthly_trend = get_monthly_collection_trend(data["fee_collection"], months=12)
    fig_bar = px.bar(
        monthly_trend,
        x="Month_Label",
        y="Amount_Paid",
        labels={"Month_Label": "Month", "Amount_Paid": "Amount (₹)"},
        color="Amount_Paid",
        color_continuous_scale="Blues",
        template="plotly_dark",
    )
    fig_bar.update_layout(
        coloraxis_showscale=False,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font_color="white",
        height=350,
    )
    fig_bar.update_traces(
        hovertemplate="<b>%{x}</b><br>₹%{y:,.0f}<extra></extra>"
    )
    st.plotly_chart(fig_bar, use_container_width=True)

with col_right:
    st.subheader("💳 Payment Mode Distribution")
    pm = data["fee_collection"]["Payment_Mode"].value_counts().reset_index()
    pm.columns = ["Payment_Mode", "Count"]
    fig_pie = px.pie(
        pm,
        names="Payment_Mode",
        values="Count",
        hole=0.4,
        color_discrete_sequence=px.colors.sequential.Blues_r,
        template="plotly_dark",
    )
    fig_pie.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font_color="white",
        height=350,
        legend=dict(orientation="h", y=-0.1),
    )
    st.plotly_chart(fig_pie, use_container_width=True)

# ── Top Defaulters ─────────────────────────────────────────────────────────
st.subheader("🚨 Top 10 Defaulters")
outstanding = data["outstanding"]
top10 = outstanding.nlargest(10, "Balance_Due")[
    ["Student_Name", "Course", "Branch", "Semester", "Balance_Due", "Days_Overdue", "Overdue_Category"]
].copy()
top10["Balance_Due_Fmt"] = top10["Balance_Due"].apply(fmt_inr)
top10["Days_Overdue"] = top10["Days_Overdue"].astype(int)

def color_row(row):
    # Uses renamed column "Days Overdue"
    days = row.get("Days Overdue", 0)
    if days > 90:
        return ["background-color: #4a1010; color: #ff6b6b"] * len(row)
    elif days > 60:
        return ["background-color: #4a2c10; color: #ffa94d"] * len(row)
    elif days > 30:
        return ["background-color: #4a3d10; color: #ffe066"] * len(row)
    return [""] * len(row)

display_cols = ["Student_Name", "Course", "Branch", "Semester", "Balance_Due_Fmt", "Days_Overdue", "Overdue_Category"]
styled = top10[display_cols].rename(columns={
    "Student_Name": "Student",
    "Balance_Due_Fmt": "Balance Due",
    "Days_Overdue": "Days Overdue",
    "Overdue_Category": "Category"
}).style.apply(color_row, axis=1)

st.dataframe(styled, use_container_width=True, hide_index=True)
