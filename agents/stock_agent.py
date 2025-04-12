# agents/stock_agent.py
import subprocess
import time
import requests


# def run_stock_agent(ticker: str) -> str:
#     try:
#         # Step 1: Ensure services are running (adjusted paths)
#         subprocess.run(["bash", "stock_sentiment_analysis/llm_service/script.sh"], check=True)
#         subprocess.run(["bash", "stock_sentiment_analysis/master_service/script.sh"], check=True)
#         time.sleep(5)
#         # Step 2: Run stock analysis
#         output = subprocess.check_output(
#             ["python3", "stock_sentiment_analysis/run_analysis.py", "--ticker", ticker],
#             stderr=subprocess.STDOUT
#         )
#         return output.decode("utf-8")
#     except subprocess.CalledProcessError as e:
#         return f"Stock analysis failed.\nCommand: {e.cmd}\nReturn code: {e.returncode}\nOutput: {e.output.decode('utf-8') if e.output else 'No output'}"


def run_stock_agent_loop():
    print("\n📈 Entering Stock Sentiment Mode")
    print("Ask about any stock ticker (e.g., TSLA, AAPL, NVDA).")
    print("Type 'exit' to return to the main FinFluent menu.\n")

    # Start services once at the beginning
    subprocess.Popen(["bash", "stock_sentiment_analysis/llm_service/script.sh"])
    subprocess.Popen(["bash", "stock_sentiment_analysis/master_service/script.sh"])
    time.sleep(5)  # Let services start

    while True:
        user_input = input("StockAgent> ").strip()
        if user_input.lower() in ["exit", "quit", "back"]:
            print("↩️ Returning to FinFluent main menu.\n")
            break

        # crude ticker extraction
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
                stderr=subprocess.STDOUT
            )
            print(output.decode("utf-8"))
        except subprocess.CalledProcessError as e:
            print("❌ Stock analysis failed.")
            print(f"Command: {e.cmd}")
            print(f"Output:\n{e.output.decode('utf-8') if e.output else 'No output'}")
