# cli/main.py
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from cryptography.fernet import Fernet
from controller.central_controller import route_user_query
from agents.budget_agent import run_budget_agent_loop
from agents.anomaly_agent import run_anomaly_agent_loop
from agents.stock_agent import run_stock_agent_loop
from agents.portfolio_agent import run_portfolio_agent_loop


desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
fldr_name = "stock_market"
file_path = "FinFluent\\user_data\\"  # add slash at end of file path


def encryption_agent(file_name: str, user_name: str, key: bytes) -> str:
    fldr_name = "stock_market"
    with open("secret.key", "wb") as key_file:
        key_file.write(key)

    cipher = Fernet(key)

    file_path = "FinFluent\\user_data\\"  # add slash at end of file path
    file_name = file_name
    user_name = user_name
    orig_path = os.path.join(desktop_path, fldr_name, file_path, user_name, file_name)
    encrypted_file_path = "FinFluent\\encrypted_files\\"  # add slash at end of file path
    encryp_path = os.path.join(desktop_path, fldr_name, encrypted_file_path, user_name, file_name)

    # Encrypt the CSV file
    with open(orig_path, "rb") as f:
        data = f.read()

    encrypted_data = cipher.encrypt(data)

    with open(encryp_path, "wb") as f:
        f.write(encrypted_data)       
    return encryp_path


def main():
    print("""Welcome to FinFluent, your personal, AI-powered financial advisor!
Here's what I can do:
🔮 Budget Forecasting — See where your money is headed next month
🚨 Anomaly Detection — Spot unusual or suspicious transactions
📈 Stock Sentiment — Get the latest trends and news on your favorite stocks
How can I help you today?
""")
    print("Type 'exit' to quit.\n")

    key = Fernet.generate_key()
    encrypted_data_5 = encryption_agent("5_year.csv", "user_1", key)
    encrypted_data_portfolio = encryption_agent("portfolio.csv", "user_1", key)
    # print(encryption_agent("5_year.csv", "user_1", key))
    while True:
        user_input = input("FinFluent> ").strip()
        if user_input.lower() in ["exit", "quit"]:
            print("Goodbye 👋")
            break

        route = route_user_query(user_input)
        print(f"Connecting you to a specialist: {route}")

        if route == "budget":
            key = Fernet.generate_key()
            run_budget_agent_loop(encrypted_data_5, key)
            response = None
        elif route == "anomaly":
            key = Fernet.generate_key()
            run_anomaly_agent_loop("encrypted_data_5", key)
            response = None
        elif route == "stock":
            run_stock_agent_loop()
            response = None  
        elif route == "portfolio":
            key = Fernet.generate_key()
            run_portfolio_agent_loop(encrypted_data_portfolio, key)
            response = None

        else:
            response = """Sorry, I didn't understand. Please ask about your 
            budget, anomalies, stocks, or portfolio analysis."""

        if response:
            print(f"\n{response}\n")


if __name__ == "__main__":
    main()
