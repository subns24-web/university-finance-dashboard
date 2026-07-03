import streamlit as st
import plotly.express as px
import pandas as pd
import sys, os
import io

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils.data_loader import load_all_data, fmt_inr

st.set_page_config(page_title="Outstanding Fees", page_icon="⚠️", layout="wide")

st.title("⚠️ Outstanding Fees")
st.markdown("---")

data = load_all_data()
out = data["outstanding"].copy()

# ── Filters ────────────────────────────────────────────────────────────────
st.sidebar.header("Filters")

courses = ["All"] + sorted(out["Course"].dropna().unique().tolist())
sel_course = st.sidebar.selectbox("Course", courses)

overdue_cats = ["All", "<30 days", "30-60 days", "60-90 days", ">90 days"]
sel_overdue = st.sidebar.selectbox("Overdue Category", overdue_cats)

if sel_course != "All":
    out = out[out["Course"] == sel_course]
if sel_overdue != "All":
    out = out[out["Overdue_Category"] == sel_overdue]

# ── KPIs ───────────────────────────────────────────────────────────────────
k1, k2, k3 = st.columns(3)
k1.metric("Total Outstanding", fmt_inr(out["Balance_Due"].sum()))
k2.metric("Number of Students", f"{len(out):,}")
avg_days = out["Days_Overdue"].mean() if len(out) > 0 else 0
k3.metric("Avg Overdue Days", f"{avg_days:.0f} days")

st.markdown("---")

# ── Chart ──────────────────────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.subheader("Outstanding by Course")
    by_course = out.groupby("Course")["Balance_Due"].sum().reset_index().sort_values("Balance_Due", ascending=True)
    fig1 = px.bar(by_course, x="Balance_Due", y="Course", orientation="h",
                  color="Balance_Due", color_continuous_scale="Reds",
                  labels={"Balance_Due": "Balance Due (₹)", "Course": ""},
                  template="plotly_dark")
    fig1.update_layout(coloraxis_showscale=False, height=350,
                       plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    fig1.update_traces(hovertemplate="<b>%{y}</b><br>₹%{x:,.0f}<extra></extra>")
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    st.subheader("Distribution by Overdue Category")
    cat_order = ["Current", "<30 days", "30-60 days", "60-90 days", ">90 days"]
    by_cat = out.groupby("Overdue_Category")["Balance_Due"].sum().reset_index()
    by_cat["Overdue_Category"] = pd.Categorical(by_cat["Overdue_Category"], categories=cat_order, ordered=True)
    by_cat = by_cat.sort_values("Overdue_Category")
    fig2 = px.bar(by_cat, x="Overdue_Category", y="Balance_Due",
                  color="Overdue_Category",
                  color_discrete_map={
                      "Current": "#27ae60",
                      "<30 days": "#f1c40f",
                      "30-60 days": "#e67e22",
                      "60-90 days": "#e74c3c",
                      ">90 days": "#922b21"
                  },
                  labels={"Overdue_Category": "Category", "Balance_Due": "Balance Due (₹)"},
                  template="plotly_dark")
    fig2.update_layout(showlegend=False, height=350,
                       plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    fig2.update_traces(hovertemplate="<b>%{x}</b><br>₹%{y:,.0f}<extra></extra>")
    st.plotly_chart(fig2, use_container_width=True)

# ── Color-coded Table ──────────────────────────────────────────────────────
st.subheader("Outstanding Fee Details")

display_df = out.copy()
display_df["Days_Overdue"] = display_df["Days_Overdue"].astype(int)
display_df["Balance_Due_Fmt"] = display_df["Balance_Due"].apply(fmt_inr)
display_df["Total_Fee_Due_Fmt"] = display_df["Total_Fee_Due"].apply(fmt_inr)
display_df["Amount_Paid_Fmt"] = display_df["Amount_Paid"].apply(fmt_inr)
display_df["Due_Date"] = display_df["Due_Date"].dt.strftime("%d-%b-%Y")
display_df["Last_Payment_Date"] = display_df["Last_Payment_Date"].dt.strftime("%d-%b-%Y")

def color_rows(row):
    days = row.get("Days Overdue", row.get("Days_Overdue", 0))
    if days > 90:
        color = "background-color: #4a1010; color: #ff6b6b"
    elif days > 60:
        color = "background-color: #4a2c10; color: #ffa94d"
    elif days > 30:
        color = "background-color: #4a3d10; color: #ffe066"
    else:
        color = ""
    return [color] * len(row)

show_cols = ["Student_Name", "Course", "Branch", "Semester",
             "Total_Fee_Due_Fmt", "Amount_Paid_Fmt", "Balance_Due_Fmt",
             "Due_Date", "Days_Overdue", "Overdue_Category", "Last_Payment_Date", "Remarks"]
styled = display_df[show_cols].rename(columns={
    "Student_Name": "Student",
    "Total_Fee_Due_Fmt": "Total Due",
    "Amount_Paid_Fmt": "Paid",
    "Balance_Due_Fmt": "Balance",
    "Due_Date": "Due Date",
    "Days_Overdue": "Days Overdue",
    "Overdue_Category": "Category",
    "Last_Payment_Date": "Last Payment",
}).style.apply(color_rows, axis=1)

st.dataframe(styled, use_container_width=True, hide_index=True)

# ── Download ───────────────────────────────────────────────────────────────
csv_data = out[["Student_ID", "Student_Name", "Course", "Branch", "Semester",
                "Total_Fee_Due", "Amount_Paid", "Balance_Due",
                "Due_Date", "Days_Overdue", "Overdue_Category"]].to_csv(index=False)
st.download_button(
    label="📥 Download Outstanding Report (CSV)",
    data=csv_data,
    file_name="outstanding_fees_report.csv",
    mime="text/csv",
)
