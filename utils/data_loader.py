import sqlite3
import pandas as pd
import streamlit as st
from datetime import datetime
import os

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(base_dir, "database", "university_finance.db")


@st.cache_data
def load_all_data(db_path=None):
    """Load and cache all tables from SQLite, return dict of DataFrames with derived fields."""
    path = db_path or DB_PATH
    conn = sqlite3.connect(path)

    # --- Student Master ---
    students = pd.read_sql("SELECT * FROM students", conn)
    students["Admission_Date"] = pd.to_datetime(students["Admission_Date"], errors="coerce")

    # --- Fee Structure ---
    fee_structure = pd.read_sql("SELECT * FROM fee_structure", conn)

    # --- Fee Collection ---
    fee_collection = pd.read_sql("SELECT * FROM fee_collection", conn)
    fee_collection["Date"] = pd.to_datetime(fee_collection["Date"], errors="coerce")
    fee_collection["Amount_Paid"] = pd.to_numeric(fee_collection["Amount_Paid"], errors="coerce").fillna(0)
    fee_collection["Month"] = fee_collection["Date"].dt.to_period("M")
    fee_collection["Month_Name"] = fee_collection["Date"].dt.strftime("%b %Y")
    fee_collection["Year"] = fee_collection["Date"].dt.year
    fee_collection["MonthNum"] = fee_collection["Date"].dt.month

    # --- Outstanding Fees ---
    outstanding = pd.read_sql("SELECT * FROM outstanding_fees", conn)
    outstanding["Total_Fee_Due"] = pd.to_numeric(outstanding["Total_Fee_Due"], errors="coerce").fillna(0)
    outstanding["Amount_Paid"] = pd.to_numeric(outstanding["Amount_Paid"], errors="coerce").fillna(0)
    outstanding["Balance_Due"] = pd.to_numeric(outstanding["Balance_Due"], errors="coerce")
    # Compute Balance_Due if missing
    mask = outstanding["Balance_Due"].isna()
    outstanding.loc[mask, "Balance_Due"] = (
        outstanding.loc[mask, "Total_Fee_Due"] - outstanding.loc[mask, "Amount_Paid"]
    )
    outstanding["Balance_Due"] = outstanding["Balance_Due"].fillna(0)
    outstanding["Days_Overdue"] = pd.to_numeric(outstanding["Days_Overdue"], errors="coerce").fillna(0)
    outstanding["Due_Date"] = pd.to_datetime(outstanding["Due_Date"], errors="coerce")
    outstanding["Last_Payment_Date"] = pd.to_datetime(outstanding["Last_Payment_Date"], errors="coerce")

    # Overdue category
    def overdue_category(days):
        if days <= 0:
            return "Current"
        elif days <= 30:
            return "<30 days"
        elif days <= 60:
            return "30-60 days"
        elif days <= 90:
            return "60-90 days"
        else:
            return ">90 days"

    outstanding["Overdue_Category"] = outstanding["Days_Overdue"].apply(overdue_category)

    # --- Balance Sheet (raw) ---
    balance_sheet_raw = pd.read_sql("SELECT * FROM balance_sheet ORDER BY row_num", conn)

    # --- Income & Expenditure (raw) ---
    income_exp_raw = pd.read_sql("SELECT * FROM income_expenditure ORDER BY row_num", conn)

    # --- Ledger Summary ---
    ledger = pd.read_sql("SELECT * FROM ledger_summary", conn)
    for col in ["Opening_Balance", "Debit_Total", "Credit_Total", "Closing_Balance"]:
        ledger[col] = pd.to_numeric(ledger[col], errors="coerce").fillna(0)

    conn.close()

    return {
        "students": students,
        "fee_structure": fee_structure,
        "fee_collection": fee_collection,
        "outstanding": outstanding,
        "balance_sheet_raw": balance_sheet_raw,
        "income_exp_raw": income_exp_raw,
        "ledger": ledger,
    }


def get_kpis(data):
    """Compute dashboard KPIs from loaded data."""
    students = data["students"]
    fee_collection = data["fee_collection"]
    outstanding = data["outstanding"]

    total_students = len(students)

    # Current AY = 2025-26
    current_ay = "2025-26"
    ay_collection = fee_collection[fee_collection["Academic_Year"] == current_ay]
    total_collected = ay_collection["Amount_Paid"].sum()

    total_outstanding = outstanding["Balance_Due"].sum()

    # Collection efficiency
    total_due = outstanding["Total_Fee_Due"].sum() + total_collected
    collection_efficiency = (total_collected / total_due * 100) if total_due > 0 else 0

    # Defaulters: dues > 30 days
    defaulters = len(outstanding[outstanding["Days_Overdue"] > 30])

    # Current month collection
    today = datetime.today()
    monthly = fee_collection[
        (fee_collection["Date"].dt.month == today.month)
        & (fee_collection["Date"].dt.year == today.year)
    ]["Amount_Paid"].sum()

    return {
        "total_students": total_students,
        "total_collected": total_collected,
        "total_outstanding": total_outstanding,
        "collection_efficiency": collection_efficiency,
        "defaulters": defaulters,
        "monthly_collection": monthly,
    }


def get_monthly_collection_trend(fee_collection, months=12):
    """Last N months of fee collection."""
    monthly = (
        fee_collection.groupby("Month")["Amount_Paid"]
        .sum()
        .reset_index()
        .sort_values("Month")
        .tail(months)
    )
    monthly["Month_Label"] = monthly["Month"].dt.strftime("%b %Y")
    return monthly


def fmt_inr(amount):
    """Format number as Indian Rupees with commas."""
    if pd.isna(amount):
        return "₹0"
    amount = int(amount)
    s = str(abs(amount))
    # Indian number system: last 3 digits, then groups of 2
    if len(s) <= 3:
        result = s
    else:
        result = s[-3:]
        s = s[:-3]
        while s:
            result = s[-2:] + "," + result
            s = s[:-2]
    return ("₹" if amount >= 0 else "-₹") + result
