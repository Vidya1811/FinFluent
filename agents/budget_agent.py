# agents/budget_agent.py
def run_budget_agent(transactions_path: str) -> str:
    # Load CSV, run SARIMA, generate summary via LLM (call LLaMA 3)
    from utils.llama3_ollama import ask_llama3
    forecast_summary = "You're projected to spend $2500 next month based on historical trends."  # Dummy for now
    return ask_llama3(f"Explain this financial forecast: {forecast_summary}")
