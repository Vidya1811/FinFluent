from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
import requests
import pandas as pd
import os
from glob import glob
from statsmodels.tsa.statespace.sarimax import SARIMAX
from pandas.tseries.offsets import MonthEnd
from sklearn.metrics import mean_absolute_error, mean_squared_error
from pmdarima import auto_arima
from prophet import Prophet
import numpy as np
from rouge_score import rouge_scorer


reference_answers = {
    "which category is the highest spender?":
        "Based on the predicted spending for next month, the highest spender is Grocery shopping, with an amount of $8041.05, which accounts for approximately 80% of the total predicted spending.",

    "where can I save more money next month?":
        "A great question! Based on your predicted spending, it looks like you're allocating a significant chunk of your income to Grocery shopping. Considering that groceries are an essential expense, we'll focus on cost-saving strategies in this category.\n\nHere are some data-driven suggestions to help you save more money next month:\n\n1. **Meal planning and prep**: Plan your meals for the week, and consider meal prepping to reduce food waste and save time. This can help you avoid last-minute takeouts or expensive dining out.\n2. **Grocery list optimization**: Make a detailed grocery list before heading to the store. Stick to your list and avoid impulse buys, which can account for up to 30% of your total grocery spend.\n3. **Shop sales and stock up**: Check weekly ads for your local stores and plan your shopping trips around the items on sale. Stock up on non-perishable items when they're at their cheapest.\n4. **Coupons and cashback apps**: Take advantage of digital coupons, cashback apps (like Ibotta or Fetch Rewards), and loyalty programs to earn rewards or discounts on your grocery purchases.\n5. **Shop at discount stores or use a grocery delivery service**: Consider shopping at discount stores or using a grocery delivery service like Instacart or Shipt, which can help you save time and money.\n\nBy implementing these strategies, you may be able to reduce your Grocery shopping expenses by 10-15%. This could translate to an additional $804.10-$1206.75 in savings next month!\n\nRemember, small changes can add up over time. Start with one or two adjustments and see how they work for you before making more significant changes.",

    "am I overspending on utilities?":
        "Let's take a closer look at your predicted spending on Utilities: $304.53.\n\nWhile it's difficult to pinpoint an exact 'overspending' threshold without knowing your overall household income and expenses, we can assess whether this amount seems reasonable compared to industry norms or your peers.\n\nAccording to the U.S. Energy Information Administration (EIA), the average monthly utility bill for a household in the United States is around $150-$200. However, these figures can vary significantly depending on factors like:\n\n1. Location: Climate, population density, and local energy prices all impact utility bills.\n2. Household size: Larger households tend to consume more energy and water.\n3. Energy efficiency: The age and efficiency of appliances, insulation, and windows affect your utility costs.\n\nBased on these factors, it's possible that your $304.53 monthly Utilities expense might be slightly higher than average, depending on your specific situation.\n\nTo better understand this expense, consider the following:\n\n1. **Review your bill**: Take a closer look at your utility bills to see if there are any unusual spikes or patterns.\n2. **Check for energy efficiency opportunities**: Assess your home's energy efficiency and identify areas where you can make improvements, such as upgrading appliances, adding insulation, or installing smart thermostats.\n3. **Negotiate with providers**: Reach out to your utility providers (electricity, gas, water) to see if they offer any discounts, promotions, or bundled plans that could help reduce your costs.\n\nIf you're concerned about overspending on Utilities, consider setting a goal to reduce this expense by 5-10% over the next few months. This might involve implementing energy-saving measures, adjusting your usage habits, or exploring alternative utility providers in your area.\n\nRemember, small changes can add up over time. Start with one or two adjustments and see how they work for you before making more significant changes.",

    "what are the risky spending patterns?":
        "Based on your predicted spending for next month, I've identified a few potential areas of concern:\n\n1. **Entertainment: $642.58**: While it's okay to indulge in some entertainment expenses, this amount is relatively high and might be a significant chunk of your overall budget. Consider setting a specific entertainment budget or finding free or low-cost alternatives.\n2. **Restaurants: $765.45**: Dining out regularly can add up quickly. This expense accounts for nearly 8'%' of your predicted spending. Try to balance this by cooking at home more often and allocating some of these funds towards groceries or meal prep.\n3. **Travel expenses: $265.24**: If you're planning a significant trip, this amount might be manageable. However, if you're not planning a trip, it's essential to reassess your travel habits and consider alternative modes of transportation or accommodations.\n\nTo mitigate these risks:\n\n1. **Set budgets**: Establish specific budgets for each category to ensure you're staying within reasonable limits.\n2. **Prioritize needs over wants**: Distinguish between essential expenses (e.g., groceries) and discretionary spending (e.g., entertainment).\n3. **Find free alternatives**: Explore low-cost or free activities, such as hiking, game nights, or potluck dinners, instead of relying on expensive alternatives.\n4. **Review and adjust**: Regularly review your spending habits and adjust as needed to ensure you're staying within your means.\n\nRemember, it's essential to strike a balance between enjoying life and being mindful of your expenses. By identifying areas for improvement and implementing strategies to reduce unnecessary spending, you can create a more sustainable financial plan for the future."
}


# Load all CSV files in the folder
folder_path = "C:\\Users\\aksha\\Downloads\\FinFluent-main\\FinFluent-main\\generated_data"
all_files = glob(os.path.join(folder_path, "*.csv"))

# Combine all datasets into one DataFrame
df_list = [pd.read_csv(file, parse_dates=["Date"]) for file in all_files]
df = pd.concat(df_list, ignore_index=True)

# Filter only debit categories
# Filter only debit categories used in data generation
debit_categories = {
    "Shopping",
    "Entertainment",
    "Restaurants",
    "Grocery shopping",
    "Travel expenses",
    "Mortgage & Rent",
    "Utilities"
}


df = df[df["Category"].isin(debit_categories)]
df["Amount"] = df["Amount"].abs()
df["Month"] = (df["Date"] + MonthEnd(0)).dt.to_period("M").dt.to_timestamp()
monthly_spending = df.groupby(["Month", "Category"])["Amount"].sum().unstack().fillna(0)

# Add month dummies
monthly_spending["Month_Num"] = monthly_spending.index.month
month_dummies = pd.get_dummies(monthly_spending["Month_Num"], prefix="month", drop_first=True)
monthly_spending_exog = monthly_spending.drop(columns=["Month_Num"])
monthly_exog = month_dummies
monthly_spending_exog.index = pd.date_range(start=monthly_spending_exog.index.min(), periods=len(monthly_spending_exog), freq="MS")

train_size = int(len(monthly_spending_exog) * 0.8)
results = {}
future_spending = {}

threshold_mape = 25

print("\n--- Hybrid Forecasting: Evaluate & Forecast with Best Model ---\n")
for category in monthly_spending_exog.columns:
    full_series = monthly_spending_exog[category]

    if full_series.std() < 1e-3 or full_series.sum() == 0:
        print(f"Skipping {category}: no variation or data.\n")
        continue

    train_data = full_series[:train_size]
    test_data = full_series[train_size:]
    train_exog = monthly_exog[:train_size]
    test_exog = monthly_exog[train_size:]

    try:
        model = auto_arima(
            train_data,
            exogenous=train_exog,
            seasonal=True,
            m=12,
            suppress_warnings=True,
            error_action="ignore",
            stepwise=True,
        )
        forecast = model.predict(n_periods=len(test_data), exogenous=test_exog)
        mae = mean_absolute_error(test_data, forecast)
        rmse = np.sqrt(mean_squared_error(test_data, forecast))
        mape = np.mean(np.abs((test_data - forecast) / test_data)) * 100

        print(f"{category}")
        print(f"  MAE:  {mae:.2f}")
        print(f"  RMSE: {rmse:.2f}")
        print(f"  MAPE: {mape:.2f}%")

        if mape > threshold_mape:
            print("  🔁 Switching to Prophet (High MAPE)\n")
            df_prophet = pd.DataFrame({"ds": full_series.index, "y": full_series.values})
            model_p = Prophet(seasonality_mode='multiplicative')
            model_p.fit(df_prophet)
            future_df = model_p.make_future_dataframe(periods=1, freq="MS")
            forecast_df = model_p.predict(future_df)
            yhat = forecast_df.iloc[-(len(test_data)+1):-1]["yhat"].values
            ytrue = test_data.values
            mae = mean_absolute_error(ytrue, yhat)
            rmse = np.sqrt(mean_squared_error(ytrue, yhat))
            mape = np.mean(np.abs((ytrue - yhat) / ytrue)) * 100
            print(f"  Prophet MAE:  {mae:.2f}")
            print(f"  Prophet RMSE: {rmse:.2f}")
            print(f"  Prophet MAPE: {mape:.2f}%\n")
            results[category] = {"MAE": mae, "RMSE": rmse, "MAPE": mape}
            future_spending[category] = forecast_df.iloc[-1]["yhat"]
        else:
            last_exog = monthly_exog.iloc[[-1]].values
            next_forecast = model.predict(n_periods=1, exogenous=last_exog)
            future_spending[category] = next_forecast[0]
            results[category] = {"MAE": mae, "RMSE": rmse, "MAPE": mape}

    except Exception as e:
        print(f"SARIMAX failed for {category}: {e}")
        try:
            print("  ➤ Falling back to Prophet.\n")
            df_prophet = pd.DataFrame({"ds": full_series.index, "y": full_series.values})
            model_p = Prophet(seasonality_mode='multiplicative')
            model_p.fit(df_prophet)
            future_df = model_p.make_future_dataframe(periods=1, freq="MS")
            forecast_df = model_p.predict(future_df)
            yhat = forecast_df.iloc[-(len(test_data)+1):-1]["yhat"].values
            ytrue = test_data.values
            mae = mean_absolute_error(ytrue, yhat)
            rmse = np.sqrt(mean_squared_error(ytrue, yhat))
            mape = np.mean(np.abs((ytrue - yhat) / ytrue)) * 100
            print(f"  Prophet MAE:  {mae:.2f}")
            print(f"  Prophet RMSE: {rmse:.2f}")
            print(f"  Prophet MAPE: {mape:.2f}%\n")
            results[category] = {"MAE": mae, "RMSE": rmse, "MAPE": mape}
            future_spending[category] = forecast_df.iloc[-1]["yhat"]
        except Exception as p_e:
            print(f"  Prophet also failed: {p_e}")

# ----- Build AI Prompt for Forecast Explanation -----
forecast_text = "You are given information on a user's predicted spending for next month:\n"
for category, amount in future_spending.items():
    forecast_text += f"{category}: ${amount:.2f}\n"

monthly_salary = 10000  # or pull from your data dynamically

system_prompt = f"""
You are an AI-powered Financial Advisor. Your job is to provide accurate, data-driven financial guidance.

## User Information
- Monthly Salary: ${monthly_salary:.2f}
- Predicted Spending for Next Month:
{forecast_text}

## Instructions
1. Be Specific & Data-Driven
2. Provide Cost-Saving Strategies
3. Warn About Potential Issues
"""


# ----- LLaMA 3 Local Chatbot Integration -----
url = "http://localhost:11434/api/chat"

def llama3(conversation_history):
    data = {
        "model": "llama3",
        "messages": conversation_history,
        "stream": False,
    }
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, headers=headers, json=data)
    return response.json()["message"]["content"]

conversation_history = [{"role": "system", "content": system_prompt}]

print("\nWelcome to your personal AI financial advisor.")
print("You can ask questions about your forecast.\n[Type 'exit' to end the conversation]\n")

while True:
    user_prompt = input("You: ")
    if user_prompt.lower() == "exit":
        print("Goodbye!")
        break

    conversation_history.append({"role": "user", "content": user_prompt})
    response = llama3(conversation_history)
    conversation_history.append({"role": "assistant", "content": response})
    print(f"FinFluent: {response}")

# ----- BLEU Evaluation -----


    ref_text = reference_answers.get(user_prompt, None)
    if ref_text:
        reference = [ref_text.split()]
        hypothesis = response.split()
        smoothie = SmoothingFunction().method4
        bleu = sentence_bleu(reference, hypothesis, smoothing_function=smoothie)
        print(f" BLEU Score: {bleu:.4f}")
    else:
        print(" No reference available for BLEU evaluation.")


# ----- ROUGE Evaluation -----
    scorer = rouge_scorer.RougeScorer(["rouge1", "rougeL"], use_stemmer=True)

    if ref_text:
        rouge_scores = scorer.score(ref_text, response)
        print(f"🔴 ROUGE-1 ➜ Precision: {rouge_scores['rouge1'].precision:.4f}, Recall: {rouge_scores['rouge1'].recall:.4f}, F1: {rouge_scores['rouge1'].fmeasure:.4f}")
        print(f"🔴 ROUGE-L ➜ Precision: {rouge_scores['rougeL'].precision:.4f}, Recall: {rouge_scores['rougeL'].recall:.4f}, F1: {rouge_scores['rougeL'].fmeasure:.4f}")




# ----- LLM Response Evaluation Block -----
import re


def evaluate_llm_response(response_text, forecast_dict, salary):
    overspend_categories = {cat: amt for cat, amt in forecast_dict.items() if amt > 0.3 * salary}
    mentioned = []
    accurate_percentages = 0
    suggestion_keywords = ["cut back", "reduce", "save", "reallocate", "budget", "limit"]

    # Check if each overspend category is mentioned
    for cat in overspend_categories:
        if cat.lower() in response_text.lower():
            mentioned.append(cat)

    # Regex-based percentage checking
    percent_matches = re.findall(r"(\w+)[:\s]+\$?([0-9]+(?:\.[0-9]+)?)\s*\(?([0-9]{1,3})%\)?", response_text)
    for cat, val, pct in percent_matches:
        cat_clean = cat.strip().lower()
        if cat_clean in [c.lower() for c in forecast_dict.keys()]:
            try:
                actual_pct = (forecast_dict[cat] / salary) * 100
                if abs(actual_pct - float(pct)) < 5:
                    accurate_percentages += 1
            except:
                continue

    # Check for suggestion keywords
    gave_advice = any(keyword in response_text.lower() for keyword in suggestion_keywords)

    return {
        "overspending_mentioned": mentioned,
        "correct_percent_mentions": accurate_percentages,
        "gave_actionable_advice": gave_advice
    }

# Example usage:
print("\n--- LLM Response Evaluation ---")
llm_response = response  # from the chatbot loop
eval_metrics = evaluate_llm_response(llm_response, future_spending, monthly_salary)

print(f"✔️ Categories correctly flagged as overspending: {eval_metrics['overspending_mentioned']}")
print(f"✔️ Number of accurate % mentions: {eval_metrics['correct_percent_mentions']}")
print(f"✔️ Actionable advice given? {'✅ Yes' if eval_metrics['gave_actionable_advice'] else '❌ No'}")
