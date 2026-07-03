import streamlit as st
import sys, os, random

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils.theme import ENTERPRISE_CSS, CUAP_LOGO
from utils.data_loader import load_all_data
from utils.ai_agent import get_ai_response

st.set_page_config(page_title="AI Finance Agent", page_icon="🤖", layout="wide")
st.markdown(ENTERPRISE_CSS, unsafe_allow_html=True)

st.markdown("""
<style>
.block-container { padding-top: 1rem !important; max-width: 900px !important; margin: 0 auto !important; }

/* chip buttons */
div[data-testid="stHorizontalBlock"] .stButton > button,
.stButton > button {
    border-radius: 22px !important;
    font-size: 0.83rem !important;
    padding: 7px 16px !important;
    border: 1.5px solid #cbd5e1 !important;
    background: white !important;
    color: #334155 !important;
    font-weight: 500 !important;
    transition: all 0.15s !important;
    white-space: normal !important;
    line-height: 1.3 !important;
}
div[data-testid="stHorizontalBlock"] .stButton > button:hover,
.stButton > button:hover {
    background: #003366 !important;
    color: white !important;
    border-color: #003366 !important;
}
/* category chips - bigger */
.cat-chip button {
    border-radius: 22px !important;
    background: #eff6ff !important;
    border: 1.5px solid #bfdbfe !important;
    color: #1e40af !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    padding: 9px 18px !important;
}
.cat-chip button:hover {
    background: #003366 !important;
    color: white !important;
    border-color: #003366 !important;
}

/* user bubble */
.user-bubble {
    background: #003366;
    color: white;
    border-radius: 20px 20px 4px 20px;
    padding: 11px 18px;
    margin: 10px 0 10px 100px;
    font-size: 0.92rem;
    line-height: 1.5;
    box-shadow: 0 2px 8px rgba(0,51,102,0.15);
}
/* ai bubble */
.ai-wrap {
    display: flex;
    gap: 10px;
    margin: 4px 80px 4px 0;
    align-items: flex-start;
}
.ai-avatar {
    width: 34px; height: 34px; border-radius: 50%;
    background: linear-gradient(135deg, #003366, #1a5fa8);
    display: flex; align-items: center; justify-content: center;
    font-size: 1.1rem; flex-shrink: 0; margin-top: 2px;
    box-shadow: 0 2px 6px rgba(0,51,102,0.2);
}
.ai-bubble {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 4px 20px 20px 20px;
    padding: 14px 18px;
    font-size: 0.91rem;
    line-height: 1.65;
    flex: 1;
    box-shadow: 0 1px 4px rgba(0,0,0,0.05);
}

/* section label */
.section-label {
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    color: #94a3b8;
    margin: 16px 0 8px;
}
.welcome-box {
    text-align: center;
    padding: 32px 20px 24px;
}
.back-btn > button {
    background: transparent !important;
    border: none !important;
    color: #64748b !important;
    font-size: 0.8rem !important;
    padding: 2px 8px !important;
}
</style>
""", unsafe_allow_html=True)

data = load_all_data()

# ── Session state ────────────────────────────────────────────────────────────
for k, v in [("messages", []), ("pending_q", None), ("active_cat", None),
              ("next_chips", []), ("last_error", None)]:
    if k not in st.session_state:
        st.session_state[k] = v

# ── Query tree ───────────────────────────────────────────────────────────────
QUERY_TREE = {
    "📌 Defaulters & Dues": {
        "Top Defaulters": [
            "Who are the top 5 defaulters?",
            "Who are the top 10 defaulters with highest dues?",
            "Which course has the highest outstanding fees?",
        ],
        "Overdue Analysis": [
            "How many students have dues greater than 60 days?",
            "How many students have dues greater than 90 days?",
            "Show all students with overdue > 90 days",
            "List students with dues between 30 and 60 days",
        ],
        "Course-wise Dues": [
            "What is the total outstanding fee for B.Tech students?",
            "What is the total outstanding fee for MBA students?",
            "Show me all MBA students with pending fees",
            "Compare outstanding fees across all courses",
        ],
    },
    "💰 Fee Collection": {
        "Monthly Trends": [
            "What is the total fee collected in March 2026?",
            "Which month had the highest fee collection?",
            "Show fee collection trend for last 6 months",
            "What is the monthly average fee collection?",
        ],
        "Payment Modes": [
            "Which payment mode is most used?",
            "What percentage of fees are paid via online transfer?",
            "List all students who paid fees in cash",
            "How many students paid fees via cheque?",
        ],
        "Collection Health": [
            "What is our collection efficiency this year?",
            "How much fee is still pending vs collected?",
            "What is the total fee collected this academic year?",
            "Compare fee collection between B.Tech and MBA students",
        ],
    },
    "📊 Financial Reports": {
        "Income & Expenditure": [
            "What is the total income vs expenditure this year?",
            "What is the annual surplus or deficit?",
            "Which expenditure head has the highest spending?",
            "Show me the top 5 income sources",
        ],
        "Balance Sheet": [
            "What is the total assets vs total liabilities?",
            "Is the balance sheet balanced?",
            "What are the major capital fund components?",
        ],
        "Budget Tracking": [
            "What is the capital budget utilization percentage?",
            "How much of the revenue budget has been used?",
            "Which budget head is over-utilized?",
            "Give me a complete financial health summary",
        ],
    },
    "👥 Payroll & Staff": {
        "Salary Info": [
            "How many active employees are on payroll?",
            "What is the total net payroll for June 2026?",
            "What is the average salary of teaching staff?",
            "Which department has the highest salary expense?",
        ],
        "Salary Slips": [
            "How many salary slips are pending for this month?",
            "What is the salary expenditure for this year?",
        ],
        "Students": [
            "How many students are enrolled course-wise?",
            "Summarize this month's financial position",
        ],
    },
}

CATEGORIES = list(QUERY_TREE.keys())
ALL_FLAT = [q for cat in QUERY_TREE.values() for sub in cat.values() for q in sub]

def send_question(q):
    st.session_state.pending_q = q
    st.session_state.active_cat = None
    st.session_state.next_chips = []

# ── Header ───────────────────────────────────────────────────────────────────
new_chat_btn = ""
if st.session_state.messages:
    new_chat_btn = """
    <a onclick="window.location.reload()" style="
        float:right; background:#f1f5f9; border:1px solid #e2e8f0;
        color:#64748b; font-size:0.78rem; font-weight:600;
        border-radius:20px; padding:5px 14px; cursor:pointer;
        text-decoration:none; margin-top:10px;">
        🗑️ New Chat
    </a>"""

st.markdown(f"""
<div style="display:flex; align-items:center; gap:14px; padding:8px 0 10px;">
  <img src="{CUAP_LOGO}" style="width:46px;height:46px;object-fit:contain;flex-shrink:0;">
  <div style="flex:1;">
    <div style="font-size:1.1rem;font-weight:800;color:#003366;line-height:1.2;">Finance AI Agent</div>
    <div style="font-size:0.73rem;color:#64748b;">Central University of Andhra Pradesh &nbsp;·&nbsp; Powered by Claude Haiku</div>
  </div>
  {new_chat_btn}
</div>
<hr style="margin:0 0 14px;border:none;border-top:1.5px solid #e2e8f0;">
""", unsafe_allow_html=True)

if st.session_state.messages and st.button("🗑️ New Chat", key="newchat", type="secondary"):
    st.session_state.messages = []
    st.session_state.active_cat = None
    st.session_state.next_chips = []
    st.rerun()

# ── Chat messages ────────────────────────────────────────────────────────────
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f'<div class="user-bubble">🧑‍💼 &nbsp; {msg["content"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="ai-wrap"><div class="ai-avatar">🤖</div><div class="ai-bubble">', unsafe_allow_html=True)
        st.markdown(msg["content"])
        st.markdown('</div></div>', unsafe_allow_html=True)

if st.session_state.get("last_error"):
    st.error(f"⚠️ {st.session_state.pop('last_error')}")

# ── Process pending question ─────────────────────────────────────────────────
if st.session_state.pending_q:
    q = st.session_state.pending_q
    st.session_state.pending_q = None
    st.session_state.messages.append({"role": "user", "content": q})
    with st.spinner(""):
        try:
            response = get_ai_response(st.session_state.messages, data)
            st.session_state.messages.append({"role": "assistant", "content": response})
            # Smart follow-up chips
            asked_lower = q.lower()
            next_qs = []
            for cat_data in QUERY_TREE.values():
                for sub_qs in cat_data.values():
                    if any(asked_lower in sq.lower() or sq.lower() in asked_lower for sq in sub_qs):
                        others = [sq for sq in sub_qs if sq != q]
                        next_qs = others[:2]
                        break
                if next_qs:
                    break
            if not next_qs:
                next_qs = random.sample(ALL_FLAT, 3)
            st.session_state.next_chips = next_qs
        except Exception as e:
            st.session_state.messages.pop()
            st.session_state["last_error"] = str(e)
    st.rerun()

# ── After last AI response: follow-up chips ───────────────────────────────────
if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant" and st.session_state.next_chips:
    st.markdown('<div class="section-label">You might also ask</div>', unsafe_allow_html=True)
    chip_cols = st.columns(len(st.session_state.next_chips))
    for i, nq in enumerate(st.session_state.next_chips):
        with chip_cols[i]:
            if st.button(nq, key=f"chip_{i}_{hash(nq)}"):
                send_question(nq)
                st.rerun()
    st.markdown('<div class="section-label">Or explore a topic</div>', unsafe_allow_html=True)

# ── Welcome / Category navigator ─────────────────────────────────────────────
if not st.session_state.messages:
    st.markdown("""
    <div class="welcome-box">
      <div style="font-size:2.4rem;">🎓</div>
      <div style="font-size:1.2rem;font-weight:700;color:#1e293b;margin:10px 0 4px;">
        Hi! I'm your Finance Assistant
      </div>
      <div style="font-size:0.9rem;color:#64748b;">
        I can help with fees, defaulters, payroll, budgets and more.<br>
        Pick a topic below or just type your question.
      </div>
    </div>
    """, unsafe_allow_html=True)

# ── Category → Subcategory → Questions drill-down ────────────────────────────
if st.session_state.active_cat is None:
    # Show top-level categories
    st.markdown('<div class="section-label">What do you want to know?</div>', unsafe_allow_html=True)
    cat_cols = st.columns(len(CATEGORIES))
    for i, cat in enumerate(CATEGORIES):
        with cat_cols[i]:
            st.markdown('<div class="cat-chip">', unsafe_allow_html=True)
            if st.button(cat, key=f"cat_{i}", use_container_width=True):
                st.session_state.active_cat = cat
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

else:
    # Show back + subcategories + questions
    active = st.session_state.active_cat
    sub_data = QUERY_TREE[active]

    bc1, bc2 = st.columns([1, 8])
    with bc1:
        st.markdown('<div class="back-btn">', unsafe_allow_html=True)
        if st.button("← Back", key="back"):
            st.session_state.active_cat = None
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    with bc2:
        st.markdown(f'<div style="font-size:0.92rem;font-weight:700;color:#003366;padding-top:6px;">{active}</div>', unsafe_allow_html=True)

    for sub_title, sub_qs in sub_data.items():
        st.markdown(f'<div class="section-label">{sub_title}</div>', unsafe_allow_html=True)
        q_cols = st.columns(min(len(sub_qs), 2))
        for j, q in enumerate(sub_qs):
            with q_cols[j % 2]:
                if st.button(q, key=f"subq_{hash(q)}", use_container_width=True):
                    send_question(q)
                    st.rerun()

# ── Free-type input ───────────────────────────────────────────────────────────
st.markdown('<hr style="margin:16px 0 4px;border-color:#e2e8f0;">', unsafe_allow_html=True)
typed = st.chat_input("Or type your own question…")
if typed:
    send_question(typed)
    st.rerun()
