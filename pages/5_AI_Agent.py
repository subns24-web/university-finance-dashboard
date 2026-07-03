import streamlit as st
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils.theme import ENTERPRISE_CSS, kpi_card, section_header, alert, cuap_header, CUAP_LOGO
from utils.data_loader import load_all_data
from utils.ai_agent import get_ai_response

st.set_page_config(page_title="AI Finance Agent", page_icon="🤖", layout="wide")

st.markdown(ENTERPRISE_CSS, unsafe_allow_html=True)

st.title("🤖 AI Finance Agent")
st.markdown("Ask any question about the university's financial data in plain English.")
st.markdown("---")

# ── Load data ──────────────────────────────────────────────────────────────
data = load_all_data()

# ── Session state ──────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

if "pending_question" not in st.session_state:
    st.session_state.pending_question = None

# ── Suggested questions ────────────────────────────────────────────────────
SUGGESTED = [
    "How many students have dues greater than 60 days?",
    "What is the total fee collected in March 2026?",
    "Which payment mode is most used?",
    "What is our collection efficiency this year?",
    "Show me all MBA students with pending fees",
    "Summarize this month's financial position",
    "Who are the top 5 defaulters?",
    "What is the total outstanding fee for B.Tech students?",
]

st.markdown("#### 💡 Suggested Questions")
cols = st.columns(4)
for i, q in enumerate(SUGGESTED):
    with cols[i % 4]:
        if st.button(q, key=f"sq_{i}", use_container_width=True):
            st.session_state.pending_question = q

st.markdown("---")

# ── Chat history display ───────────────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="🧑‍💼" if msg["role"] == "user" else "🤖"):
        st.markdown(msg["content"])

# ── Handle suggested question (set before chat_input to pre-fill) ──────────
if st.session_state.pending_question:
    user_input = st.session_state.pending_question
    st.session_state.pending_question = None
else:
    user_input = None

# ── Chat input ─────────────────────────────────────────────────────────────
typed = st.chat_input("Ask about fees, students, outstanding dues, financial reports...")
if typed:
    user_input = typed

if user_input:
    # Display user message
    with st.chat_message("user", avatar="🧑‍💼"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Get AI response
    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("Thinking..."):
            try:
                response = get_ai_response(st.session_state.messages, data)
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
            except Exception as e:
                error_msg = f"Error: {str(e)}"
                st.error(error_msg)
                # Remove the failed user message from history
                st.session_state.messages.pop()

    st.rerun()

# ── Clear conversation button ──────────────────────────────────────────────
if st.session_state.messages:
    st.markdown("---")
    if st.button("🗑️ Clear Conversation", type="secondary"):
        st.session_state.messages = []
        st.rerun()

# ── Info box ───────────────────────────────────────────────────────────────
with st.expander("ℹ️ About this AI Agent"):
    st.markdown("""
    **University Finance AI Agent** is powered by Claude claude-sonnet-4-6 and has access to:

    - **Student Master**: All enrolled student records
    - **Fee Collection**: All payment receipts and transaction history
    - **Outstanding Fees**: Pending dues and overdue accounts
    - **Balance Sheet**: Assets and liabilities as of 31st March 2026
    - **Income & Expenditure**: Monthly income vs expense breakdown
    - **Ledger Summary**: Tally ledger closing balances

    The agent understands questions in natural language and can:
    - Calculate totals, averages, and percentages
    - Identify defaulters and overdue accounts
    - Generate financial summaries
    - Compare courses, time periods, and payment modes

    **Note:** Set `ANTHROPIC_API_KEY` in your environment or `.env` file to use this feature.
    """)
