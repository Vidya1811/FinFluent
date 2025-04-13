import pandas as pd
from statsmodels.tsa.statespace.sarimax import SARIMAX
from pandas.tseries.offsets import MonthEnd
import requests

try:
    import streamlit as st
except ImportError:
    st = None

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

def run_budget_agent_loop(transactions_path: str, streamlit_mode=False):
    import streamlit as st  # safe for dual use

    # Load session memory
    memory = st.session_state.agent_conversations["budget"]

    # Only do forecast ONCE per session
    if not memory:
        # Load and clean data
        df = pd.read_csv(transactions_path, parse_dates=["Date"])
        debit_categories = {
            "Shopping", "Entertainment", "Restaurants", "Travel expenses",
            "Mortgage & Rent", "Grocery shopping", "Utilities", "Heating fuel"
        }
        df = df[df["Category"].isin(debit_categories)]
        df["Amount"] = df["Amount"].abs()
        df["Month"] = (df["Date"] + MonthEnd(0)).dt.to_period("M").dt.to_timestamp()
        monthly_spending = df.groupby(["Month", "Category"])["Amount"].sum().unstack().fillna(0)
        monthly_spending.index = pd.date_range(
            start=monthly_spending.index.min(), periods=len(monthly_spending), freq="MS"
        )

        # Forecast
        future_spending = {
            category: forecast_sarima(monthly_spending[category]).iloc[0]
            for category in monthly_spending.columns
        }

        # Format forecast
        forecast_text = "\n".join(
            f"- {cat}: ${amt:.2f}" for cat, amt in future_spending.items()
        )

        # System prompt
        system_prompt = f"""
You are an AI-powered Financial Advisor. Your job is to provide accurate, data-driven financial guidance.

## User Information:
- Monthly Salary: $10,000  
- Predicted Spending for Next Month:
{forecast_text}

## Instructions:
1. Be specific and data-driven
2. Recommend savings strategies
3. Warn about high-risk categories
"""

        memory.append({"role": "system", "content": system_prompt})
        memory.append({"role": "user", "content": "Please analyze my forecast and offer suggestions."})

        # Initial response
        res = requests.post(
            "http://localhost:11434/api/chat",
            json={"model": "llama3", "messages": memory, "stream": False},
            headers={"Content-Type": "application/json"},
        )

        initial_response = res.json()["message"]["content"]
        memory.append({"role": "assistant", "content": initial_response})
        return initial_response

    # Otherwise: continue the conversation
    user_input = st.session_state.current_input
    memory.append({"role": "user", "content": user_input})

    res = requests.post(
        "http://localhost:11434/api/chat",
        json={"model": "llama3", "messages": memory, "stream": False},
        headers={"Content-Type": "application/json"},
    )

    response = res.json()["message"]["content"]
    memory.append({"role": "assistant", "content": response})
    return response
