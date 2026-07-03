import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils.data_loader import load_all_data, fmt_inr

st.set_page_config(page_title="Income & Expenditure", page_icon="📈", layout="wide")

st.title("📈 Income & Expenditure")
st.markdown("**April 2025 – March 2026**")
st.markdown("---")

data = load_all_data()
ie_raw = data["income_exp_raw"]

# ── Parse the I&E sheet ────────────────────────────────────────────────────
# Row 1 has months in cols 1..12, col 13 = Annual Total
months = ["Apr-25","May-25","Jun-25","Jul-25","Aug-25","Sep-25",
          "Oct-25","Nov-25","Dec-25","Jan-26","Feb-26","Mar-26"]

INCOME_ROWS   = ["Tuition Fees","Hostel Fees","Transport Fees",
                 "Exam Fees","Development Fees","Other Income"]
EXPENSE_ROWS  = ["Teaching Staff Salary","Non-Teaching Salary",
                 "Electricity & Water","Building Maintenance",
                 "Lab & Library Expenses","Admin Expenses",
                 "Depreciation","Other Expenses"]

income_data = {}
expense_data = {}

month_cols = ["col_b","col_c","col_d","col_e","col_f","col_g",
              "col_h","col_i","col_j","col_k","col_l","col_m"]

for _, row in ie_raw.iterrows():
    head = str(row["col_a"]).strip() if pd.notna(row["col_a"]) else ""
    if head in INCOME_ROWS:
        income_data[head] = [float(row[c]) if pd.notna(row[c]) else 0 for c in month_cols]
    elif head in EXPENSE_ROWS:
        expense_data[head] = [float(row[c]) if pd.notna(row[c]) else 0 for c in month_cols]

# Build monthly totals dataframe
monthly_income  = [sum(income_data[k][i] for k in income_data) for i in range(12)]
monthly_expense = [sum(expense_data[k][i] for k in expense_data) for i in range(12)]
monthly_surplus = [monthly_income[i] - monthly_expense[i] for i in range(12)]

df_monthly = pd.DataFrame({
    "Month": months,
    "Income": monthly_income,
    "Expenditure": monthly_expense,
    "Surplus_Deficit": monthly_surplus,
})

# ── Annual KPIs ────────────────────────────────────────────────────────────
total_income   = sum(monthly_income)
total_expense  = sum(monthly_expense)
total_surplus  = total_income - total_expense
surplus_pct    = (total_surplus / total_income * 100) if total_income > 0 else 0

k1, k2, k3, k4 = st.columns(4)
k1.metric("Annual Income", fmt_inr(total_income))
k2.metric("Annual Expenditure", fmt_inr(total_expense))
surplus_label = "Annual Surplus" if total_surplus >= 0 else "Annual Deficit"
k3.metric(surplus_label, fmt_inr(abs(total_surplus)), delta=f"{surplus_pct:.1f}%")
k4.metric("Surplus Ratio", f"{surplus_pct:.1f}%")

st.markdown("---")

# ── Grouped bar: Income vs Expenditure by month ────────────────────────────
st.subheader("Monthly Income vs Expenditure")
fig1 = go.Figure()
fig1.add_trace(go.Bar(name="Income", x=months, y=monthly_income,
                      marker_color="#4fc3f7",
                      hovertemplate="<b>%{x}</b><br>Income: ₹%{y:,.0f}<extra></extra>"))
fig1.add_trace(go.Bar(name="Expenditure", x=months, y=monthly_expense,
                      marker_color="#ef9a9a",
                      hovertemplate="<b>%{x}</b><br>Expenditure: ₹%{y:,.0f}<extra></extra>"))
fig1.update_layout(
    barmode="group",
    template="plotly_dark",
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    height=380,
    legend=dict(orientation="h", y=1.1),
)
st.plotly_chart(fig1, use_container_width=True)

# ── Line chart: Surplus/Deficit trend ─────────────────────────────────────
st.subheader("Surplus / (Deficit) Trend")
colors = ["#4caf50" if s >= 0 else "#f44336" for s in monthly_surplus]
fig2 = go.Figure()
fig2.add_trace(go.Scatter(
    x=months, y=monthly_surplus,
    mode="lines+markers",
    line=dict(color="#ffd54f", width=3),
    marker=dict(size=8, color=colors),
    hovertemplate="<b>%{x}</b><br>Surplus: ₹%{y:,.0f}<extra></extra>",
    fill="tozeroy",
    fillcolor="rgba(255,213,79,0.15)",
))
fig2.add_hline(y=0, line_dash="dash", line_color="gray")
fig2.update_layout(
    template="plotly_dark",
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    height=300,
    yaxis_title="Surplus (₹)",
)
st.plotly_chart(fig2, use_container_width=True)

# ── Monthly breakdown table ────────────────────────────────────────────────
st.subheader("Monthly Breakdown")
display_df = df_monthly.copy()
for col in ["Income", "Expenditure", "Surplus_Deficit"]:
    display_df[col] = display_df[col].apply(fmt_inr)
display_df = display_df.rename(columns={"Surplus_Deficit": "Surplus / (Deficit)"})
st.dataframe(display_df, use_container_width=True, hide_index=True)

# ── Income breakdown chart ─────────────────────────────────────────────────
st.subheader("Annual Income Breakdown")
income_totals = {k: sum(v) for k, v in income_data.items()}
df_inc = pd.DataFrame(list(income_totals.items()), columns=["Head", "Amount"]).sort_values("Amount")
fig3 = px.bar(df_inc, x="Amount", y="Head", orientation="h",
              color="Amount", color_continuous_scale="Greens",
              labels={"Amount": "Amount (₹)", "Head": ""},
              template="plotly_dark")
fig3.update_layout(coloraxis_showscale=False, height=320,
                   plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
fig3.update_traces(hovertemplate="<b>%{y}</b><br>₹%{x:,.0f}<extra></extra>")

st.subheader("Annual Expenditure Breakdown")
expense_totals = {k: sum(v) for k, v in expense_data.items()}
df_exp = pd.DataFrame(list(expense_totals.items()), columns=["Head", "Amount"]).sort_values("Amount")
fig4 = px.bar(df_exp, x="Amount", y="Head", orientation="h",
              color="Amount", color_continuous_scale="Reds",
              labels={"Amount": "Amount (₹)", "Head": ""},
              template="plotly_dark")
fig4.update_layout(coloraxis_showscale=False, height=320,
                   plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
fig4.update_traces(hovertemplate="<b>%{y}</b><br>₹%{x:,.0f}<extra></extra>")

col1, col2 = st.columns(2)
with col1:
    st.plotly_chart(fig3, use_container_width=True)
with col2:
    st.plotly_chart(fig4, use_container_width=True)
