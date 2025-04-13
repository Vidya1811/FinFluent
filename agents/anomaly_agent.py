from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import pandas as pd
import requests

try:
    import streamlit as st
except ImportError:
    st = None  # Allow CLI use


def run_anomaly_agent_loop(transactions_path: str, streamlit_mode=False):
    # For Streamlit: use session memory
    if streamlit_mode and st:
        memory = st.session_state.agent_conversations["anomaly"]
        st.markdown("🚨 **Anomaly Detection Agent**")
    else:
        memory = []

    # Only do anomaly scan once
    if not memory:
        if streamlit_mode and st:
            st.markdown("🔍 Scanning your debit transactions for unusual activity...")

        print("\n🚨 Entering Anomaly Detection Mode")
        print("I've scanned your debit transactions for unusual spending.")
        print("Ask about any transaction, category, or pattern. Type 'exit' to return.\n")

        # 1. Load and filter data
        df = pd.read_csv(transactions_path)
        df_debit = df[df["Transaction Type"].str.lower() == "debit"].copy()

        if df_debit.empty or "Amount" not in df_debit.columns:
            msg = "❌ No debit transactions found or missing 'Amount' column."
            if streamlit_mode:
                return msg
            print(msg)
            return

        # 2. Standardize amounts
        scaler = StandardScaler()
        df_debit["Amount_scaled"] = scaler.fit_transform(df_debit[["Amount"]])

        # 3. Isolation Forest
        model = IsolationForest(n_estimators=100, contamination=0.01, random_state=42)
        df_debit["outlier_flag"] = model.fit_predict(df_debit[["Amount_scaled"]])
        df_debit["is_outlier"] = df_debit["outlier_flag"] == -1

        # 4. Top outliers
        outliers = df_debit[df_debit["is_outlier"]].sort_values(by="Amount", ascending=False)
        if outliers.empty:
            msg = "✅ No major spending anomalies detected this month. You're all good!"
            if streamlit_mode:
                return msg
            print(msg)
            return

        outlier_summary = ""
        for _, row in outliers.head(5).iterrows():
            outlier_summary += f"- {row['Date']}: ${row['Amount']:.2f} for {row['Category']} ({row['Description']})\n"

        system_prompt = f"""
You are a smart financial assistant. Below are unusual debit transactions detected by an Isolation Forest algorithm.

## Detected Anomalies:
{outlier_summary}

## Instructions:
1. Summarize the potential concerns in a friendly tone.
2. Mention if these seem risky or need user attention.
3. Suggest follow-up steps or questions to ask the user.
"""

        memory.append({"role": "system", "content": system_prompt})
        memory.append({
            "role": "user",
            "content": "Please analyze these transactions and tell me what's unusual."
        })

        res = requests.post(
            "http://localhost:11434/api/chat",
            json={"model": "llama3", "messages": memory, "stream": False},
            headers={"Content-Type": "application/json"},
        )

        response = res.json()["message"]["content"]
        memory.append({"role": "assistant", "content": response})

        return response if streamlit_mode else print(f"\n💬 {response}\n")

    # Subsequent turns: continue the conversation
    user_input = st.session_state.current_input if streamlit_mode else input("AnomalyAgent> ").strip()

    if user_input.lower() in ["exit", "quit", "back"]:
        if not streamlit_mode:
            print("↩️ Returning to FinFluent main menu.\n")
        return None

    memory.append({"role": "user", "content": user_input})

    res = requests.post(
        "http://localhost:11434/api/chat",
        json={"model": "llama3", "messages": memory, "stream": False},
        headers={"Content-Type": "application/json"},
    )

    response = res.json()["message"]["content"]
    memory.append({"role": "assistant", "content": response})

    return response if streamlit_mode else print(f"\n💬 {response}\n")
