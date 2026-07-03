import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.theme import ENTERPRISE_CSS, kpi_card, section_header, alert, cuap_header, CUAP_LOGO
import sqlite3
import pandas as pd
import plotly.express as px
import streamlit as st
from utils.data_loader import fmt_inr

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database", "university_finance.db")

st.set_page_config(page_title="Student Fee Ledger", page_icon="🎓", layout="wide")
st.markdown(ENTERPRISE_CSS, unsafe_allow_html=True)

st.title("🎓 Student Fee Ledger")

@st.cache_data
def load_fee_ledger():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM student_fee_ledger", conn)
    conn.close()
    df["due_date"] = pd.to_datetime(df["due_date"], errors="coerce")
    df["paid_date"] = pd.to_datetime(df["paid_date"], errors="coerce")
    return df

df = load_fee_ledger()

# Filters
col1, col2, col3, col4 = st.columns(4)
with col1:
    batch = st.selectbox("Batch Year", ["All"] + sorted(df["batch_year"].unique().tolist(), reverse=True))
with col2:
    course = st.selectbox("Course", ["All"] + sorted(df["course"].unique().tolist()))
with col3:
    fee_type = st.selectbox("Fee Type", ["All"] + sorted(df["fee_type"].unique().tolist()))
with col4:
    status = st.selectbox("Status", ["All", "Paid", "Partial", "Pending"])

fdf = df.copy()
if batch != "All":    fdf = fdf[fdf["batch_year"] == int(batch)]
if course != "All":   fdf = fdf[fdf["course"] == course]
if fee_type != "All": fdf = fdf[fdf["fee_type"] == fee_type]
if status != "All":   fdf = fdf[fdf["status"] == status]

# KPIs
total_students = fdf["student_id"].nunique()
total_due = fdf["amount_due"].sum()
total_paid = fdf["amount_paid"].sum()
total_pending = fdf["balance"].sum()
coll_pct = (total_paid / total_due * 100) if total_due > 0 else 0

c1,c2,c3,c4,c5 = st.columns(5)
with c1: st.markdown(f'<div class="metric-card"><div class="metric-label">Students</div><div class="metric-value">{total_students}</div></div>', unsafe_allow_html=True)
with c2: st.markdown(f'<div class="metric-card purple"><div class="metric-label">Total Due</div><div class="metric-value">{fmt_inr(total_due)}</div></div>', unsafe_allow_html=True)
with c3: st.markdown(f'<div class="metric-card green"><div class="metric-label">Collected</div><div class="metric-value">{fmt_inr(total_paid)}</div></div>', unsafe_allow_html=True)
with c4: st.markdown(f'<div class="metric-card red"><div class="metric-label">Pending</div><div class="metric-value">{fmt_inr(total_pending)}</div></div>', unsafe_allow_html=True)
with c5:
    color = "green" if coll_pct >= 80 else ("orange" if coll_pct >= 60 else "red")
    st.markdown(f'<div class="metric-card {color}"><div class="metric-label">Collection %</div><div class="metric-value">{coll_pct:.1f}%</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["📋 Fee Ledger", "👤 4-Year Student View", "📊 Batch Analysis", "⚠️ Defaulter Report"])

with tab1:
    show = fdf[["student_id","student_name","course","branch","batch_year","fee_type",
                "year_of_study","semester","amount_due","amount_paid","balance","status"]].copy()
    show["amount_due"] = show["amount_due"].apply(fmt_inr)
    show["amount_paid"] = show["amount_paid"].apply(fmt_inr)
    show["balance"] = show["balance"].apply(fmt_inr)
    show.columns = ["ID","Name","Course","Branch","Batch","Fee Type","Year","Sem","Due","Paid","Balance","Status"]

    def color_status(row):
        s = row["Status"]
        if s == "Paid":    return ["background-color:#1a3a1a"]*len(row)
        if s == "Partial": return ["background-color:#3a2a00"]*len(row)
        return ["background-color:#3a1010"]*len(row)

    st.dataframe(show.style.apply(color_status, axis=1), use_container_width=True, hide_index=True)

    csv = fdf.to_csv(index=False)
    st.download_button("📥 Download CSV", csv, "fee_ledger.csv", "text/csv")

with tab2:
    students = df[["student_id","student_name","course","branch","batch_year"]].drop_duplicates("student_id")
    student_opts = {r["student_id"]: f"{r['student_name']} ({r['student_id']}) — {r['course']} {r['batch_year']}" for _, r in students.iterrows()}
    sel = st.selectbox("Select Student", list(student_opts.keys()), format_func=lambda x: student_opts[x])

    sdf = df[df["student_id"] == sel].copy()
    st.markdown(f"### Fee Summary for {student_opts[sel]}")

    for yr in sorted(sdf["year_of_study"].unique()):
        ydf = sdf[sdf["year_of_study"] == yr]
        due = ydf["amount_due"].sum()
        paid = ydf["amount_paid"].sum()
        pct = paid / due if due > 0 else 0
        st.markdown(f"**Year {int(yr)}** — Due: {fmt_inr(due)} | Paid: {fmt_inr(paid)} | Balance: {fmt_inr(due-paid)}")
        st.progress(min(pct, 1.0))

        show_yr = ydf[["fee_type","semester","amount_due","amount_paid","balance","status","due_date","paid_date"]].copy()
        show_yr["amount_due"] = show_yr["amount_due"].apply(fmt_inr)
        show_yr["amount_paid"] = show_yr["amount_paid"].apply(fmt_inr)
        show_yr["balance"] = show_yr["balance"].apply(fmt_inr)
        show_yr.columns = ["Fee Type","Sem","Due","Paid","Balance","Status","Due Date","Paid Date"]
        st.dataframe(show_yr, use_container_width=True, hide_index=True)
        st.markdown("---")

with tab3:
    batch_grp = df.groupby(["batch_year","fee_type"]).agg(due=("amount_due","sum"), paid=("amount_paid","sum")).reset_index()
    fig = px.bar(batch_grp, x="batch_year", y="paid", color="fee_type", barmode="group",
                 labels={"batch_year":"Batch","paid":"Amount Collected (₹)","fee_type":"Fee Type"},
                 title="Fee Collection by Batch & Fee Type", template="plotly_dark")
    fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, use_container_width=True)

    summary = df.groupby("batch_year").agg(
        Students=("student_id","nunique"),
        Total_Due=("amount_due","sum"),
        Total_Paid=("amount_paid","sum"),
        Balance=("balance","sum")
    ).reset_index()
    summary["Collection %"] = (summary["Total_Paid"]/summary["Total_Due"]*100).round(1).astype(str) + "%"
    for c in ["Total_Due","Total_Paid","Balance"]:
        summary[c] = summary[c].apply(fmt_inr)
    st.dataframe(summary, use_container_width=True, hide_index=True)

with tab4:
    defaulters = df[df["status"].isin(["Pending","Partial"])].copy()
    defaulters = defaulters.sort_values("balance", ascending=False)
    d_show = defaulters[["student_id","student_name","course","branch","batch_year",
                          "fee_type","amount_due","amount_paid","balance","status","due_date"]].copy()
    d_show["amount_due"] = d_show["amount_due"].apply(fmt_inr)
    d_show["amount_paid"] = d_show["amount_paid"].apply(fmt_inr)
    d_show["balance"] = d_show["balance"].apply(fmt_inr)
    d_show.columns = ["ID","Name","Course","Branch","Batch","Fee Type","Due","Paid","Balance","Status","Due Date"]
    st.dataframe(d_show, use_container_width=True, hide_index=True)
    st.download_button("📥 Download Defaulter Report", defaulters.to_csv(index=False), "defaulters.csv", "text/csv")
