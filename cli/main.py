# cli/main.py
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from controller.central_controller import route_user_query
from agents.budget_agent import run_budget_agent
from agents.anomaly_agent import run_anomaly_agent
from agents.stock_agent import run_stock_agent


def main():
    print("📊 Welcome to FinFluent CLI!")
    print("Ask about your budget, spending anomalies, or a stock like AAPL.")
    print("Type 'exit' to quit.\n")

    while True:
        user_input = input("FinFluent> ").strip()
        if user_input.lower() in ["exit", "quit"]:
            print("Goodbye 👋")
            break

        route = route_user_query(user_input)
        print(f"[Controller] Routed to agent: {route}")

        if route == "budget":
            response = run_budget_agent("data/sample_transactions.csv")
        elif route == "anomaly":
            response = run_anomaly_agent("data/sample_transactions.csv")
        elif route == "stock":
            # crude ticker detection (refine later)
            ticker = next(
                (
                    word
                    for word in user_input.split()
                    if word.isupper() and 2 <= len(word) <= 5
                ),
                "AAPL",
            )
            response = run_stock_agent(ticker)
        else:
            response = "Sorry, I didn't understand. Please ask about your budget, anomalies, or stocks."

        print(f"\n{response}\n")


if __name__ == "__main__":
    main()
