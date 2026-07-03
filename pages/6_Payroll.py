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

        from datetime import datetime

        pay_date = row["payment_date"]
        try:
            pay_date = datetime.strptime(pay_date, "%Y-%m-%d").strftime("%d-%b-%Y")
        except Exception:
            pass

        doj = row.get("date_of_joining", "") or ""
        dob = row.get("date_of_birth", "") or ""
        for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"):
            try: doj = datetime.strptime(doj, fmt).strftime("%d.%m.%Y"); break
            except: pass
        for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"):
            try: dob = datetime.strptime(dob, fmt).strftime("%d.%m.%Y"); break
            except: pass

        gross       = float(row["gross_salary"] or 0)
        net         = float(row["net_salary"] or 0)
        basic       = float(row["basic"] or 0)
        hra         = float(row["hra"] or 0)
        da          = float(row["da"] or 0)
        ta          = float(row["ta"] or 0)
        med         = float(row["medical_allowance"] or 0)
        other_allow = float(row.get("other_allowance") or 0)
        pf          = float(row["pf_deduction"] or 0)
        pt          = float(row["pt"] or 0)
        tds         = float(row["tds"] or 0)
        total_ded_v = float(row["total_deductions"] or 0)
        working_days = int(row.get("working_days") or 31)
        acct = str(row["bank_account"] or "")
        acct_masked = acct[:2] + "X"*(len(acct)-4) + acct[-2:] if len(acct) > 4 else acct

        # Amount in words
        def num_to_words(n):
            n = int(round(n))
            ones = ["","One","Two","Three","Four","Five","Six","Seven","Eight","Nine",
                    "Ten","Eleven","Twelve","Thirteen","Fourteen","Fifteen","Sixteen",
                    "Seventeen","Eighteen","Nineteen"]
            tens = ["","","Twenty","Thirty","Forty","Fifty","Sixty","Seventy","Eighty","Ninety"]
            def two_digit(n):
                if n < 20: return ones[n]
                return tens[n//10] + (" " + ones[n%10] if n%10 else "")
            def three_digit(n):
                if n >= 100:
                    return ones[n//100] + " Hundred" + (" " + two_digit(n%100) if n%100 else "")
                return two_digit(n)
            if n == 0: return "Zero"
            parts = []
            if n >= 10000000:
                parts.append(three_digit(n//10000000) + " Crore"); n %= 10000000
            if n >= 100000:
                parts.append(three_digit(n//100000) + " Lakh"); n %= 100000
            if n >= 1000:
                parts.append(three_digit(n//1000) + " Thousand"); n %= 1000
            if n > 0:
                parts.append(three_digit(n))
            return " ".join(parts)

        net_words = "Rupees " + num_to_words(int(net)) + " Only"

        # Build rows for credits and debits
        credits_rows = [
            ("Basic Salary", f"₹ {basic:,.2f}"),
            ("House Rent Allowance", f"₹ {hra:,.2f}"),
            ("Dearness Allowance", f"₹ {da:,.2f}"),
            ("Transport Allowance", f"₹ {ta:,.2f}"),
            ("Medical Allowance", f"₹ {med:,.2f}"),
        ]
        if other_allow > 0:
            credits_rows.append(("Other Allowance", f"₹ {other_allow:,.2f}"))

        debits_rows = [
            ("Professional Tax", f"₹ {pt:,.2f}"),
            ("Tax Deducted at Source", f"₹ {tds:,.2f}"),
            ("Provident Fund (Employee)", f"₹ {pf:,.2f}"),
        ]

        max_rows = max(len(credits_rows), len(debits_rows))
        while len(credits_rows) < max_rows: credits_rows.append(("", ""))
        while len(debits_rows)  < max_rows: debits_rows.append(("", ""))

        table_rows = ""
        for (cl, cv), (dl, dv) in zip(credits_rows, debits_rows):
            table_rows += f"""
            <tr>
              <td style="padding:6px 10px">{cl}</td>
              <td style="padding:6px 10px; text-align:right; border-right:1px solid #ddd">{cv}</td>
              <td style="padding:6px 10px">{dl}</td>
              <td style="padding:6px 10px; text-align:right">{dv}</td>
            </tr>"""

        slip_html = f"""
<div style="background:white; color:#000; border:2px solid #333; border-radius:4px;
            padding:0; font-family:Arial,sans-serif; font-size:13px; max-width:860px; margin:auto;">

  <!-- Header -->
  <div style="background:#fff; border-bottom:2px solid #333; padding:16px 20px; display:flex; align-items:center; gap:16px;">
    <div style="width:70px; height:70px; border:2px solid #c0392b; border-radius:50%;
                display:flex; align-items:center; justify-content:center; font-size:10px;
                color:#c0392b; text-align:center; font-weight:bold; flex-shrink:0;">UNIV<br>LOGO</div>
    <div style="text-align:center; flex:1;">
      <div style="font-size:18px; font-weight:bold; color:#c0392b;">विश्वविद्यालय वित्त हब</div>
      <div style="font-size:22px; font-weight:bold; color:#1a3a6b;">University Finance Hub</div>
      <div style="font-size:11px; color:#555;">Central University Campus, Visakhapatnam</div>
    </div>
  </div>

  <!-- Slip title -->
  <div style="text-align:center; padding:8px; background:#f5f5f5; border-bottom:1px solid #ccc;">
    <strong style="font-size:15px; text-decoration:underline;">Payslip for {selected_month.replace('-',"' ")}</strong>
  </div>

  <!-- Employee Details Grid -->
  <table style="width:100%; border-collapse:collapse; border-bottom:1px solid #ccc;">
    <tr>
      <td style="padding:5px 10px; width:22%; color:#555;">Employee Number</td>
      <td style="padding:5px 10px; width:28%; font-weight:bold;">{row['emp_id']}</td>
      <td style="padding:5px 10px; width:22%; color:#555;">Employee Name:</td>
      <td style="padding:5px 10px; width:28%; font-weight:bold;">{row['name']}</td>
    </tr>
    <tr style="background:#fafafa;">
      <td style="padding:5px 10px; color:#555;">Department:</td>
      <td style="padding:5px 10px;">{row['department']}</td>
      <td style="padding:5px 10px; color:#555;">No. of Working Days</td>
      <td style="padding:5px 10px;">{working_days}</td>
    </tr>
    <tr>
      <td style="padding:5px 10px; color:#555;">Designation:</td>
      <td style="padding:5px 10px;">{row['designation']}</td>
      <td style="padding:5px 10px; color:#555;">Employment Type:</td>
      <td style="padding:5px 10px;">{row['employment_type']}</td>
    </tr>
    <tr style="background:#fafafa;">
      <td style="padding:5px 10px; color:#555;">PAN No:</td>
      <td style="padding:5px 10px;">{row['pan']}</td>
      <td style="padding:5px 10px; color:#555;">Account No:</td>
      <td style="padding:5px 10px;">{acct_masked}</td>
    </tr>
    <tr>
      <td style="padding:5px 10px; color:#555;">Date of Birth:</td>
      <td style="padding:5px 10px;">{dob}</td>
      <td style="padding:5px 10px; color:#555;">IFSC Code:</td>
      <td style="padding:5px 10px;">{row['ifsc']}</td>
    </tr>
    <tr style="background:#fafafa;">
      <td style="padding:5px 10px; color:#555;">Date of Joining:</td>
      <td style="padding:5px 10px;">{doj}</td>
      <td style="padding:5px 10px; color:#555;">Bank Name:</td>
      <td style="padding:5px 10px;">{row['bank_name']}</td>
    </tr>
    <tr>
      <td style="padding:5px 10px; color:#555;">Payment Mode:</td>
      <td style="padding:5px 10px;">{row['payment_mode']}</td>
      <td style="padding:5px 10px; color:#555;">UTR / Ref No:</td>
      <td style="padding:5px 10px;">{row['utr_number']}</td>
    </tr>
  </table>

  <!-- Credits / Debits -->
  <table style="width:100%; border-collapse:collapse;">
    <thead>
      <tr style="background:#1a3a6b; color:white;">
        <th colspan="2" style="padding:8px 10px; text-align:center; border-right:1px solid #aaa;">CREDITS</th>
        <th colspan="2" style="padding:8px 10px; text-align:center;">DEBITS</th>
      </tr>
    </thead>
    <tbody style="background:#fff;">
      {table_rows}
      <tr style="border-top:1px solid #ccc; font-weight:bold; background:#f0f0f0;">
        <td style="padding:8px 10px;">Gross Total</td>
        <td style="padding:8px 10px; text-align:right; border-right:1px solid #ddd;">₹ {gross:,.2f}</td>
        <td style="padding:8px 10px;">Total Deductions</td>
        <td style="padding:8px 10px; text-align:right;">₹ {total_ded_v:,.2f}</td>
      </tr>
    </tbody>
  </table>

  <!-- Net Salary -->
  <table style="width:100%; border-collapse:collapse; border-top:2px solid #333;">
    <tr style="background:#e8f4e8;">
      <td colspan="3" style="padding:10px 10px; font-weight:bold; font-size:14px; color:#1a6b3a; text-align:center;">
        Net Salary Remitted to Account
      </td>
      <td style="padding:10px 10px; font-weight:bold; font-size:14px; color:#1a6b3a; text-align:right;">
        ₹ {net:,.2f}
      </td>
    </tr>
  </table>

  <!-- Amount in Words -->
  <div style="padding:10px 14px; border-top:1px solid #ccc; background:#fff;">
    <span style="color:#555;">Amount in Words : </span>
    <span style="text-decoration:underline; font-weight:bold;">{net_words}</span>
  </div>

  <!-- Footer -->
  <div style="padding:8px 14px; background:#f9f9f9; border-top:1px solid #ccc;
              font-size:11px; color:#777; font-style:italic; text-align:center;">
    ' This is computer generated, hence no signature is required '
  </div>
</div>
"""
        st.markdown(slip_html, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

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
