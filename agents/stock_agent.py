import subprocess
import time
import requests

try:
    import streamlit as st
except ImportError:
    st = None  # CLI-safe

def run_stock_agent_loop(streamlit_mode=False):
    if streamlit_mode and st:
        memory = st.session_state.agent_conversations["stock"]
        st.markdown("📈 **Stock Sentiment Agent**")

    else:
        memory = []

    # Launch services (only once per runtime; subprocess is idempotent here)
    if not memory:
        print("🚀 Starting stock sentiment services...")
        subprocess.Popen(["bash", "stock_sentiment_analysis/llm_service/script.sh"])
        subprocess.Popen(["bash", "stock_sentiment_analysis/master_service/script.sh"])
        time.sleep(5)  # Wait for APIs to boot

    # ✅ STREAMLIT MODE
    if streamlit_mode and st:
        user_input = st.session_state.get("current_input", "").strip()

        if user_input.lower() in ["exit", "quit", "back"]:
            st.session_state.agent_conversations["stock"] = []  # Clear memory
            return "↩️ Exited Stock Agent. Ask something else to continue."

        # Parse ticker
        ticker = next(
            (word for word in user_input.split() if word.isupper() and 2 <= len(word) <= 5),
            None,
        )

        if not ticker:
            return "❗ Please enter a valid stock ticker (e.g., AAPL, TSLA)."

        try:
            output = subprocess.check_output(
                ["python3", "stock_sentiment_analysis/run_analysis.py", "--ticker", ticker],
                stderr=subprocess.STDOUT,
            )
            response = output.decode("utf-8")
            memory.append({"role": "user", "content": user_input})
            memory.append({"role": "assistant", "content": response})
            return response
        except subprocess.CalledProcessError as e:
            return f"❌ Stock analysis failed.\n\n{e.output.decode('utf-8') if e.output else 'No output'}"

    # ✅ CLI MODE
    else:
        print("\n📈 Entering Stock Sentiment Mode")
        print("Ask about any stock ticker (e.g., TSLA, AAPL, NVDA).")
        print("Type 'exit' to return to the main FinFluent menu.\n")

        while True:
            user_input = input("StockAgent> ").strip()
            if user_input.lower() in ["exit", "quit", "back"]:
                print("↩️ Returning to FinFluent main menu.\n")
                break

            ticker = next(
                (word for word in user_input.split() if word.isupper() and 2 <= len(word) <= 5),
                None,
            )

            if not ticker:
                print("❗ Please include a valid stock ticker (e.g., AAPL, TSLA).")
                continue

            try:
                output = subprocess.check_output(
                    ["python3", "stock_sentiment_analysis/run_analysis.py", "--ticker", ticker],
                    stderr=subprocess.STDOUT,
                )
                print(output.decode("utf-8"))
            except subprocess.CalledProcessError as e:
                print("❌ Stock analysis failed.")
                print(f"Command: {e.cmd}")
                print(f"Output:\n{e.output.decode('utf-8') if e.output else 'No output'}")
