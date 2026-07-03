import streamlit as st
import pandas as pd
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils.theme import ENTERPRISE_CSS, kpi_card, section_header, alert, cuap_header, CUAP_LOGO
from utils.data_loader import load_all_data, fmt_inr

st.set_page_config(page_title="Balance Sheet", page_icon="📊", layout="wide")

st.markdown(ENTERPRISE_CSS, unsafe_allow_html=True)

st.title("📊 Balance Sheet")
st.markdown("**As at 31st March 2026**")
st.markdown("---")

data = load_all_data()
bs = data["balance_sheet_raw"]

# ── Parse liabilities (cols 0, 3) and assets (cols 4, 7) ──────────────────
liabilities = []
assets = []

for _, row in bs.iterrows():
    liab_name  = str(row["col_a"]).strip() if pd.notna(row["col_a"]) else ""
    liab_val   = row["col_d"] if pd.notna(row["col_d"]) else None
    asset_name = str(row["col_e"]).strip() if pd.notna(row["col_e"]) else ""
    asset_val  = row["col_h"] if pd.notna(row["col_h"]) else None

    # Skip header rows
    if liab_name in ["BALANCE SHEET AS AT 31st MARCH 2026", "LIABILITIES", "Amount (INR)", "nan", ""]:
        liab_name = ""
    if asset_name in ["ASSETS", "Amount (INR)", "nan", ""]:
        asset_name = ""

    liabilities.append({"name": liab_name, "amount": liab_val})
    assets.append({"name": asset_name, "amount": asset_val})

# Section headers (all caps, no amount)
SECTION_HEADERS = {
    "CAPITAL FUND", "RESERVES & SURPLUS", "LOANS & BORROWINGS",
    "CURRENT LIABILITIES", "TOTAL LIABILITIES",
    "FIXED ASSETS", "INVESTMENTS", "CURRENT ASSETS", "TOTAL ASSETS",
}

def render_bs_column(items, title, color):
    st.markdown(f"<h3 style='color:{color};'>{title}</h3>", unsafe_allow_html=True)

    total = 0
    rows_html = []
    for item in items:
        name = item["name"]
        amt = item["amount"]
        if not name:
            rows_html.append("<tr><td>&nbsp;</td><td></td></tr>")
            continue

        is_header = name.upper() in SECTION_HEADERS
        is_total = "TOTAL" in name.upper()

        if is_total:
            # Compute total from numeric amounts collected so far
            rows_html.append(
                f"<tr style='border-top:2px solid {color}; font-weight:700;'>"
                f"<td style='padding:8px 4px'>{name}</td>"
                f"<td style='text-align:right; padding:8px 4px; color:{color};'>{fmt_inr(total)}</td>"
                f"</tr>"
            )
        elif is_header:
            rows_html.append(
                f"<tr><td colspan='2' style='padding:10px 4px 4px; font-weight:700; "
                f"font-size:1rem; color:{color}; border-bottom:1px solid {color};'>"
                f"{name}</td></tr>"
            )
        else:
            display_amt = fmt_inr(amt) if amt is not None else ""
            style = "font-style:italic;" if name.startswith("Less:") else ""
            if amt is not None:
                try:
                    total += float(amt)
                except Exception:
                    pass
            rows_html.append(
                f"<tr><td style='padding:4px 4px 4px 20px; {style}'>{name}</td>"
                f"<td style='text-align:right; padding:4px 8px;'>{display_amt}</td></tr>"
            )

    table_html = (
        f"<table style='width:100%; border-collapse:collapse; font-size:0.92rem;'>"
        + "".join(rows_html)
        + "</table>"
    )
    st.markdown(table_html, unsafe_allow_html=True)
    return total

col_left, col_divider, col_right = st.columns([5, 0.2, 5])

with col_left:
    liab_total = render_bs_column(liabilities, "LIABILITIES", "#4fc3f7")

with col_divider:
    st.markdown(
        "<div style='border-left:2px solid #444; height:600px; margin-top:40px;'></div>",
        unsafe_allow_html=True
    )

with col_right:
    asset_total = render_bs_column(assets, "ASSETS", "#a5d6a7")

st.markdown("---")

col_l, col_r = st.columns(2)
col_l.metric("Total Liabilities", fmt_inr(liab_total))
col_r.metric("Total Assets", fmt_inr(asset_total))

diff = abs(liab_total - asset_total)
if diff < 1:
    st.success("Balance Sheet is BALANCED ✓")
else:
    st.warning(f"Difference: {fmt_inr(diff)} (check data)")
