from stock_sentiment_analysis.master_service.master_agent.agents.price import PriceAgent
from stock_sentiment_analysis.master_service.master_agent.agents.alpha_vantage_agent import AlphaVantageNewsAgent
from cryptography.fernet import Fernet
import pandas as pd
import requests
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'stock_sentiment_analysis', 'master_service')))


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


def run_portfolio_agent_loop(csv_path_enc: str, key: bytes):
    print("\n📊 Entering Stock Portfolio Analyzer")
    print("Reading your portfolio and fetching market insights...")
    
    # 1. Load portfolio
    csv_path = decrypt_user_files(csv_path_enc, "user_1", key)
    df = pd.read_csv(csv_path)
    if df.empty or not all(col in df.columns for col in ["Ticker", "Holding", "Profit percentage"]):
        print("❌ CSV format is invalid or empty.")
        return

    # 2. Fetch data per ticker
    price_agent = PriceAgent()
    news_agent = AlphaVantageNewsAgent()
    portfolio_summary = []

    for _, row in df.iterrows():
        ticker = row["Ticker"]
        holding = row["Holding"]
        profit_pct = row["Profit percentage"]

        data = {
            "ticker": ticker,
            "holding": holding,
            "profit_pct": profit_pct
        }

        # Add price and news
        data = price_agent.run(data)
        data = news_agent.run(data)
        portfolio_summary.append(data)

    # 3. Build prompt for LLaMA 3
    system_prompt = """
You are a financial portfolio advisor. Your job is to analyze the user's holdings based on current prices, profit %, and recent news.
The dataset contains the following information:
- Ticker: ticker of the stock
- Holding: percentage of the portfolio that contains the stock with the particular ticker
- Profit percentage: gain or loss of the project after buying the stock with particular ticker

Give:
- Suggestions on whether to hold/sell
- Risky or overperforming stocks
- Portfolio balance tips
- Mention if any stocks are overexposed or trending negatively

In the end please add the following statement in comments "Investments in the stock market are subject to market risks. Please perform your own research before investing in the market!"

"""

    analysis_input = "### User Portfolio:\n"
    for stock in portfolio_summary:
        analysis_input += f"""
{stock['ticker']}:
- Holding: {stock['holding']}
- Profit %: {stock['profit_pct']}%
- Price: ${stock.get('price', 'N/A')}
- Recent News:
"""
        for article in stock.get("sources", [])[:2]:
            analysis_input += f"    • {article['title']} ({article['sentiment_label']})\n"

    # 4. Begin interactive loop
    conversation = [{"role": "system", "content": system_prompt}, {"role": "user", "content": analysis_input}]

    res = requests.post(
        "http://localhost:11434/api/chat",
        json={"model": "llama3", "messages": conversation, "stream": False},
        headers={"Content-Type": "application/json"}
    )

    assistant_response = res.json()["message"]["content"]
    print(f"\n💬 {assistant_response}\n")
    conversation.append({"role": "assistant", "content": assistant_response})

    # Multi-turn loop
    while True:
        user_input = input("PortfolioAgent> ").strip()
        if user_input.lower() in ["exit", "quit", "back"]:
            print("↩️ Returning to FinFluent main menu.\n")
            break

        conversation.append({"role": "user", "content": user_input})
        res = requests.post(
            "http://localhost:11434/api/chat",
            json={"model": "llama3", "messages": conversation, "stream": False},
            headers={"Content-Type": "application/json"}
        )

        assistant_response = res.json()["message"]["content"]
        conversation.append({"role": "assistant", "content": assistant_response})
        print(f"\n💬 {assistant_response}\n")
