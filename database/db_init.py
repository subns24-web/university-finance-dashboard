"""
database/db_init.py
Initialize the SQLite database and seed it from the Tally Excel export.
Run directly:  python database/db_init.py
"""

import sqlite3
import os
import json
from datetime import datetime

import pandas as pd

# ── Paths ──────────────────────────────────────────────────────────────────
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_DIR = os.path.dirname(_THIS_DIR)

DEFAULT_DB_PATH = os.path.join(_THIS_DIR, "university_finance.db")
DEFAULT_EXCEL_PATH = os.path.join(_PROJECT_DIR, "..", "university_tally_export.xlsx")


# ── Schema ─────────────────────────────────────────────────────────────────
_DDL = """
CREATE TABLE IF NOT EXISTS students (
    Student_ID      TEXT,
    Student_Name    TEXT,
    Father_Name     TEXT,
    Course          TEXT,
    Branch          TEXT,
    Batch_Year      INTEGER,
    Semester        INTEGER,
    Mobile          TEXT,
    Email           TEXT,
    Address         TEXT,
    Admission_Date  TEXT,
    Category        TEXT,
    Hostel          TEXT
);

CREATE TABLE IF NOT EXISTS fee_structure (
    Course          TEXT,
    Branch          TEXT,
    Semester        INTEGER,
    Tuition_Fee     REAL,
    Exam_Fee        REAL,
    Lab_Fee         REAL,
    Library_Fee     REAL,
    Sports_Fee      REAL,
    Hostel_Fee      REAL,
    Transport_Fee   REAL,
    Total_Fee       REAL
);

CREATE TABLE IF NOT EXISTS fee_collection (
    Receipt_No      TEXT,
    Date            TEXT,
    Student_ID      TEXT,
    Student_Name    TEXT,
    Course          TEXT,
    Branch          TEXT,
    Semester        INTEGER,
    Academic_Year   TEXT,
    Fee_Type        TEXT,
    Amount_Paid     REAL,
    Payment_Mode    TEXT,
    Transaction_ID  TEXT,
    Bank_Name       TEXT,
    Remarks         TEXT,
    Collected_By    TEXT
);

CREATE TABLE IF NOT EXISTS outstanding_fees (
    Student_ID          TEXT,
    Student_Name        TEXT,
    Course              TEXT,
    Branch              TEXT,
    Semester            INTEGER,
    Academic_Year       TEXT,
    Total_Fee_Due       REAL,
    Amount_Paid         REAL,
    Balance_Due         REAL,
    Due_Date            TEXT,
    Days_Overdue        REAL,
    Last_Payment_Date   TEXT,
    Remarks             TEXT
);

CREATE TABLE IF NOT EXISTS balance_sheet (
    row_num INTEGER,
    col_a   TEXT,
    col_b   TEXT,
    col_c   TEXT,
    col_d   TEXT,
    col_e   TEXT,
    col_f   TEXT,
    col_g   TEXT,
    col_h   TEXT
);

CREATE TABLE IF NOT EXISTS income_expenditure (
    row_num INTEGER,
    col_a   TEXT,
    col_b   TEXT,
    col_c   TEXT,
    col_d   TEXT,
    col_e   TEXT,
    col_f   TEXT,
    col_g   TEXT,
    col_h   TEXT,
    col_i   TEXT,
    col_j   TEXT,
    col_k   TEXT,
    col_l   TEXT,
    col_m   TEXT,
    col_n   TEXT
);

CREATE TABLE IF NOT EXISTS ledger_summary (
    Ledger_Name         TEXT,
    "Group"             TEXT,
    Opening_Balance     REAL,
    Debit_Total         REAL,
    Credit_Total        REAL,
    Closing_Balance     REAL
);

CREATE TABLE IF NOT EXISTS tally_imports (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    filename        TEXT,
    imported_at     TEXT,
    record_counts   TEXT,
    imported_by     TEXT
);
"""

_INDEXES = """
CREATE INDEX IF NOT EXISTS idx_students_course         ON students(Course);
CREATE INDEX IF NOT EXISTS idx_fee_collection_date     ON fee_collection(Date);
CREATE INDEX IF NOT EXISTS idx_fee_collection_ay       ON fee_collection(Academic_Year);
CREATE INDEX IF NOT EXISTS idx_outstanding_days        ON outstanding_fees(Days_Overdue);
"""


# ── Public API ─────────────────────────────────────────────────────────────

def init_db(db_path=None):
    """Create all tables and indexes if they don't already exist."""
    db_path = db_path or DEFAULT_DB_PATH
    conn = sqlite3.connect(db_path)
    conn.executescript(_DDL)
    conn.executescript(_INDEXES)
    conn.commit()
    conn.close()


def _safe_str(val):
    """Convert a value to string for TEXT columns, handling NaT/NaN gracefully."""
    if val is None:
        return None
    try:
        import pandas as pd
        if pd.isna(val):
            return None
    except (TypeError, ValueError):
        pass
    return str(val)


def seed_from_excel(excel_path=None, db_path=None, imported_by="system"):
    """
    Read all sheets from the Tally Excel export and insert into SQLite.
    Clears existing rows before inserting (full refresh).
    Logs the import to the tally_imports audit table.

    Returns a dict with record counts per table.
    """
    excel_path = excel_path or DEFAULT_EXCEL_PATH
    db_path = db_path or DEFAULT_DB_PATH

    # Ensure schema exists
    init_db(db_path)

    xl = pd.ExcelFile(excel_path)
    conn = sqlite3.connect(db_path)
    counts = {}

    try:
        # ── students ──────────────────────────────────────────────────────
        conn.execute("DELETE FROM students")
        df = xl.parse("Student_Master")
        df["Admission_Date"] = pd.to_datetime(df["Admission_Date"], errors="coerce").astype(str)
        df.to_sql("students", conn, if_exists="append", index=False)
        counts["students"] = len(df)

        # ── fee_structure ─────────────────────────────────────────────────
        conn.execute("DELETE FROM fee_structure")
        df = xl.parse("Fee_Structure")
        df.to_sql("fee_structure", conn, if_exists="append", index=False)
        counts["fee_structure"] = len(df)

        # ── fee_collection ────────────────────────────────────────────────
        conn.execute("DELETE FROM fee_collection")
        df = xl.parse("Fee_Collection")
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce").astype(str)
        df.to_sql("fee_collection", conn, if_exists="append", index=False)
        counts["fee_collection"] = len(df)

        # ── outstanding_fees ──────────────────────────────────────────────
        conn.execute("DELETE FROM outstanding_fees")
        df = xl.parse("Outstanding_Fees")
        df["Due_Date"] = pd.to_datetime(df["Due_Date"], errors="coerce").astype(str)
        df["Last_Payment_Date"] = pd.to_datetime(df["Last_Payment_Date"], errors="coerce").astype(str)
        df.to_sql("outstanding_fees", conn, if_exists="append", index=False)
        counts["outstanding_fees"] = len(df)

        # ── balance_sheet (raw, no header) ────────────────────────────────
        conn.execute("DELETE FROM balance_sheet")
        df = xl.parse("Balance_Sheet", header=None)
        # Pad or trim to 8 data columns
        col_names = ["col_a", "col_b", "col_c", "col_d", "col_e", "col_f", "col_g", "col_h"]
        while len(df.columns) < len(col_names):
            df[len(df.columns)] = None
        df = df.iloc[:, :len(col_names)]
        df.columns = col_names
        df.insert(0, "row_num", range(len(df)))
        df = df.map(_safe_str)
        df["row_num"] = df["row_num"].apply(lambda x: int(x) if x is not None else None)
        df.to_sql("balance_sheet", conn, if_exists="append", index=False)
        counts["balance_sheet"] = len(df)

        # ── income_expenditure (raw, no header) ───────────────────────────
        conn.execute("DELETE FROM income_expenditure")
        df = xl.parse("Income_Expenditure", header=None)
        col_names = ["col_a","col_b","col_c","col_d","col_e","col_f","col_g",
                     "col_h","col_i","col_j","col_k","col_l","col_m","col_n"]
        while len(df.columns) < len(col_names):
            df[len(df.columns)] = None
        df = df.iloc[:, :len(col_names)]
        df.columns = col_names
        df.insert(0, "row_num", range(len(df)))
        df = df.map(_safe_str)
        df["row_num"] = df["row_num"].apply(lambda x: int(x) if x is not None else None)
        df.to_sql("income_expenditure", conn, if_exists="append", index=False)
        counts["income_expenditure"] = len(df)

        # ── ledger_summary ────────────────────────────────────────────────
        conn.execute("DELETE FROM ledger_summary")
        df = xl.parse("Ledger_Summary")
        df.to_sql("ledger_summary", conn, if_exists="append", index=False)
        counts["ledger_summary"] = len(df)

        # ── tally_imports audit log ───────────────────────────────────────
        conn.execute(
            "INSERT INTO tally_imports (filename, imported_at, record_counts, imported_by) VALUES (?,?,?,?)",
            (
                os.path.basename(excel_path),
                datetime.now().isoformat(timespec="seconds"),
                json.dumps(counts),
                imported_by,
            ),
        )

        conn.commit()
    finally:
        conn.close()

    return counts


# ── Standalone entry point ─────────────────────────────────────────────────
if __name__ == "__main__":
    excel_path = os.path.abspath(DEFAULT_EXCEL_PATH)
    db_path = DEFAULT_DB_PATH

    print(f"Initializing database at: {db_path}")
    print(f"Seeding from Excel: {excel_path}")

    counts = seed_from_excel(excel_path=excel_path, db_path=db_path, imported_by="cli")

    print("\n✅ Database initialized at database/university_finance.db")
    print("   Record counts:")
    for table, n in counts.items():
        print(f"     {table}: {n} rows")
