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
_NEW_DDL = """
CREATE TABLE IF NOT EXISTS employees (
    emp_id TEXT PRIMARY KEY,
    name TEXT, designation TEXT, department TEXT,
    date_of_joining TEXT, date_of_birth TEXT,
    mobile TEXT, email TEXT, pan TEXT, bank_account TEXT, bank_name TEXT, ifsc TEXT,
    employment_type TEXT,
    status TEXT DEFAULT 'Active'
);

CREATE TABLE IF NOT EXISTS salary_structure (
    emp_id TEXT, month_year TEXT,
    basic REAL, hra REAL, da REAL, ta REAL, medical_allowance REAL, other_allowance REAL,
    gross_salary REAL,
    pf_deduction REAL, pt REAL, tds REAL, other_deduction REAL,
    total_deductions REAL, net_salary REAL,
    working_days INTEGER, paid_days INTEGER, lop_days INTEGER,
    payment_date TEXT, payment_mode TEXT,
    utr_number TEXT,
    slip_sent INTEGER DEFAULT 0,
    PRIMARY KEY (emp_id, month_year)
);

CREATE TABLE IF NOT EXISTS student_fee_ledger (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT, student_name TEXT, course TEXT, branch TEXT,
    batch_year INTEGER,
    fee_type TEXT,
    year_of_study INTEGER,
    semester INTEGER,
    amount_due REAL, amount_paid REAL, balance REAL,
    due_date TEXT, paid_date TEXT,
    receipt_no TEXT, payment_mode TEXT,
    academic_year TEXT, status TEXT
);

CREATE TABLE IF NOT EXISTS budget_revenue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    financial_year TEXT,
    budget_head TEXT, sub_head TEXT,
    budget_amount REAL, revised_amount REAL,
    q1_actual REAL, q2_actual REAL, q3_actual REAL, q4_actual REAL,
    total_actual REAL, variance REAL, variance_pct REAL
);

CREATE TABLE IF NOT EXISTS budget_capital (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    financial_year TEXT,
    asset_category TEXT,
    description TEXT,
    budget_amount REAL, sanctioned_amount REAL,
    amount_spent REAL, amount_committed REAL, balance REAL,
    status TEXT
);
"""

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
    conn.executescript(_NEW_DDL)
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


# ── Seed New Modules ────────────────────────────────────────────────────────

def seed_new_modules(db_path=None):
    """Seed employees, salary_structure, student_fee_ledger, budget tables."""
    import random, math
    from datetime import date, timedelta

    db_path = db_path or DEFAULT_DB_PATH
    init_db(db_path)
    conn = sqlite3.connect(db_path)

    # ── helpers ──────────────────────────────────────────────────────────────
    rng = random.Random(42)

    def rand_date(start_year, end_year):
        d = date(start_year, 1, 1) + timedelta(days=rng.randint(0, (date(end_year, 12, 31) - date(start_year, 1, 1)).days))
        return d.isoformat()

    def rand_mobile():
        return f"9{rng.randint(100000000, 999999999)}"

    def rand_pan():
        letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        return (f"{''.join(rng.choices(letters,k=5))}"
                f"{rng.randint(1000,9999)}"
                f"{rng.choice(letters)}")

    def rand_bank_account():
        return str(rng.randint(10000000000, 99999999999))

    BANKS = ["SBI", "Canara Bank", "Union Bank", "HDFC Bank", "ICICI Bank", "Andhra Bank", "PNB"]
    IFSC_PREFIXES = {"SBI": "SBIN", "Canara Bank": "CNRB", "Union Bank": "UBIN",
                     "HDFC Bank": "HDFC", "ICICI Bank": "ICIC", "Andhra Bank": "ANDB", "PNB": "PUNB"}

    FIRST_NAMES = [
        "Ravi","Suresh","Ramesh","Venkat","Krishna","Srinivas","Rajesh","Naresh","Anil","Sunil",
        "Prasad","Mahesh","Ganesh","Mohan","Kishore","Srikanth","Vamsi","Harish","Deepak","Santosh",
        "Lakshmi","Padma","Sunita","Priya","Anitha","Kavitha","Swathi","Madhavi","Rekha","Usha",
        "Vijaya","Saritha","Mounika","Divya","Aparna","Sravanthi","Bhavana","Sowmya","Keerthi","Naga",
        "Ramu","Sekhar","Babu","Chandra","Hari","Murali","Naidu","Reddy","Rao","Satish",
        "Bhaskar","Teja","Pavan","Arun","Kiran","Vikram","Praveen","Sudheer","Girish","Laxman",
        "Uma","Manga","Lalitha","Sarada","Kamala","Vani","Ratna","Shanti","Mani","Santha"
    ]
    LAST_NAMES = [
        "Reddy","Rao","Naidu","Sharma","Varma","Kumar","Prasad","Chandra","Babu","Raju",
        "Mohan","Kishore","Murthy","Srinivas","Krishnamurthy","Venkatesh","Subramaniam","Iyer","Pillai","Nair"
    ]

    def rand_name():
        return f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}"

    DEPARTMENTS = ["CSE", "ECE", "EEE", "MECH", "CIVIL", "MBA", "MCA", "Science & Humanities", "Administration", "Library", "Accounts", "Estate"]

    teaching_designations = [
        ("Professor", 65000, 85000, "Teaching"),
        ("Associate Professor", 50000, 65000, "Teaching"),
        ("Assistant Professor", 35000, 50000, "Teaching"),
        ("Lecturer", 28000, 35000, "Teaching"),
    ]
    admin_designations = [
        ("Accountant", 22000, 30000, "Admin"),
        ("Senior Clerk", 20000, 28000, "Admin"),
        ("Clerk", 18000, 24000, "Admin"),
        ("Librarian", 25000, 32000, "Admin"),
        ("Lab Technician", 20000, 28000, "Admin"),
        ("Office Superintendent", 28000, 35000, "Admin"),
    ]
    support_designations = [
        ("Security Guard", 14000, 18000, "Non-Teaching"),
        ("Housekeeping Staff", 12000, 15000, "Non-Teaching"),
        ("Driver", 15000, 18000, "Non-Teaching"),
        ("Peon", 12000, 14000, "Non-Teaching"),
        ("Gardener", 12000, 14000, "Non-Teaching"),
    ]

    employees = []
    # 40 teaching
    teach_depts = ["CSE","ECE","EEE","MECH","CIVIL","MBA","MCA","Science & Humanities"]
    for i in range(1, 41):
        desig_info = rng.choice(teaching_designations)
        dept = rng.choice(teach_depts)
        bank = rng.choice(BANKS)
        emp = {
            "emp_id": f"EMP{i:03d}",
            "name": rand_name(),
            "designation": desig_info[0],
            "department": dept,
            "date_of_joining": rand_date(2005, 2023),
            "date_of_birth": rand_date(1970, 1995),
            "mobile": rand_mobile(),
            "email": f"emp{i:03d}@university.edu.in",
            "pan": rand_pan(),
            "bank_account": rand_bank_account(),
            "bank_name": bank,
            "ifsc": f"{IFSC_PREFIXES[bank]}0{rng.randint(100000,999999)}",
            "employment_type": "Teaching",
            "status": "Active",
            "_basic_min": desig_info[1],
            "_basic_max": desig_info[2],
        }
        employees.append(emp)

    # 15 admin
    for i in range(41, 56):
        desig_info = rng.choice(admin_designations)
        dept = rng.choice(["Administration","Accounts","Library","CSE","ECE"])
        bank = rng.choice(BANKS)
        emp = {
            "emp_id": f"EMP{i:03d}",
            "name": rand_name(),
            "designation": desig_info[0],
            "department": dept,
            "date_of_joining": rand_date(2008, 2023),
            "date_of_birth": rand_date(1975, 1998),
            "mobile": rand_mobile(),
            "email": f"emp{i:03d}@university.edu.in",
            "pan": rand_pan(),
            "bank_account": rand_bank_account(),
            "bank_name": bank,
            "ifsc": f"{IFSC_PREFIXES[bank]}0{rng.randint(100000,999999)}",
            "employment_type": "Admin",
            "status": "Active",
            "_basic_min": desig_info[1],
            "_basic_max": desig_info[2],
        }
        employees.append(emp)

    # 10 support
    for i in range(56, 66):
        desig_info = rng.choice(support_designations)
        dept = rng.choice(["Estate","Administration"])
        bank = rng.choice(BANKS)
        emp = {
            "emp_id": f"EMP{i:03d}",
            "name": rand_name(),
            "designation": desig_info[0],
            "department": dept,
            "date_of_joining": rand_date(2010, 2023),
            "date_of_birth": rand_date(1980, 2000),
            "mobile": rand_mobile(),
            "email": f"emp{i:03d}@university.edu.in",
            "pan": rand_pan(),
            "bank_account": rand_bank_account(),
            "bank_name": bank,
            "ifsc": f"{IFSC_PREFIXES[bank]}0{rng.randint(100000,999999)}",
            "employment_type": "Non-Teaching",
            "status": "Active",
            "_basic_min": desig_info[1],
            "_basic_max": desig_info[2],
        }
        employees.append(emp)

    # Insert employees
    conn.execute("DELETE FROM employees")
    for e in employees:
        conn.execute(
            "INSERT OR REPLACE INTO employees (emp_id,name,designation,department,date_of_joining,date_of_birth,mobile,email,pan,bank_account,bank_name,ifsc,employment_type,status) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (e["emp_id"],e["name"],e["designation"],e["department"],e["date_of_joining"],e["date_of_birth"],
             e["mobile"],e["email"],e["pan"],e["bank_account"],e["bank_name"],e["ifsc"],e["employment_type"],e["status"])
        )

    # salary_structure for Jan-2026 to Jun-2026
    months = ["Jan-2026","Feb-2026","Mar-2026","Apr-2026","May-2026","Jun-2026"]
    payment_dates = ["2026-01-28","2026-02-27","2026-03-28","2026-04-28","2026-05-28","2026-06-28"]
    conn.execute("DELETE FROM salary_structure")

    utr_counter = 1000001
    for e in employees:
        basic = rng.randint(e["_basic_min"], e["_basic_max"])
        for mi, (month, pdate) in enumerate(zip(months, payment_dates)):
            basic_var = basic + rng.randint(-500, 500)
            hra = round(basic_var * 0.20, 2)
            da = round(basic_var * 0.17, 2)
            ta = rng.randint(1500, 3000)
            medical = 1250.0
            other_allow = rng.randint(500, 2000)
            gross = round(basic_var + hra + da + ta + medical + other_allow, 2)
            pf = round(basic_var * 0.12, 2)
            pt = 200.0
            # TDS: rough slab
            annual_gross = gross * 12
            if annual_gross > 1000000:
                tds = round((gross * 0.20) / 12, 2)
            elif annual_gross > 500000:
                tds = round((gross * 0.10) / 12, 2)
            else:
                tds = 0.0
            other_ded = 0.0
            total_ded = round(pf + pt + tds + other_ded, 2)
            net = round(gross - total_ded, 2)
            working_days = 26
            lop = rng.choice([0,0,0,0,1,1,2])
            paid_days = working_days - lop
            conn.execute(
                """INSERT OR REPLACE INTO salary_structure
                (emp_id,month_year,basic,hra,da,ta,medical_allowance,other_allowance,gross_salary,
                pf_deduction,pt,tds,other_deduction,total_deductions,net_salary,
                working_days,paid_days,lop_days,payment_date,payment_mode,utr_number,slip_sent)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (e["emp_id"],month,basic_var,hra,da,ta,medical,other_allow,gross,
                 pf,pt,tds,other_ded,total_ded,net,
                 working_days,paid_days,lop,"2026-"+pdate[5:],"NEFT",f"UTR{utr_counter}",1)
            )
            utr_counter += 1

    # ── student_fee_ledger ───────────────────────────────────────────────────
    COURSES = [
        ("B.Tech", ["CSE","ECE","EEE","MECH","CIVIL"], 85000, 8),
        ("MBA",    ["Finance","Marketing","HR"],        95000, 4),
        ("MCA",    ["MCA"],                             70000, 6),
        ("BBA",    ["BBA"],                             55000, 6),
    ]
    FEE_TYPES_ANNUAL = [
        ("Mess Fee",    35000),
        ("Annual Fee",  5000),
    ]
    PAYMENT_MODES = ["Online","Challan","DD","NEFT","Cash"]
    BATCH_YEARS = [2022, 2023, 2024, 2025]

    conn.execute("DELETE FROM student_fee_ledger")
    receipt_counter = 100001
    student_counter = 1

    student_pool = []
    for batch in BATCH_YEARS:
        for ci, (course, branches, sem_fee, num_sems) in enumerate(COURSES):
            count = 200 // len(COURSES)
            for j in range(count):
                sid = f"STU{batch}{ci+1}{j+1:03d}"
                sname = rand_name()
                branch = rng.choice(branches)
                student_pool.append((sid, sname, course, branch, batch, sem_fee, num_sems))

    for (sid, sname, course, branch, batch, sem_fee, num_sems) in student_pool:
        num_years = num_sems // 2
        ay_start = batch
        for yr in range(1, num_years + 1):
            ay = f"{ay_start+yr-1}-{str(ay_start+yr)[2:]}"
            sems_this_year = [yr*2-1, yr*2]
            for sem in sems_this_year:
                due_date = f"{ay_start+yr-1}-07-15" if sem % 2 == 1 else f"{ay_start+yr-1}-12-15"
                roll = rng.random()
                if roll < 0.75:
                    status = "Paid"
                    amount_paid = sem_fee
                    balance = 0.0
                    paid_date = f"{due_date[:4]}-{rng.randint(7,8):02d}-{rng.randint(1,25):02d}" if sem % 2 == 1 else f"{due_date[:4]}-{rng.randint(12,12):02d}-{rng.randint(1,25):02d}"
                elif roll < 0.90:
                    status = "Partial"
                    amount_paid = round(sem_fee * rng.uniform(0.3, 0.8), 2)
                    balance = round(sem_fee - amount_paid, 2)
                    paid_date = f"{due_date[:4]}-{rng.randint(7,9):02d}-{rng.randint(1,28):02d}"
                else:
                    status = "Pending"
                    amount_paid = 0.0
                    balance = sem_fee
                    paid_date = None

                conn.execute(
                    """INSERT INTO student_fee_ledger
                    (student_id,student_name,course,branch,batch_year,fee_type,year_of_study,semester,
                    amount_due,amount_paid,balance,due_date,paid_date,receipt_no,payment_mode,academic_year,status)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (sid,sname,course,branch,batch,"Semester Fee",yr,sem,
                     sem_fee,amount_paid,balance,due_date,paid_date,
                     f"RCT{receipt_counter}" if amount_paid>0 else None,
                     rng.choice(PAYMENT_MODES) if amount_paid>0 else None,
                     ay,status)
                )
                if amount_paid > 0:
                    receipt_counter += 1

            # Mess fee
            mess_due = sem_fee * 0  # different calc
            mess_amount = 35000.0
            mess_roll = rng.random()
            if mess_roll < 0.75:
                mess_status = "Paid"; mess_paid = mess_amount; mess_bal = 0.0; mess_pdate = f"{ay_start+yr-1}-08-01"
            elif mess_roll < 0.90:
                mess_status = "Partial"; mess_paid = round(mess_amount * rng.uniform(0.4, 0.8), 2); mess_bal = round(mess_amount - mess_paid, 2); mess_pdate = f"{ay_start+yr-1}-08-10"
            else:
                mess_status = "Pending"; mess_paid = 0.0; mess_bal = mess_amount; mess_pdate = None

            conn.execute(
                """INSERT INTO student_fee_ledger
                (student_id,student_name,course,branch,batch_year,fee_type,year_of_study,semester,
                amount_due,amount_paid,balance,due_date,paid_date,receipt_no,payment_mode,academic_year,status)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (sid,sname,course,branch,batch,"Mess Fee",yr,None,
                 mess_amount,mess_paid,mess_bal,f"{ay_start+yr-1}-07-20",mess_pdate,
                 f"RCT{receipt_counter}" if mess_paid>0 else None,
                 rng.choice(PAYMENT_MODES) if mess_paid>0 else None,
                 ay,mess_status)
            )
            if mess_paid > 0:
                receipt_counter += 1

            # Annual/Dev fee
            ann_amount = 5000.0
            ann_roll = rng.random()
            if ann_roll < 0.80:
                ann_status = "Paid"; ann_paid = ann_amount; ann_bal = 0.0; ann_pdate = f"{ay_start+yr-1}-07-25"
            elif ann_roll < 0.92:
                ann_status = "Partial"; ann_paid = round(ann_amount * 0.5, 2); ann_bal = round(ann_amount - ann_paid, 2); ann_pdate = f"{ay_start+yr-1}-08-05"
            else:
                ann_status = "Pending"; ann_paid = 0.0; ann_bal = ann_amount; ann_pdate = None

            conn.execute(
                """INSERT INTO student_fee_ledger
                (student_id,student_name,course,branch,batch_year,fee_type,year_of_study,semester,
                amount_due,amount_paid,balance,due_date,paid_date,receipt_no,payment_mode,academic_year,status)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (sid,sname,course,branch,batch,"Annual Fee",yr,None,
                 ann_amount,ann_paid,ann_bal,f"{ay_start+yr-1}-07-20",ann_pdate,
                 f"RCT{receipt_counter}" if ann_paid>0 else None,
                 rng.choice(PAYMENT_MODES) if ann_paid>0 else None,
                 ay,ann_status)
            )
            if ann_paid > 0:
                receipt_counter += 1

    # ── Budget Revenue ────────────────────────────────────────────────────────
    conn.execute("DELETE FROM budget_revenue")
    revenue_heads = [
        ("Tuition Fee Income",   None, 42000000, 45000000),
        ("Hostel Fee",           None, 8500000,  9000000),
        ("Transport Fee",        None, 2200000,  2200000),
        ("Exam Fee",             None, 1800000,  1900000),
        ("Development Fee",      None, 3000000,  3000000),
        ("Grant Income",         "UGC Grant",    5000000,  5500000),
        ("Grant Income",         "State Grant",  2000000,  2200000),
        ("Other Income",         None, 800000,   850000),
    ]
    for (head, sub, budget, revised) in revenue_heads:
        q1 = round(revised * rng.uniform(0.22, 0.30), 2)
        q2 = round(revised * rng.uniform(0.20, 0.28), 2)
        q3 = round(revised * rng.uniform(0.18, 0.26), 2)
        q4 = round(revised * rng.uniform(0.15, 0.25), 2)
        total = round(q1+q2+q3+q4, 2)
        variance = round(total - budget, 2)
        variance_pct = round((variance / budget)*100, 2) if budget else 0
        conn.execute(
            """INSERT INTO budget_revenue
            (financial_year,budget_head,sub_head,budget_amount,revised_amount,q1_actual,q2_actual,q3_actual,q4_actual,total_actual,variance,variance_pct)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            ("2025-26", head, sub, budget, revised, q1, q2, q3, q4, total, variance, variance_pct)
        )

    # ── Budget Capital ────────────────────────────────────────────────────────
    conn.execute("DELETE FROM budget_capital")
    capital_items = [
        ("Building",   "Building Renovation - Phase 2",      8000000, 8000000, 6500000, 800000, "In Progress"),
        ("IT",         "Computer Lab Equipment Upgrade",      4500000, 4500000, 3200000, 500000, "In Progress"),
        ("Library",    "Library Books & Journals",            1200000, 1200000, 1100000, 0,      "Completed"),
        ("Furniture",  "Furniture for New Classrooms",         800000,  800000,  750000,  0,      "Completed"),
        ("Security",   "CCTV & Security System",              600000,  600000,  580000,  0,      "Completed"),
        ("Vehicles",   "University Bus Purchase",            2200000, 2200000,  900000, 1100000, "In Progress"),
        ("Electrical", "Solar Panel Installation",           3500000, 3500000,  500000, 1200000, "In Progress"),
        ("IT",         "ERP Software Implementation",        1500000, 1500000,  800000,  400000, "In Progress"),
        ("Building",   "Hostel Renovation",                  2500000, 1800000,    0,   500000,   "Planned"),
        ("Equipment",  "Science Lab Equipment",              1000000,  800000,    0,       0,     "On Hold"),
    ]
    for (cat, desc, budget, sanctioned, spent, committed, status) in capital_items:
        balance = round(sanctioned - spent - committed, 2)
        conn.execute(
            """INSERT INTO budget_capital
            (financial_year,asset_category,description,budget_amount,sanctioned_amount,amount_spent,amount_committed,balance,status)
            VALUES (?,?,?,?,?,?,?,?,?)""",
            ("2025-26", cat, desc, budget, sanctioned, spent, committed, balance, status)
        )

    conn.commit()
    conn.close()
    print("✅ New modules seeded: employees, salary_structure, student_fee_ledger, budget_revenue, budget_capital")


# ── Standalone entry point ─────────────────────────────────────────────────
if __name__ == "__main__":
    excel_path = os.path.abspath(DEFAULT_EXCEL_PATH)
    db_path = DEFAULT_DB_PATH

    print(f"Initializing database at: {db_path}")
    print(f"Seeding from Excel: {excel_path}")

    # Seed new modules regardless of Excel
    seed_new_modules(db_path=db_path)

    try:
        counts = seed_from_excel(excel_path=excel_path, db_path=db_path, imported_by="cli")
        print("\n✅ Database initialized at database/university_finance.db")
        print("   Record counts:")
        for table, n in counts.items():
            print(f"     {table}: {n} rows")
    except Exception as e:
        print(f"\n⚠️  Excel seeding skipped (file not found or error): {e}")
        print("✅ New module tables seeded successfully.")
