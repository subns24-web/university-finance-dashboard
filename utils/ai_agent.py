import os
import anthropic
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

MODEL = "claude-sonnet-4-6"


def build_data_context(data: dict) -> str:
    """Build a concise text summary of the financial data for the system prompt."""
    students = data["students"]
    fee_collection = data["fee_collection"]
    outstanding = data["outstanding"]
    ledger = data["ledger"]

    lines = []

    # Student stats
    lines.append("=== STUDENT MASTER ===")
    lines.append(f"Total students: {len(students)}")
    course_counts = students["Course"].value_counts().to_dict()
    for course, cnt in course_counts.items():
        lines.append(f"  {course}: {cnt} students")

    # Fee collection stats
    lines.append("\n=== FEE COLLECTION ===")
    total_collected = fee_collection["Amount_Paid"].sum()
    lines.append(f"Total collected (all time): ₹{total_collected:,.0f}")

    ay_col = fee_collection[fee_collection["Academic_Year"] == "2025-26"]
    lines.append(f"Collected in AY 2025-26: ₹{ay_col['Amount_Paid'].sum():,.0f}")

    monthly = (
        fee_collection.groupby("Month_Name")["Amount_Paid"]
        .sum()
        .reset_index()
        .sort_values("Amount_Paid", ascending=False)
    )
    lines.append("Monthly collection (top months):")
    for _, row in monthly.head(12).iterrows():
        lines.append(f"  {row['Month_Name']}: ₹{row['Amount_Paid']:,.0f}")

    payment_modes = fee_collection["Payment_Mode"].value_counts().to_dict()
    lines.append(f"Payment modes: {payment_modes}")

    course_collection = fee_collection.groupby("Course")["Amount_Paid"].sum().to_dict()
    lines.append("Collection by course:")
    for course, amt in course_collection.items():
        lines.append(f"  {course}: ₹{amt:,.0f}")

    # Outstanding fees
    lines.append("\n=== OUTSTANDING FEES ===")
    lines.append(f"Total outstanding (Balance Due): ₹{outstanding['Balance_Due'].sum():,.0f}")
    lines.append(f"Number of students with dues: {len(outstanding)}")
    overdue_cats = outstanding["Overdue_Category"].value_counts().to_dict()
    lines.append(f"By overdue category: {overdue_cats}")
    course_outstanding = outstanding.groupby("Course")["Balance_Due"].sum().to_dict()
    lines.append("Outstanding by course:")
    for course, amt in course_outstanding.items():
        lines.append(f"  {course}: ₹{amt:,.0f}")

    top_defaulters = outstanding.nlargest(10, "Balance_Due")[
        ["Student_Name", "Course", "Balance_Due", "Days_Overdue"]
    ]
    lines.append("Top 10 defaulters:")
    for _, r in top_defaulters.iterrows():
        lines.append(f"  {r['Student_Name']} ({r['Course']}): ₹{r['Balance_Due']:,.0f} — {r['Days_Overdue']:.0f} days overdue")

    # Ledger summary
    lines.append("\n=== LEDGER SUMMARY ===")
    lines.append(f"Total ledger entries: {len(ledger)}")
    top_ledger = ledger.nlargest(5, "Closing_Balance")[
        ["Ledger_Name", "Closing_Balance"]
    ]
    lines.append("Top ledger entries by closing balance:")
    for _, r in top_ledger.iterrows():
        lines.append(f"  {r['Ledger_Name']}: ₹{r['Closing_Balance']:,.0f}")

    return "\n".join(lines)


def get_relevant_data_for_query(query: str, data: dict) -> str:
    """Return relevant data rows as string for specific queries."""
    query_lower = query.lower()
    parts = []

    outstanding = data["outstanding"]
    fee_collection = data["fee_collection"]
    students = data["students"]

    # Student-specific or course-specific outstanding queries
    for course in outstanding["Course"].unique():
        if course and course.lower() in query_lower:
            df = outstanding[outstanding["Course"] == course]
            parts.append(f"Outstanding fees for {course} students:\n{df[['Student_Name','Branch','Semester','Balance_Due','Days_Overdue','Overdue_Category']].to_string(index=False)}")
            break

    # Overdue day queries
    if "60 day" in query_lower or "60-day" in query_lower or "> 60" in query_lower or ">60" in query_lower:
        df = outstanding[outstanding["Days_Overdue"] > 60]
        parts.append(f"Students with dues > 60 days:\n{df[['Student_Name','Course','Balance_Due','Days_Overdue']].to_string(index=False)}")

    if "90 day" in query_lower or "> 90" in query_lower or ">90" in query_lower:
        df = outstanding[outstanding["Days_Overdue"] > 90]
        parts.append(f"Students with dues > 90 days:\n{df[['Student_Name','Course','Balance_Due','Days_Overdue']].to_string(index=False)}")

    if "30 day" in query_lower or "> 30" in query_lower or ">30" in query_lower:
        df = outstanding[outstanding["Days_Overdue"] > 30]
        parts.append(f"Students with dues > 30 days:\n{df[['Student_Name','Course','Balance_Due','Days_Overdue']].to_string(index=False)}")

    # Month-specific collection queries
    months = ["january","february","march","april","may","june",
              "july","august","september","october","november","december",
              "jan","feb","mar","apr","jun","jul","aug","sep","oct","nov","dec"]
    for month in months:
        if month in query_lower:
            df = fee_collection[fee_collection["Date"].dt.strftime("%B").str.lower() == month.lower()]
            if df.empty:
                df = fee_collection[fee_collection["Date"].dt.strftime("%b").str.lower() == month[:3].lower()]
            if not df.empty:
                parts.append(f"Fee collection in {month.capitalize()}:\nTotal: ₹{df['Amount_Paid'].sum():,.0f}\nNumber of receipts: {len(df)}\n{df[['Receipt_No','Date','Student_Name','Course','Amount_Paid','Payment_Mode']].to_string(index=False)}")
            break

    # Defaulter queries
    if "defaulter" in query_lower or "default" in query_lower:
        df = outstanding[outstanding["Days_Overdue"] > 30].sort_values("Balance_Due", ascending=False)
        parts.append(f"Defaulters (>30 days overdue):\n{df[['Student_Name','Course','Balance_Due','Days_Overdue']].to_string(index=False)}")

    # Payment mode queries
    if "payment mode" in query_lower or "cash" in query_lower or "online" in query_lower or "cheque" in query_lower:
        pm = fee_collection["Payment_Mode"].value_counts()
        parts.append(f"Payment mode breakdown:\n{pm.to_string()}")

    return "\n\n".join(parts) if parts else ""


SYSTEM_PROMPT_TEMPLATE = """You are a University Finance AI Assistant. You have access to the complete financial data of the university including student fee records, outstanding dues, balance sheet, and income/expenditure statements.

You help accountants and finance team members by:
- Answering questions about student fees and payments
- Identifying defaulters and overdue accounts
- Providing financial summaries and trends
- Helping with compliance queries
- Generating reports on demand

Data available:
{data_summary}

Always be precise with numbers, mention amounts in Indian Rupees (₹), and format large numbers with commas (e.g., ₹1,25,000). Use markdown tables and bullet points for clear presentation."""


def get_ai_response(messages: list, data: dict) -> str:
    """
    Call Claude with the full conversation history.
    messages: list of {"role": "user"/"assistant", "content": str}
    """
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    data_summary = build_data_context(data)
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(data_summary=data_summary)

    # For the latest user message, append any relevant data rows
    api_messages = list(messages)
    if api_messages and api_messages[-1]["role"] == "user":
        last_user_msg = api_messages[-1]["content"]
        extra = get_relevant_data_for_query(last_user_msg, data)
        if extra:
            api_messages[-1] = {
                "role": "user",
                "content": last_user_msg + "\n\n[Relevant data from database:]\n" + extra
            }

    response = client.messages.create(
        model=MODEL,
        max_tokens=2048,
        system=system_prompt,
        messages=api_messages,
    )

    return response.content[0].text
