import streamlit as st
import plotly.express as px
import pandas as pd
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils.theme import ENTERPRISE_CSS, kpi_card, section_header, alert, cuap_header, CUAP_LOGO
from utils.data_loader import load_all_data, fmt_inr

st.set_page_config(page_title="Fee Collection", page_icon="💰", layout="wide")

st.markdown(ENTERPRISE_CSS, unsafe_allow_html=True)

st.title("💰 Fee Collection")
st.markdown("---")

data = load_all_data()
fc = data["fee_collection"].copy()

# ── Filters ────────────────────────────────────────────────────────────────
st.sidebar.header("Filters")

min_date = fc["Date"].min().date() if not fc["Date"].isnull().all() else None
max_date = fc["Date"].max().date() if not fc["Date"].isnull().all() else None

if min_date and max_date:
    date_range = st.sidebar.date_input(
        "Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )
    if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
        fc = fc[(fc["Date"].dt.date >= date_range[0]) & (fc["Date"].dt.date <= date_range[1])]

courses = ["All"] + sorted(fc["Course"].dropna().unique().tolist())
sel_course = st.sidebar.selectbox("Course", courses)
if sel_course != "All":
    fc = fc[fc["Course"] == sel_course]

modes = ["All"] + sorted(fc["Payment_Mode"].dropna().unique().tolist())
sel_mode = st.sidebar.selectbox("Payment Mode", modes)
if sel_mode != "All":
    fc = fc[fc["Payment_Mode"] == sel_mode]

# ── KPIs ───────────────────────────────────────────────────────────────────
k1, k2, k3 = st.columns(3)
k1.metric("Total Collected", fmt_inr(fc["Amount_Paid"].sum()))
k2.metric("Number of Receipts", f"{len(fc):,}")
avg = fc["Amount_Paid"].mean() if len(fc) > 0 else 0
k3.metric("Average Payment", fmt_inr(avg))

st.markdown("---")

# ── Charts ─────────────────────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.subheader("Collection by Month")
    monthly = fc.groupby("Month_Name")["Amount_Paid"].sum().reset_index().sort_values("Amount_Paid", ascending=False)
    # Sort chronologically
    fc_sorted = fc.copy()
    fc_sorted["MonthSort"] = fc_sorted["Date"].dt.to_period("M")
    month_order = fc_sorted.drop_duplicates("Month_Name").sort_values("MonthSort")["Month_Name"].tolist()
    monthly["Month_Name"] = pd.Categorical(monthly["Month_Name"], categories=month_order, ordered=True)
    monthly = monthly.sort_values("Month_Name")

    fig1 = px.bar(monthly, x="Month_Name", y="Amount_Paid",
                  labels={"Month_Name": "Month", "Amount_Paid": "Amount (₹)"},
                  color="Amount_Paid", color_continuous_scale="Teal",
                  template="plotly_dark")
    fig1.update_layout(coloraxis_showscale=False, height=350,
                       plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    fig1.update_traces(hovertemplate="<b>%{x}</b><br>₹%{y:,.0f}<extra></extra>")
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    st.subheader("Collection by Course")
    by_course = fc.groupby("Course")["Amount_Paid"].sum().reset_index().sort_values("Amount_Paid", ascending=True)
    fig2 = px.bar(by_course, x="Amount_Paid", y="Course", orientation="h",
                  labels={"Amount_Paid": "Amount (₹)", "Course": ""},
                  color="Amount_Paid", color_continuous_scale="Blues",
                  template="plotly_dark")
    fig2.update_layout(coloraxis_showscale=False, height=350,
                       plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    fig2.update_traces(hovertemplate="<b>%{y}</b><br>₹%{x:,.0f}<extra></extra>")
    st.plotly_chart(fig2, use_container_width=True)

# ── Detailed Table ─────────────────────────────────────────────────────────
st.subheader("Receipt Details")
search = st.text_input("Search student name or receipt number")
display_df = fc.copy()
if search:
    mask = (
        display_df["Student_Name"].str.contains(search, case=False, na=False) |
        display_df["Receipt_No"].astype(str).str.contains(search, case=False, na=False)
    )
    display_df = display_df[mask]

display_df["Date"] = display_df["Date"].dt.strftime("%d-%b-%Y")
display_df["Amount_Paid_Fmt"] = display_df["Amount_Paid"].apply(fmt_inr)
cols = ["Receipt_No", "Date", "Student_Name", "Course", "Branch", "Semester",
        "Academic_Year", "Fee_Type", "Amount_Paid_Fmt", "Payment_Mode", "Collected_By"]
st.dataframe(
    display_df[cols].rename(columns={"Amount_Paid_Fmt": "Amount Paid"}),
    use_container_width=True,
    hide_index=True,
)
