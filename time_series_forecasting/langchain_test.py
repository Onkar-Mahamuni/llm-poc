from langchain_community.llms import Ollama
from langchain_core.prompts import PromptTemplate
import json
import datetime

llm = Ollama(model="llama3.2:1b")

def analyze_intent(user_query, schema_description):
    """
    Analyzes the user's intent and extracts relevant information, handling multiple intents.

    Args:
        user_query: The user's natural language query.
        schema_description: A description of the database schema.

    Returns:
        A dictionary containing the extracted information.
    """

    prompt_template = PromptTemplate(
        input_variables=["user_query", "schema_description"],
        template="""
        You are an AI assistant that analyzes user queries related to database data and forecasting, handling multiple intents.

        Database Schema:
        {schema_description}

        User Query:
        {user_query}

        Instructions:
        1.  Determine all user intents:
            -   "data_retrieval": If the user wants raw data.
            -   "forecast": If the user wants a time-series forecast.
            -   "action": If the user wants to perform an action (e.g., scaling).
        2.  Identify the necessary data columns and time range.
        3.  If "forecast" intent is detected, determine the forecast period in days.
        4.  If "action" intent is detected, identify the requested action.
        5.  Return the results only as a JSON object (response should directly be parsable to json) with the following structure:
            {{
                "intents": ["intent1", "intent2", ...],
                "columns": ["column1", "column2", ...],
                "time_range": {{
                    "start_date": "YYYY-MM-DD",
                    "end_date": "YYYY-MM-DD"
                }},
                "forecast_days": integer (if applicable),
                "action": "action_name" (if applicable)
            }}
        6. Start and end dates always should be valid dates. Start date will always be the date of tomorrow.
        7. End date should be the last date of requested forecast.

        JSON Output:
        """,
    )

    chain = prompt_template | llm
    response = chain.invoke({"user_query":user_query, "schema_description":schema_description})

    try:
        data = json.loads(response.strip())
        # Rule based data retrieval.
        if "forecast_days" in data and data["forecast_days"] is not None:
            forecast_days = data["forecast_days"]
            data["time_range"] = calculate_data_range(forecast_days)

        return data
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {response}, Error: {e}")
        return None

def calculate_data_range(forecast_days):
    """
    Calculates the required data range based on the forecast period.
    """
    today = datetime.date.today()
    end_date = today - datetime.timedelta(days=1)
    if forecast_days <= 7:
        start_date = end_date - datetime.timedelta(days=30)
    elif forecast_days <= 30:
        start_date = end_date - datetime.timedelta(days=90)
    else:
        start_date = end_date - datetime.timedelta(days=365) #for longer forecasts, get a years worth of data.
    return {
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
    }

# Example Usage
schema_description = """
Table: cpu_usage
Columns: timestamp (datetime), usage (float)
"""
user_query_1 = "Show me the CPU usage and forecast the next 7 days."
user_query_2 = "Forecast the CPU usage for the next 30 days and scale up if needed."
user_query_3 = "Scale down the instances, and show me the last 90 days of data."

result_1 = analyze_intent(user_query_1, schema_description)
result_2 = analyze_intent(user_query_2, schema_description)
result_3 = analyze_intent(user_query_3, schema_description)

print(f"Result 1: {result_1}")
print(f"Result 2: {result_2}")
print(f"Result 3: {result_3}")