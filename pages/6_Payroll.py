"""
pages/6_Payroll.py
Payroll Management — Salary Register, Salary Slips, Department Summary, Trend
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from database.db_init import DEFAULT_DB_PATH

# ── Page config ────────────────────────────────────────────────────────────
st.set_page_config(page_title="Payroll | University Finance", page_icon="💼", layout="wide")

# ── CSS ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.metric-card {
    background: linear-gradient(135deg, #1e3a5f 0%, #2d6a9f 100%);
    border-radius: 12px; padding: 20px; color: white;
    text-align: center; box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}
.metric-value { font-size: 1.8rem; font-weight: 700; margin: 8px 0; }
.metric-label { font-size: 0.85rem; opacity: 0.85; text-transform: uppercase; letter-spacing: 1px; }
.metric-card.green  { background: linear-gradient(135deg, #1a6b3a 0%, #27a85f 100%); }
.metric-card.orange { background: linear-gradient(135deg, #7a3a00 0%, #d4700a 100%); }
.metric-card.red    { background: linear-gradient(135deg, #6b1a1a 0%, #c0392b 100%); }
.metric-card.purple { background: linear-gradient(135deg, #3a1a6b 0%, #7d3ac1 100%); }
.slip-box {
    background: #0e1117; border: 1px solid #333;
    border-radius: 8px; padding: 20px; font-family: monospace;
    font-size: 0.85rem; line-height: 1.7;
}
</style>
""", unsafe_allow_html=True)

# ── Helpers ────────────────────────────────────────────────────────────────
def fmt_inr(v):
    try:
        v = float(v)
    except Exception:
        return "₹0"
    if v >= 1e7:
        return f"₹{v/1e7:.2f} Cr"
    elif v >= 1e5:
        return f"₹{v/1e5:.2f} L"
    return f"₹{v:,.0f}"

MONTHS = ["Jun-2026", "May-2026", "Apr-2026", "Mar-2026", "Feb-2026", "Jan-2026"]

@st.cache_data(ttl=60)
def load_payroll_data(month_year, db_path=DEFAULT_DB_PATH):
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("""
        SELECT e.emp_id, e.name, e.designation, e.department, e.employment_type, e.status,
               e.pan, e.bank_account, e.bank_name, e.ifsc, e.email, e.mobile,
               s.month_year, s.basic, s.hra, s.da, s.ta, s.medical_allowance, s.other_allowance,
               s.gross_salary, s.pf_deduction, s.pt, s.tds, s.other_deduction,
               s.total_deductions, s.net_salary, s.working_days, s.paid_days, s.lop_days,
               s.payment_date, s.payment_mode, s.utr_number, s.slip_sent
        FROM employees e
        LEFT JOIN salary_structure s ON e.emp_id = s.emp_id AND s.month_year = ?
        WHERE e.status = 'Active'
        ORDER BY e.emp_id
    """, conn, params=(month_year,))
    conn.close()
    return df

@st.cache_data(ttl=60)
def load_trend_data(db_path=DEFAULT_DB_PATH):
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("""
        SELECT month_year,
               SUM(gross_salary) as gross, SUM(total_deductions) as deductions, SUM(net_salary) as net
        FROM salary_structure
        GROUP BY month_year
        ORDER BY
            CASE SUBSTR(month_year,1,3)
                WHEN 'Jan' THEN 1 WHEN 'Feb' THEN 2 WHEN 'Mar' THEN 3
                WHEN 'Apr' THEN 4 WHEN 'May' THEN 5 WHEN 'Jun' THEN 6
                WHEN 'Jul' THEN 7 WHEN 'Aug' THEN 8 WHEN 'Sep' THEN 9
                WHEN 'Oct' THEN 10 WHEN 'Nov' THEN 11 WHEN 'Dec' THEN 12
            END
    """, conn)
    conn.close()
    return df

# ── Month selector ─────────────────────────────────────────────────────────
st.title("💼 Payroll Management")
st.markdown("---")

col_sel, _ = st.columns([2, 6])
with col_sel:
    selected_month = st.selectbox("📅 Select Month", MONTHS, index=0)

df = load_payroll_data(selected_month)
df_valid = df.dropna(subset=["gross_salary"])

# ── KPI Cards ──────────────────────────────────────────────────────────────
total_emp     = len(df)
gross_payroll = df_valid["gross_salary"].sum()
total_ded     = df_valid["total_deductions"].sum()
net_payroll   = df_valid["net_salary"].sum()
slips_sent    = int(df_valid["slip_sent"].sum()) if "slip_sent" in df_valid.columns else 0

c1, c2, c3, c4, c5 = st.columns(5)
cards = [
    (c1, "Total Employees", str(total_emp), ""),
    (c2, "Gross Payroll", fmt_inr(gross_payroll), "green"),
    (c3, "Total Deductions", fmt_inr(total_ded), "red"),
    (c4, "Net Payroll", fmt_inr(net_payroll), "purple"),
    (c5, "Slips Sent", f"{slips_sent}/{len(df_valid)}", "orange"),
]
for col, label, value, color in cards:
    cls = f"metric-card {color}".strip()
    col.markdown(f"""
    <div class="{cls}">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Tabs ───────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["📋 Salary Register", "🧾 Salary Slip", "🏢 Department Summary", "📈 Payroll Trend"])

# ══════════════════════════════════════════════════════════════════════════
# TAB 1 — Salary Register
# ══════════════════════════════════════════════════════════════════════════
with tab1:
    st.subheader(f"Salary Register — {selected_month}")

    fcol1, fcol2 = st.columns(2)
    with fcol1:
        depts = ["All"] + sorted(df["department"].dropna().unique().tolist())
        sel_dept = st.selectbox("Filter by Department", depts, key="reg_dept")
    with fcol2:
        etypes = ["All"] + sorted(df["employment_type"].dropna().unique().tolist())
        sel_etype = st.selectbox("Filter by Employment Type", etypes, key="reg_etype")

    fdf = df_valid.copy()
    if sel_dept != "All":
        fdf = fdf[fdf["department"] == sel_dept]
    if sel_etype != "All":
        fdf = fdf[fdf["employment_type"] == sel_etype]

    display = fdf[["emp_id","name","designation","department","employment_type","basic","gross_salary","net_salary","slip_sent"]].copy()
    display.columns = ["Emp ID","Name","Designation","Department","Type","Basic (₹)","Gross (₹)","Net Pay (₹)","Slip Sent"]
    display["Basic (₹)"] = display["Basic (₹)"].apply(lambda x: f"₹{x:,.0f}")
    display["Gross (₹)"] = display["Gross (₹)"].apply(lambda x: f"₹{x:,.0f}")
    display["Net Pay (₹)"] = display["Net Pay (₹)"].apply(lambda x: f"₹{x:,.0f}")
    display["Slip Sent"] = display["Slip Sent"].apply(lambda x: "✅ Sent" if x == 1 else "⏳ Pending")

    def color_slip(row):
        if row["Slip Sent"] == "✅ Sent":
            return ["background-color: #0d3320; color: #4ade80"] * len(row)
        return ["background-color: #3d2200; color: #fb923c"] * len(row)

    styled = display.style.apply(color_slip, axis=1)
    st.dataframe(styled, use_container_width=True, hide_index=True)
    st.caption(f"Showing {len(fdf)} employees")

# ══════════════════════════════════════════════════════════════════════════
# TAB 2 — Salary Slip
# ══════════════════════════════════════════════════════════════════════════
with tab2:
    st.subheader("Generate Salary Slip")

    emp_options = df_valid.apply(lambda r: f"{r['emp_id']} — {r['name']} ({r['designation']})", axis=1).tolist()
    sel_emp_str = st.selectbox("Select Employee", emp_options, key="slip_emp")
    sel_emp_id  = sel_emp_str.split(" — ")[0]

    if st.button("🖨️ Generate Slip", type="primary"):
        row = df_valid[df_valid["emp_id"] == sel_emp_id].iloc[0]

        month_disp = selected_month.replace("-", " ")
        pay_date = row["payment_date"]
        try:
            from datetime import datetime
            pay_date = datetime.strptime(pay_date, "%Y-%m-%d").strftime("%d-%b-%Y")
        except Exception:
            pass

        gross = row["gross_salary"]
        net   = row["net_salary"]
        basic = row["basic"]
        hra   = row["hra"]
        da    = row["da"]
        ta    = row["ta"]
        med   = row["medical_allowance"]
        other_allow = row.get("other_allowance", 0) or 0
        pf    = row["pf_deduction"]
        pt    = row["pt"]
        tds   = row["tds"]
        total_ded_v = row["total_deductions"]
        utr   = row["utr_number"]
        acct  = str(row["bank_account"])
        acct_masked = acct[:2] + "X"*(len(acct)-4) + acct[-2:] if len(acct) > 4 else acct

        slip_html = f"""
<div class="slip-box">
<pre style="color:#e2e8f0; margin:0">
╔══════════════════════════════════════════════════════════════════╗
║          UNIVERSITY FINANCE HUB — SALARY SLIP                  ║
║                     {month_disp.upper():^36}                ║
╠══════════════════════════════════════════════════════════════════╣
║  Employee  : {row['name']:<30}  Emp ID : {row['emp_id']:<8}║
║  Designation: {row['designation']:<28}  Dept   : {row['department']:<8}║
║  PAN       : {row['pan']:<30}  Bank   : {row['bank_name']:<8}║
║  A/c No    : {acct_masked:<30}  IFSC   : {row['ifsc']:<8}║
╠══════════════════════════════════════════════════════════════════╣
║        EARNINGS                      DEDUCTIONS                 ║
║  Basic Salary : ₹{basic:>10,.2f}     PF Deduction : ₹{pf:>10,.2f}  ║
║  HRA          : ₹{hra:>10,.2f}     Prof. Tax    : ₹{pt:>10,.2f}  ║
║  DA           : ₹{da:>10,.2f}     TDS          : ₹{tds:>10,.2f}  ║
║  TA           : ₹{ta:>10,.2f}                                   ║
║  Medical      : ₹{med:>10,.2f}     Total Ded    : ₹{total_ded_v:>10,.2f}  ║
║  Other Allow  : ₹{other_allow:>10,.2f}                                   ║
╠══════════════════════════════════════════════════════════════════╣
║  GROSS SALARY : ₹{gross:>10,.2f}       NET PAY      : ₹{net:>10,.2f}  ║
╠══════════════════════════════════════════════════════════════════╣
║  Payment Mode : {row['payment_mode']:<12}   UTR No  : {utr:<20}║
║  Payment Date : {pay_date:<49}║
╚══════════════════════════════════════════════════════════════════╝
</pre>
</div>
"""
        st.markdown(slip_html, unsafe_allow_html=True)

        if st.button("✉️ Mark as Sent", key=f"mark_sent_{sel_emp_id}"):
            conn = sqlite3.connect(DEFAULT_DB_PATH)
            conn.execute(
                "UPDATE salary_structure SET slip_sent=1 WHERE emp_id=? AND month_year=?",
                (sel_emp_id, selected_month)
            )
            conn.commit()
            conn.close()
            load_payroll_data.clear()
            st.success(f"✅ Salary slip marked as sent for {row['name']} ({selected_month})")
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════
# TAB 3 — Department Summary
# ══════════════════════════════════════════════════════════════════════════
with tab3:
    st.subheader(f"Department-wise Payroll Summary — {selected_month}")

    dept_grp = df_valid.groupby("department").agg(
        Headcount=("emp_id","count"),
        Gross=("gross_salary","sum"),
        Deductions=("total_deductions","sum"),
        Net=("net_salary","sum"),
    ).reset_index().sort_values("Net", ascending=False)

    fig_bar = px.bar(
        dept_grp, x="department", y="Net",
        labels={"department": "Department", "Net": "Net Payroll (₹)"},
        title="Net Payroll by Department",
        color="Net",
        color_continuous_scale="Blues",
        template="plotly_dark",
        text=dept_grp["Net"].apply(lambda x: f"₹{x/1e5:.1f}L"),
    )
    fig_bar.update_layout(
        coloraxis_showscale=False,
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font_color="white", height=400,
    )
    fig_bar.update_traces(textposition="outside")
    st.plotly_chart(fig_bar, use_container_width=True)

    dept_display = dept_grp.copy()
    dept_display["Gross"] = dept_display["Gross"].apply(fmt_inr)
    dept_display["Deductions"] = dept_display["Deductions"].apply(fmt_inr)
    dept_display["Net"] = dept_display["Net"].apply(fmt_inr)
    dept_display.columns = ["Department", "Headcount", "Gross Payroll", "Total Deductions", "Net Payroll"]
    st.dataframe(dept_display, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════
# TAB 4 — Payroll Trend
# ══════════════════════════════════════════════════════════════════════════
with tab4:
    st.subheader("Monthly Payroll Trend (Jan–Jun 2026)")

    trend = load_trend_data()

    fig_line = go.Figure()
    fig_line.add_trace(go.Scatter(
        x=trend["month_year"], y=trend["gross"],
        name="Gross Payroll", mode="lines+markers",
        line=dict(color="#60a5fa", width=2),
        hovertemplate="<b>%{x}</b><br>Gross: ₹%{y:,.0f}<extra></extra>",
    ))
    fig_line.add_trace(go.Scatter(
        x=trend["month_year"], y=trend["net"],
        name="Net Payroll", mode="lines+markers",
        line=dict(color="#4ade80", width=2),
        hovertemplate="<b>%{x}</b><br>Net: ₹%{y:,.0f}<extra></extra>",
    ))
    fig_line.add_trace(go.Scatter(
        x=trend["month_year"], y=trend["deductions"],
        name="Total Deductions", mode="lines+markers",
        line=dict(color="#f87171", width=2),
        hovertemplate="<b>%{x}</b><br>Deductions: ₹%{y:,.0f}<extra></extra>",
    ))
    fig_line.update_layout(
        template="plotly_dark",
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font_color="white", height=420,
        xaxis_title="Month", yaxis_title="Amount (₹)",
        legend=dict(orientation="h", y=1.1),
    )
    st.plotly_chart(fig_line, use_container_width=True)

    trend_display = trend.copy()
    trend_display["gross"] = trend_display["gross"].apply(fmt_inr)
    trend_display["deductions"] = trend_display["deductions"].apply(fmt_inr)
    trend_display["net"] = trend_display["net"].apply(fmt_inr)
    trend_display.columns = ["Month", "Gross Payroll", "Total Deductions", "Net Payroll"]
    st.dataframe(trend_display, use_container_width=True, hide_index=True)
