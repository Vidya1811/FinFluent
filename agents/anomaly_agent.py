from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from cryptography.fernet import Fernet
import pandas as pd
import requests
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'stock_sentiment_analysis', 'master_service')))


def decrypt_user_files(file_name: str, user_name: str, key: bytes) -> str:
    cipher = Fernet(key)
    fldr_name = "stock_market"
    decrypted_file_path = "decrypted_data/"  # add slash at end of file path
    with open("secret.key", "wb") as key_file:
        key_file.write(key)

    encrypted_file_path = "FinFluent\\encrypted_files\\"  # add slash at end of file path
    encryp_path = os.path.join(desktop_path, fldr_name, encrypted_file_path, user_name, file_name)

    # Encrypt the CSV file
    with open(encryp_path, "rb") as f:
        data = f.read()

    decrypted_data = cipher.decrypt(data)
    decrypted_file_path = "FinFluent\\decrypted_files\\"  # add slash at end of file path
    decryp_path = os.path.join(desktop_path, fldr_name, decrypted_file_path, user_name, file_name)

    with open(decryp_path, "wb") as f:
        f.write(decrypted_data)
    return decryp_path



def run_anomaly_agent_loop(transactions_path: str, key: bytes) -> None:
    print("\n🚨 Entering Anomaly Detection Mode")
    print("I've scanned your debit transactions for unusual spending.")
    print("Ask about any transaction, category, or pattern. Type 'exit' to return.\n")

    # 1. Load and filter data
    df = pd.read_csv(transactions_path)
    df_debit = df[df["Transaction Type"].str.lower() == "debit"].copy()

    if df_debit.empty or "Amount" not in df_debit.columns:
        print("❌ No debit transactions found or missing 'Amount' column in the dataset.")
        return

    # 2. Standardize transaction amounts
    scaler = StandardScaler()
    df_debit["Amount_scaled"] = scaler.fit_transform(df_debit[["Amount"]])

    # 3. Run Isolation Forest
    model = IsolationForest(n_estimators=100, contamination=0.01, random_state=42)
    df_debit["outlier_flag"] = model.fit_predict(df_debit[["Amount_scaled"]])
    df_debit["is_outlier"] = df_debit["outlier_flag"] == -1

    # 4. Get top outliers
    outliers = df_debit[df_debit["is_outlier"]].sort_values(by="Amount", ascending=False)
    if outliers.empty:
        print("✅ No major spending anomalies detected this month. You're all good!\n")
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

    # 5. Start LLM-powered conversation loop
    conversation_history = [{"role": "system", "content": system_prompt}]
    first_question = "Please analyze these transactions and tell me what's unusual."
    conversation_history.append({"role": "user", "content": first_question})

    res = requests.post(
        "http://localhost:11434/api/chat",
        json={"model": "llama3", "messages": conversation_history, "stream": False},
        headers={"Content-Type": "application/json"},
    )

    response = res.json()["message"]["content"]
    conversation_history.append({"role": "assistant", "content": response})
    print(f"\n💬 {response}\n")

    # 6. Keep the user in a loop
    while True:
        user_input = input("AnomalyAgent> ").strip()
        if user_input.lower() in ["exit", "quit", "back"]:
            print("↩️ Returning to FinFluent main menu.\n")
            break

        conversation_history.append({"role": "user", "content": user_input})
        res = requests.post(
            "http://localhost:11434/api/chat",
            json={"model": "llama3", "messages": conversation_history, "stream": False},
            headers={"Content-Type": "application/json"},
        )

        response = res.json()["message"]["content"]
        conversation_history.append({"role": "assistant", "content": response})
        print(f"\n💬 {response}\n")
