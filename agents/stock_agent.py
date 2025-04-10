# agents/stock_agent.py
import subprocess
import time


def run_stock_agent(ticker: str) -> str:
    try:
        # Step 1: Ensure services are running (adjusted paths)
        subprocess.run(["bash", "stock_sentiment_analysis/llm_service/script.sh"], check=True)
        subprocess.run(["bash", "stock_sentiment_analysis/master_service/script.sh"], check=True)
        time.sleep(5)
        # Step 2: Run stock analysis
        output = subprocess.check_output(
            ["python3", "stock_sentiment_analysis/run_analysis.py", "--ticker", ticker],
            stderr=subprocess.STDOUT
        )
        return output.decode("utf-8")
    except subprocess.CalledProcessError as e:
        return f"Stock analysis failed.\nCommand: {e.cmd}\nReturn code: {e.returncode}\nOutput: {e.output.decode('utf-8') if e.output else 'No output'}"
