import streamlit as st
import tempfile
import os
from controller.central_controller import route_user_query
from agents.budget_agent import run_budget_agent_loop
from agents.anomaly_agent import run_anomaly_agent_loop
from agents.stock_agent import run_stock_agent_loop
from agents.portfolio_agent import run_portfolio_agent_loop

# ==============================
# 🔒 Default fallback CSV paths
# ==============================

DEFAULT_BUDGET_PATH = "/Users/vidyakalyandurg/Desktop/FinFluent/data/user_1.csv"
DEFAULT_ANOMALY_PATH = "/Users/vidyakalyandurg/Desktop/FinFluent/data/user_1.csv"
DEFAULT_PORTFOLIO_PATH = "/Users/vidyakalyandurg/Desktop/FinFluent/data/sample_portfolio.csv"

# ==============================
# ⚙️ Streamlit config & app title
# ==============================

st.set_page_config(page_title="FinFluent", layout="wide")
st.title("💰 FinFluent - Your AI Financial Advisor")

# ==============================
# 🧠 Session state initialization
# ==============================

if "messages" not in st.session_state:
    st.session_state.messages = [{
        "role": "assistant",
        "content": """👋 Welcome to FinFluent!

Here’s what I can do:

🔮 Budget Forecasting — See where your money is headed next month  
🚨 Anomaly Detection — Spot unusual or suspicious transactions  
📈 Stock Sentiment — Get recent stock news and trends  
📊 Portfolio Review — Analyze your current holdings

You can also upload your own files.
"""
    }]

if "active_agent" not in st.session_state:
    st.session_state.active_agent = None

if "agent_conversations" not in st.session_state:
    st.session_state.agent_conversations = {
        "budget": [],
        "anomaly": [],
        "stock": [],
        "portfolio": [],
    }

# ==============================
# 📁 Upload section (always at top)
# ==============================

st.markdown("### 📁 Upload Your Files")

st.markdown("Upload a bank statement for budget & anomaly detection:")
budget_file = st.file_uploader("📄 Bank Statement CSV", type=["csv"], key="budget_file", label_visibility="collapsed")

st.markdown("Upload a stock portfolio for portfolio analysis:")
portfolio_file = st.file_uploader("📊 Portfolio CSV", type=["csv"], key="portfolio_file", label_visibility="collapsed")

# 🔐 Trust Message (moved here)
st.markdown(
    "<div style='margin-top: -5px; margin-bottom: 15px; font-size: 0.85rem; color: gray;'>🔐 We ensure end-to-end encryption. Your data is safe with us.</div>",
    unsafe_allow_html=True,
)

# Handle uploaded files → fallback to defaults if not uploaded
if budget_file:
    temp_budget = tempfile.NamedTemporaryFile(delete=False, suffix=".csv", mode="wb")
    temp_budget.write(budget_file.read())
    temp_budget.flush()
    temp_budget.close()
    BUDGET_DATA_PATH = temp_budget.name
    ANOMALY_DATA_PATH = temp_budget.name
else:
    BUDGET_DATA_PATH = DEFAULT_BUDGET_PATH
    ANOMALY_DATA_PATH = DEFAULT_ANOMALY_PATH

if portfolio_file:
    temp_portfolio = tempfile.NamedTemporaryFile(delete=False, suffix=".csv", mode="wb")
    temp_portfolio.write(portfolio_file.read())
    temp_portfolio.flush()
    temp_portfolio.close()
    PORTFOLIO_DATA_PATH = temp_portfolio.name
else:
    PORTFOLIO_DATA_PATH = DEFAULT_PORTFOLIO_PATH

# ==============================
# 🧼 Markdown sanitization helper
# ==============================

def safe_markdown(text: str) -> str:
    return (
        text.replace("_", "\\_")
            .replace("*", "\\*")
            .replace("`", "\\`")
    )

# ==============================
# 💬 Render chat history
# ==============================

st.divider()
st.markdown("### 💬 FinFluent Chat")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(safe_markdown(msg["content"]))

# ==============================
# 📤 Input + Agent routing
# ==============================

def get_active_agent_response(agent, message):
    st.session_state.current_input = message

    if agent == "budget":
        return run_budget_agent_loop(BUDGET_DATA_PATH, streamlit_mode=True)
    elif agent == "anomaly":
        return run_anomaly_agent_loop(ANOMALY_DATA_PATH, streamlit_mode=True)
    elif agent == "stock":
        return run_stock_agent_loop(streamlit_mode=True)
    elif agent == "portfolio":
        return run_portfolio_agent_loop(PORTFOLIO_DATA_PATH, streamlit_mode=True)
    return "❌ Unknown agent"

# Agent status indicator
agent_labels = {
    "budget": "🔮 Budget Forecasting Agent",
    "anomaly": "🚨 Anomaly Detection Agent",
    "stock": "📈 Stock Sentiment Agent",
    "portfolio": "📊 Portfolio Review Agent"
}
active = st.session_state.active_agent
if active:
    st.markdown(
        f"<div style='margin-top: 0.25rem; font-size: 0.9rem;'>🧠 <b>Currently talking to:</b> <code>{agent_labels.get(active, active)}</code></div>",
        unsafe_allow_html=True
    )

# Chat input field
user_input = st.chat_input("Ask about your finances... [type 'back' to exit agent]")

if user_input:
    user_lower = user_input.lower().strip()
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.markdown(safe_markdown(user_input))

    with st.chat_message("assistant"):
        if user_lower in ["exit", "quit", "back"]:
            agent = st.session_state.active_agent
            st.session_state.agent_conversations[agent] = []
            st.session_state.active_agent = None
            response = "👋 You’ve exited the current agent. Ask anything to begin again."
        else:
            agent = st.session_state.active_agent
            if agent is None:
                agent = route_user_query(user_input)
                st.session_state.active_agent = agent
                st.markdown(f"🔁 Routing to `{agent}` agent...")

            try:
                response = get_active_agent_response(agent, user_input)
            except Exception as e:
                response = f"❌ An error occurred while processing your request.\n\n```{e}```"

        st.markdown(safe_markdown(response))
        st.session_state.messages.append({"role": "assistant", "content": response})
