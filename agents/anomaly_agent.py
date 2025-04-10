# agents/anomaly_agent.py
def run_anomaly_agent(transactions_path: str) -> str:
    # Run isolation forest on transactions
    from utils.llama3_ollama import ask_llama3
    anomalies = "An unusual $3000 transaction was made on Jan 10."  # Dummy
    return ask_llama3(f"Explain this potential anomaly: {anomalies}")
