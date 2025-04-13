import pandas as pd
import requests
from statsmodels.tsa.statespace.sarimax import SARIMAX
from pandas.tseries.offsets import MonthEnd
from cryptography.fernet import Fernet
import sys
import os

desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")


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


def forecast_sarima(data, steps=1):
    model = SARIMAX(
        data,
        order=(3, 0, 0),
        seasonal_order=(1, 0, 1, 12),
        enforce_stationarity=False,
        enforce_invertibility=False,
    )
    model_fit = model.fit(disp=False)
    return model_fit.forecast(steps=steps)


# def run_budget_agent(transactions_path: str) -> str:
#     # 1. Load and clean data
#     df = pd.read_csv(transactions_path, parse_dates=["Date"])

#     debit_categories = {
#         "Shopping",
#         "Entertainment",
#         "Bills",
#         "Restaurants",
#         "Travel",
#         "Mortgage & Rent",
#     }
#     df = df[df["Category"].isin(debit_categories)]
#     df["Amount"] = df["Amount"].abs()
#     df["Month"] = (df["Date"] + MonthEnd(0)).dt.to_period("M").dt.to_timestamp()
#     monthly_spending = (
#         df.groupby(["Month", "Category"])["Amount"].sum().unstack().fillna(0)
#     )
#     monthly_spending.index = pd.date_range(
#         start=monthly_spending.index.min(), periods=len(monthly_spending), freq="MS"
#     )

#     # 2. Forecast next month
#     future_spending = {}
#     for category in monthly_spending.columns:
#         forecast = forecast_sarima(monthly_spending[category])
#         future_spending[category] = forecast.iloc[0]

#     # 3. Compose system prompt
#     forecast_text = "Predicted Spending for Next Month:\n"
#     for category, amount in future_spending.items():
#         forecast_text += f"{category}: ${amount:.2f}\n"

#     system_prompt = f"""
# You are an AI-powered Financial Advisor. Your job is to provide **accurate, data-driven financial guidance**.

# ## User Information:
# - **Monthly Salary:** $10,000
# - **Predicted Spending for Next Month:**
# {forecast_text}

# ## Instructions:
# 1. **Be Specific & Data-Driven:**
#    - Refer to the user’s salary and predicted spending.
#    - Use **numbers, percentages, and trends** instead of generic advice.

# 2. **Provide Cost-Saving Strategies:**
#    - If spending in a category is **higher than 30% of salary**, suggest ways to reduce it.
#    - Recommend savings and investment strategies.

# 3. **Warn About Potential Issues:**
#    - If spending in a category has **increased significantly**, explain why it might be a problem.
#    - Identify risky patterns.
# """

#     # 4. Send to LLaMA 3 via Ollama
#     conversation_history = [{"role": "system", "content": system_prompt}]
#     user_question = "Please analyze this forecast and suggest improvements."
#     conversation_history.append({"role": "user", "content": user_question})

#     res = requests.post(
#         "http://localhost:11434/api/chat",
#         json={"model": "llama3", "messages": conversation_history, "stream": False},
#         headers={"Content-Type": "application/json"},
#     )

#     return res.json()["message"]["content"]

def encrypt_string(string, key):
    cipher = Fernet(key)
    encrypted_string = cipher.encrypt(string.encode())
    return encrypted_string

def decrypt_string(encrypted_string, key):
    cipher = Fernet(key)
    decrypted_string = cipher.decrypt(encrypted_string).decode()
    return decrypted_string

def run_budget_agent_loop(transactions_path: str, key: bytes) -> None:
    print("\n💰 Entering Budget Forecast Mode")
    print(
        "Ask follow-up questions about your spending forecast, categories, or ways to save."
    )
    print("Type 'exit' to return to the FinFluent main menu.\n")

    # 1. Load and clean data
    df = pd.read_csv(transactions_path, parse_dates=["Date"])
    debit_categories = {
        "Shopping",
        "Entertainment",
        "Restaurants",
        "Travel expenses",
        "Mortgage & Rent",
        "Grocery shopping",
        "Utilities",
        "Heating fuel",
    }
    df = df[df["Category"].isin(debit_categories)]
    df["Amount"] = df["Amount"].abs()
    df["Month"] = (df["Date"] + MonthEnd(0)).dt.to_period("M").dt.to_timestamp()
    monthly_spending = (
        df.groupby(["Month", "Category"])["Amount"].sum().unstack().fillna(0)
    )
    monthly_spending.index = pd.date_range(
        start=monthly_spending.index.min(), periods=len(monthly_spending), freq="MS"
    )

    # 2. Forecast next month
    future_spending = {}
    for category in monthly_spending.columns:
        forecast = forecast_sarima(monthly_spending[category])
        future_spending[category] = forecast.iloc[0]

    # 3. Compose system prompt
    forecast_text = "Predicted Spending for Next Month:\n"
    for category, amount in future_spending.items():
        forecast_text += f"{category}: ${amount:.2f}\n"

    system_prompt = f"""
You are an AI-powered Financial Advisor. Your job is to provide **accurate, data-driven financial guidance**.

## User Information:
- **Monthly Salary:** $10,000  
- **Predicted Spending for Next Month:**
{forecast_text}

## Instructions:
1. **Be Specific & Data-Driven:**  
   - Refer to the user’s salary and predicted spending.  
   - Use **numbers, percentages, and trends** instead of generic advice.  

2. **Provide Cost-Saving Strategies:**  
   - If spending in a category is **higher than 30% of salary**, suggest ways to reduce it.  
   - Recommend savings and investment strategies.

3. **Warn About Potential Issues:**  
   - If spending in a category has **increased significantly**, explain why it might be a problem.  
   - Identify risky patterns.
"""

    # 4. Conversation loop with LLaMA 3
    conversation_history = [{"role": "system", "content": system_prompt}]
    print("🧠 Forecast loaded. Ask me anything about your spending.")

    while True:
        user_input = input("BudgetAgent> ").strip()
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
