import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from utils.data_loader import fmt_inr

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database", "university_finance.db")

st.set_page_config(page_title="Budgeting", page_icon="📋", layout="wide")
st.markdown("""
<style>
.metric-card{background:linear-gradient(135deg,#1e3a5f,#2d6a9f);border-radius:12px;padding:20px;color:white;text-align:center;box-shadow:0 4px 12px rgba(0,0,0,.15)}
.metric-value{font-size:1.8rem;font-weight:700;margin:8px 0}
.metric-label{font-size:.85rem;opacity:.85;text-transform:uppercase;letter-spacing:1px}
.metric-card.green{background:linear-gradient(135deg,#1a6b3a,#27a85f)}
.metric-card.orange{background:linear-gradient(135deg,#7a3a00,#d4700a)}
.metric-card.red{background:linear-gradient(135deg,#6b1a1a,#c0392b)}
.metric-card.purple{background:linear-gradient(135deg,#3a1a6b,#7d3ac1)}
</style>
""", unsafe_allow_html=True)

st.title("📋 Budget vs Actual")
st.markdown("**Financial Year 2025–26**")
st.markdown("---")

@st.cache_data
def load_budget():
    conn = sqlite3.connect(DB_PATH)
    rev = pd.read_sql("SELECT * FROM budget_revenue WHERE financial_year='2025-26'", conn)
    cap = pd.read_sql("SELECT * FROM budget_capital WHERE financial_year='2025-26'", conn)
    conn.close()
    return rev, cap

rev, cap = load_budget()

tab1, tab2, tab3 = st.tabs(["📊 Revenue Budget", "🏗️ Capital Budget", "📈 Quarterly Trend"])

with tab1:
    total_budget = rev["budget_amount"].sum()
    total_actual = rev["total_actual"].sum()
    total_var = total_budget - total_actual
    util_pct = (total_actual / total_budget * 100) if total_budget > 0 else 0

    c1,c2,c3,c4 = st.columns(4)
    with c1: st.markdown(f'<div class="metric-card purple"><div class="metric-label">Total Budget</div><div class="metric-value">{fmt_inr(total_budget)}</div></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="metric-card green"><div class="metric-label">Total Actual</div><div class="metric-value">{fmt_inr(total_actual)}</div></div>', unsafe_allow_html=True)
    with c3:
        color = "red" if total_var < 0 else "orange"
        st.markdown(f'<div class="metric-card {color}"><div class="metric-label">Variance</div><div class="metric-value">{fmt_inr(abs(total_var))}</div></div>', unsafe_allow_html=True)
    with c4:
        color = "green" if util_pct <= 100 else "red"
        st.markdown(f'<div class="metric-card {color}"><div class="metric-label">Utilization %</div><div class="metric-value">{util_pct:.1f}%</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    fig = go.Figure()
    fig.add_trace(go.Bar(name="Budget", x=rev["budget_head"], y=rev["budget_amount"], marker_color="#4fc3f7"))
    fig.add_trace(go.Bar(name="Actual", x=rev["budget_head"], y=rev["total_actual"], marker_color="#27a85f"))
    fig.update_layout(barmode="group", template="plotly_dark", title="Revenue Budget vs Actual",
                      plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                      xaxis_tickangle=-30, height=400)
    st.plotly_chart(fig, use_container_width=True)

    tbl = rev[["budget_head","budget_amount","total_actual","variance","variance_pct"]].copy()
    tbl["util_pct"] = (tbl["total_actual"] / tbl["budget_amount"] * 100).round(1)
    tbl["budget_amount"] = tbl["budget_amount"].apply(fmt_inr)
    tbl["total_actual"] = tbl["total_actual"].apply(fmt_inr)
    tbl["variance"] = tbl["variance"].apply(lambda x: fmt_inr(abs(x)))
    tbl["util_pct"] = tbl["util_pct"].astype(str) + "%"
    tbl.columns = ["Budget Head","Budget Amount","Actual","Variance","Var %","Utilization %"]
    st.dataframe(tbl, use_container_width=True, hide_index=True)

with tab2:
    total_cap_budget = cap["budget_amount"].sum()
    total_spent = cap["amount_spent"].sum()
    total_committed = cap["amount_committed"].sum()
    balance = cap["balance"].sum()

    c1,c2,c3,c4 = st.columns(4)
    with c1: st.markdown(f'<div class="metric-card purple"><div class="metric-label">Capital Budget</div><div class="metric-value">{fmt_inr(total_cap_budget)}</div></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="metric-card green"><div class="metric-label">Amount Spent</div><div class="metric-value">{fmt_inr(total_spent)}</div></div>', unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="metric-card orange"><div class="metric-label">Committed</div><div class="metric-value">{fmt_inr(total_committed)}</div></div>', unsafe_allow_html=True)
    with c4: st.markdown(f'<div class="metric-card"><div class="metric-label">Available Balance</div><div class="metric-value">{fmt_inr(balance)}</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col_l, col_r = st.columns([1,2])
    with col_l:
        pie_data = pd.DataFrame({
            "Category": ["Spent", "Committed", "Balance"],
            "Amount": [total_spent, total_committed, max(balance,0)]
        })
        fig2 = px.pie(pie_data, names="Category", values="Amount", hole=0.45,
                      color_discrete_map={"Spent":"#27a85f","Committed":"#d4700a","Balance":"#4fc3f7"},
                      template="plotly_dark", title="Capital Budget Utilization")
        fig2.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig2, use_container_width=True)

    with col_r:
        STATUS_COLORS = {"Completed":"🟢","In Progress":"🟡","Planned":"🔵","On Hold":"🔴"}
        tbl2 = cap[["asset_category","description","budget_amount","amount_spent","amount_committed","balance","status"]].copy()
        tbl2["progress"] = (tbl2["amount_spent"] / tbl2["budget_amount"] * 100).clip(0,100).round(1).astype(str) + "%"
        tbl2["status"] = tbl2["status"].apply(lambda x: f"{STATUS_COLORS.get(x,'⚪')} {x}")
        tbl2["budget_amount"] = tbl2["budget_amount"].apply(fmt_inr)
        tbl2["amount_spent"] = tbl2["amount_spent"].apply(fmt_inr)
        tbl2["amount_committed"] = tbl2["amount_committed"].apply(fmt_inr)
        tbl2["balance"] = tbl2["balance"].apply(fmt_inr)
        tbl2.columns = ["Category","Description","Budget","Spent","Committed","Balance","Status","Progress"]
        st.dataframe(tbl2, use_container_width=True, hide_index=True)

with tab3:
    quarters = ["Q1 (Apr-Jun)","Q2 (Jul-Sep)","Q3 (Oct-Dec)","Q4 (Jan-Mar)"]
    q_actuals = [rev["q1_actual"].sum(), rev["q2_actual"].sum(), rev["q3_actual"].sum(), rev["q4_actual"].sum()]
    q_budget = [total_budget/4]*4

    fig3 = go.Figure()
    fig3.add_trace(go.Bar(name="Quarterly Budget", x=quarters, y=q_budget, marker_color="#4fc3f7", opacity=0.7))
    fig3.add_trace(go.Bar(name="Quarterly Actual", x=quarters, y=q_actuals, marker_color="#27a85f"))
    fig3.update_layout(barmode="group", template="plotly_dark", title="Quarterly Budget vs Actual",
                       plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig3, use_container_width=True)

    cum_budget = [q_budget[0], q_budget[0]+q_budget[1], sum(q_budget[:3]), sum(q_budget)]
    cum_actual = [q_actuals[0], q_actuals[0]+q_actuals[1], sum(q_actuals[:3]), sum(q_actuals)]
    fig4 = go.Figure()
    fig4.add_trace(go.Scatter(x=quarters, y=cum_budget, name="Cumulative Budget", line=dict(color="#4fc3f7", dash="dash"), mode="lines+markers"))
    fig4.add_trace(go.Scatter(x=quarters, y=cum_actual, name="Cumulative Actual", line=dict(color="#27a85f"), mode="lines+markers"))
    fig4.update_layout(template="plotly_dark", title="Cumulative Budget vs Actual",
                       plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig4, use_container_width=True)
