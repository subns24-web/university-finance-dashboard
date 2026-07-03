import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import sqlite3
import sys, os
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))
from utils.data_loader import load_all_data, get_kpis, get_monthly_collection_trend, fmt_inr
from utils.theme import ENTERPRISE_CSS, kpi_card, section_header, alert, cuap_header, CUAP_LOGO, CUAP_FULL

st.set_page_config(
    page_title="CUAP Finance & Accounts",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(ENTERPRISE_CSS, unsafe_allow_html=True)

# ── Sidebar ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div style="text-align:center; padding: 12px 0 8px;">
      <img src="{CUAP_LOGO}" style="width:70px; height:70px; object-fit:contain;">
      <div style="font-size:0.85rem; font-weight:700; margin-top:6px; color:#ffffff;">Central University of</div>
      <div style="font-size:0.85rem; font-weight:700; color:#F4A41C;">Andhra Pradesh</div>
      <div style="font-size:0.7rem; color:#b8d4f0; margin-top:2px;">Finance & Accounts Portal</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('<hr style="border-color: rgba(255,255,255,0.2); margin:8px 0;">', unsafe_allow_html=True)

    # DB Status
    DB_PATH = os.path.join(os.path.dirname(__file__), "database", "university_finance.db")
    db_ok = os.path.exists(DB_PATH)
    db_size = f"{os.path.getsize(DB_PATH)/1024:.0f} KB" if db_ok else "N/A"
    st.markdown(f"""
    <div style="background:rgba(255,255,255,0.08); border-radius:8px; padding:10px 12px; margin-bottom:8px;">
      <div style="font-size:0.72rem; color:#b8d4f0; margin-bottom:4px;">DATABASE STATUS</div>
      <div><span class="live-dot"></span><span style="font-size:0.8rem;">On-Premise SQLite</span></div>
      <div style="font-size:0.72rem; color:#b8d4f0; margin-top:3px;">Size: {db_size} &nbsp;|&nbsp; {'🟢 Connected' if db_ok else '🔴 Error'}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div style="font-size:0.72rem; color:#b8d4f0; margin:8px 0 4px; text-transform:uppercase; letter-spacing:1px;">Import Data</div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Upload Tally Excel", type=["xlsx","xls"],
        help="Upload Tally ERP export. Sheets: Student_Master, Fee_Collection, Outstanding_Fees, Fee_Structure, Balance_Sheet, Income_Expenditure, Ledger_Summary")

    if uploaded_file:
        import tempfile
        from database.db_init import seed_from_excel, DEFAULT_DB_PATH
        if "uploaded_file_name" not in st.session_state or st.session_state.uploaded_file_name != uploaded_file.name:
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
            tmp.write(uploaded_file.read()); tmp.close()
            with st.spinner("Importing into database..."):
                counts = seed_from_excel(tmp.name, DEFAULT_DB_PATH, "web_upload")
            st.session_state.uploaded_file_name = uploaded_file.name
            load_all_data.clear()
            st.success(f"✅ {counts.get('students',0)} students · {counts.get('fee_collection',0)} records")
        try:
            conn = sqlite3.connect(DB_PATH)
            row = conn.execute("SELECT filename, imported_at FROM tally_imports ORDER BY id DESC LIMIT 1").fetchone()
            conn.close()
            if row: st.caption(f"Last: **{row[0]}**\n{row[1][:16]}")
        except: pass
    else:
        st.caption("Live data from on-premise SQLite database.")

    st.markdown('<hr style="border-color: rgba(255,255,255,0.2); margin:8px 0;">', unsafe_allow_html=True)
    st.markdown(f"""
    <div style="font-size:0.72rem; color:#b8d4f0;">
      <div>🎓 AY 2025–26</div>
      <div style="margin-top:4px;">🕐 {datetime.now().strftime('%d %b %Y, %H:%M')}</div>
      <div style="margin-top:4px;">🌐 <a href="https://cuap.ac.in" style="color:#F4A41C;">cuap.ac.in</a></div>
      <div style="margin-top:4px;">👤 VC: Prof. S A Kori</div>
    </div>
    """, unsafe_allow_html=True)

# ── Load data ──────────────────────────────────────────────────────────────
with st.spinner(""):
    data = load_all_data()
kpis = get_kpis(data)

# ── Header ─────────────────────────────────────────────────────────────────
st.markdown(cuap_header("Finance & Accounts Dashboard"), unsafe_allow_html=True)

# ── Smart Alerts ───────────────────────────────────────────────────────────
outstanding = data["outstanding"]
critical_dues = len(outstanding[outstanding["Days_Overdue"] > 90])
salary_pending = 0
try:
    conn = sqlite3.connect(DB_PATH)
    salary_pending = conn.execute("SELECT COUNT(*) FROM salary_structure WHERE slip_sent=0 AND month_year='Jun-2026'").fetchone()[0]
    conn.close()
except: pass

if critical_dues > 0 or salary_pending > 0:
    a1, a2 = st.columns(2)
    with a1:
        if critical_dues > 0:
            st.markdown(alert(f"<b>{critical_dues} students</b> have fees overdue by more than 90 days — immediate follow-up required.", "critical"), unsafe_allow_html=True)
    with a2:
        if salary_pending > 0:
            st.markdown(alert(f"<b>{salary_pending} salary slips</b> for June 2026 are pending — last working day: 30 Jun 2026.", "warning"), unsafe_allow_html=True)

# ── KPI Cards ──────────────────────────────────────────────────────────────
st.markdown(section_header("Key Financial Indicators", "AY 2025–26"), unsafe_allow_html=True)

c1,c2,c3,c4,c5,c6 = st.columns(6)
cards = [
    (c1, "Students Enrolled", str(kpis['total_students']), "As of June 2026", "", ""),
    (c2, "Fees Collected", fmt_inr(kpis['total_collected']), "Current AY", "green", ""),
    (c3, "Outstanding Dues", fmt_inr(kpis['total_outstanding']), f"{kpis['defaulters']} defaulters", "red", ""),
    (c4, "Collection Efficiency", f"{kpis['collection_efficiency']:.1f}%",
         "Good" if kpis['collection_efficiency']>=80 else "Needs attention",
         "green" if kpis['collection_efficiency']>=80 else "gold", ""),
    (c5, "Salary Slips Pending", str(salary_pending), "Jun-2026", "gold" if salary_pending>0 else "green", ""),
    (c6, "Monthly Collection", fmt_inr(kpis['monthly_collection']), "This month", "purple", ""),
]
for col, lbl, val, sub, color, icon in cards:
    col.markdown(kpi_card(lbl, val, sub, color, icon), unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Charts Row ─────────────────────────────────────────────────────────────
col_left, col_right = st.columns([3, 2])

with col_left:
    st.markdown(section_header("Monthly Fee Collection Trend"), unsafe_allow_html=True)
    monthly_trend = get_monthly_collection_trend(data["fee_collection"], months=12)
    fig_bar = px.bar(monthly_trend, x="Month_Label", y="Amount_Paid",
        labels={"Month_Label":"Month","Amount_Paid":"Amount (₹)"},
        color="Amount_Paid", color_continuous_scale=[[0,"#b8d4f0"],[1,"#003366"]],
        template="plotly_white")
    fig_bar.update_layout(
        coloraxis_showscale=False, plot_bgcolor="white", paper_bgcolor="white",
        font=dict(family="Arial", color="#003366"), height=300,
        margin=dict(l=0,r=0,t=10,b=0),
        xaxis=dict(gridcolor="#f0f0f0"), yaxis=dict(gridcolor="#f0f0f0"))
    fig_bar.update_traces(hovertemplate="<b>%{x}</b><br>₹%{y:,.0f}<extra></extra>",
        marker_line_width=0)
    st.plotly_chart(fig_bar, use_container_width=True)

with col_right:
    st.markdown(section_header("Payment Mode Split"), unsafe_allow_html=True)
    pm = data["fee_collection"]["Payment_Mode"].value_counts().reset_index()
    pm.columns = ["Payment_Mode","Count"]
    fig_pie = px.pie(pm, names="Payment_Mode", values="Count", hole=0.5,
        color_discrete_sequence=["#003366","#F4A41C","#1a7a4a","#c0392b"],
        template="plotly_white")
    fig_pie.update_layout(
        plot_bgcolor="white", paper_bgcolor="white",
        font=dict(family="Arial", color="#003366"), height=300,
        margin=dict(l=0,r=0,t=10,b=0),
        legend=dict(orientation="h", y=-0.15, font_size=11))
    fig_pie.update_traces(hovertemplate="<b>%{label}</b><br>Count: %{value}<br>%{percent}<extra></extra>")
    st.plotly_chart(fig_pie, use_container_width=True)

# ── Second Row ─────────────────────────────────────────────────────────────
col_a, col_b = st.columns([2, 3])

with col_a:
    st.markdown(section_header("Outstanding by Category"), unsafe_allow_html=True)
    overdue_grp = outstanding.groupby("Overdue_Category")["Balance_Due"].sum().reset_index()
    color_map = {"Current":"#1a7a4a","<30 days":"#F4A41C","30-60 days":"#d4700a","60-90 days":"#c0392b",">90 days":"#7f1d1d"}
    fig_ov = px.bar(overdue_grp, x="Balance_Due", y="Overdue_Category", orientation="h",
        color="Overdue_Category", color_discrete_map=color_map, template="plotly_white",
        labels={"Balance_Due":"Amount (₹)","Overdue_Category":"Category"})
    fig_ov.update_layout(showlegend=False, plot_bgcolor="white", paper_bgcolor="white",
        font=dict(family="Arial",color="#003366"), height=260,
        margin=dict(l=0,r=0,t=10,b=0))
    fig_ov.update_traces(hovertemplate="<b>%{y}</b><br>₹%{x:,.0f}<extra></extra>")
    st.plotly_chart(fig_ov, use_container_width=True)

with col_b:
    st.markdown(section_header("Top 10 Defaulters", f"{len(outstanding)} total"), unsafe_allow_html=True)
    top10 = outstanding.nlargest(10,"Balance_Due")[
        ["Student_Name","Course","Branch","Balance_Due","Days_Overdue","Overdue_Category"]].copy()
    top10["Balance_Due"] = top10["Balance_Due"].apply(fmt_inr)
    top10["Days_Overdue"] = top10["Days_Overdue"].astype(int)

    def _color(row):
        d = row.get("Days Overdue", row.get("Days_Overdue", 0))
        if d > 90:  return ["background-color:#fee2e2; color:#991b1b"]*len(row)
        if d > 60:  return ["background-color:#ffedd5; color:#9a3412"]*len(row)
        if d > 30:  return ["background-color:#fef9c3; color:#854d0e"]*len(row)
        return [""]*len(row)

    top10.columns = ["Student","Course","Branch","Balance Due","Days Overdue","Category"]
    st.dataframe(top10.style.apply(_color, axis=1), use_container_width=True, hide_index=True, height=270)

# ── Quick Summary Row ──────────────────────────────────────────────────────
st.markdown(section_header("Quick Snapshot"), unsafe_allow_html=True)
try:
    conn = sqlite3.connect(DB_PATH)
    emp_count = conn.execute("SELECT COUNT(*) FROM employees WHERE status='Active'").fetchone()[0]
    net_payroll = conn.execute("SELECT SUM(net_salary) FROM salary_structure WHERE month_year='Jun-2026'").fetchone()[0] or 0
    stu_ledger  = conn.execute("SELECT COUNT(DISTINCT student_id) FROM student_fee_ledger").fetchone()[0]
    cap_spent   = conn.execute("SELECT SUM(amount_spent) FROM budget_capital WHERE financial_year='2025-26'").fetchone()[0] or 0
    cap_budget  = conn.execute("SELECT SUM(budget_amount) FROM budget_capital WHERE financial_year='2025-26'").fetchone()[0] or 1
    conn.close()
except:
    emp_count = net_payroll = stu_ledger = cap_spent = cap_budget = 0

qs_cols = st.columns(4)
snaps = [
    ("Active Employees", emp_count, "On payroll", "💼"),
    ("Jun-26 Net Payroll", fmt_inr(net_payroll), "Processed", "💰"),
    ("Students in Ledger", stu_ledger, "Across 4 batches", "🎓"),
    ("Capital Budget Used", f"{cap_spent/cap_budget*100:.0f}%" if cap_budget else "N/A", "of ₹ capital plan", "🏗️"),
]
for col,(lbl,val,sub,icon) in zip(qs_cols, snaps):
    col.markdown(f"""
    <div style="background:white; border-radius:10px; padding:16px; text-align:center;
                box-shadow:0 2px 8px rgba(0,0,0,0.07); border-top: 3px solid #003366;">
      <div style="font-size:1.6rem;">{icon}</div>
      <div style="font-size:1.4rem; font-weight:800; color:#003366; margin:4px 0;">{val}</div>
      <div style="font-size:0.75rem; color:#6b7280; text-transform:uppercase;">{lbl}</div>
      <div style="font-size:0.72rem; color:#9ca3af;">{sub}</div>
    </div>""", unsafe_allow_html=True)

# ── Footer ─────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="cuap-footer">
  🔒 On-Premise Secure Portal &nbsp;|&nbsp; {CUAP_FULL} &nbsp;|&nbsp; Finance & Accounts Division<br>
  Data stored locally on university servers. No data transmitted externally.<br>
  <span style="color:#F4A41C;">cuap.ac.in</span> &nbsp;|&nbsp; 'Jnana Seema', Ananthapuramu, AP – 515701
</div>
""", unsafe_allow_html=True)
