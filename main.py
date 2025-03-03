from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from database import execute_query
from query_generator import generate_sql_query
from ai_analyzer import analyze_data
import config
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = FastAPI()

@app.post("/ask")
async def ask_question(query):
    """
    Handles user questions by:
    1. Generating an SQL query from natural language using SQLCoder:7B.
    2. Executing the query on PostgreSQL.
    3. Using AI to analyze the data and generate insights.
    """
    try:
        logging.info(f"Received question: {query}")
        sql_query = generate_sql_query(query, model=config.LLM_MODEL)
        logging.info(f"Generated SQL: {sql_query}")
        
        if not sql_query:
            return {"response": "Could not generate a valid SQL query."}
        
        results = execute_query(sql_query)
        logging.info(f"Query Results: {results}")
        
        if not results:
            return {"response": "No relevant data found."}
        
        response = analyze_data(query, results)
        return response
    except Exception as e:
        logging.error(f"Error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config.HOST, port=config.PORT)



#####################################################################################################################

# import requests
# import psycopg2
# import pandas as pd
# from datetime import datetime, timedelta
# from fastapi import FastAPI, Query
# from statsmodels.tsa.arima.model import ARIMA
# import re

# app = FastAPI()

# DB_PARAMS = {
#     "dbname": "llm_poc",
#     "user": "postgres",
#     "password": "Transflash",
#     "host": "localhost",
#     "port": 5432
# }

# LLAMA_MODEL = "llama3.2:1b"
# OLLAMA_API_URL = "http://localhost:11434/api/generate"

# def call_llama_ollama(prompt: str):
#   """Generate response using Llama via Ollama API"""
#   print(f"📌 Sending request to Ollama: {prompt}")

#   payload = {
#       "model": LLAMA_MODEL,
#       "prompt": f"Extract intent, metric, time range, and condition from this query: '{prompt}'",
#       "stream": False
#   }
  
#   try:
#       response = requests.post(OLLAMA_API_URL, json=payload)
#       response_json = response.json()
#       return response_json.get("response", "Error processing request.")
  
#   except Exception as e:
#       print(f"❌ Ollama Request Error: {e}")
#       return "Error connecting to Ollama."

# def query_postgres(sql_query: str, params: tuple):
#   """Executes SQL queries on PostgreSQL"""
#   print(f"📌 Executing Query: {sql_query} with params {params}")

#   try:
#       conn = psycopg2.connect(**DB_PARAMS)
#       cursor = conn.cursor()
#       cursor.execute(sql_query, params)
#       data = cursor.fetchall()
#       cursor.close()
#       conn.close()
#       return data
  
#   except Exception as e:
#       print(f"❌ PostgreSQL Query Error: {e}")
#       return []

# def extract_query_components(user_query: str):
#   """Extracts metric, time range, and condition using Llama"""
#   llm_response = call_llama_ollama(user_query)
#   print(f"✅ Parsed Query: {llm_response}")

#   # Example Llama response parsing (convert to structured format)
#   extracted_data = {
#       "metric": "cpu",
#       "operation": "max",
#       "time_range": "last 10 days",
#       "condition": "> 50%"
#   }

#   return extracted_data


# def generate_sql_from_query(user_query: str):
#     """Use Llama to generate SQL queries dynamically based on schema context."""
#     schema_context = """
#     The database has a table called `metrics` with the following columns:
#     - id (INT, primary key)
#     - time (TIMESTAMP)
#     - measurement (TEXT) -- e.g., 'cpu', 'memory'
#     - value (FLOAT) -- Numeric value of the metric

#     Convert the following natural language question into a PostgreSQL SQL query.
#     Only return the postgre SQL query without any explanation or formatting. Dont include ```sql ... ``` syntax.
#     """

#     prompt = f"{schema_context}\nUser Question: {user_query}\nSQL Query:"
    
#     payload = {
#         "model": LLAMA_MODEL,
#         "prompt": prompt,
#         "stream": False
#     }

#     try:
#         response = requests.post(OLLAMA_API_URL, json=payload)
#         sql_query = response.json().get("response", "")

#         # 🔹 Remove markdown syntax like ```sql ... ```
#         sql_query = re.sub(r"```sql|```", "", sql_query).strip()
        
#         print(f"✅ Cleaned SQL Query: {sql_query}")
#         return sql_query

#     except Exception as e:
#         print(f"❌ Ollama Request Error: {e}")
#         return "Error generating SQL"


# # def generate_sql_query(parsed_query):
# #     """Generates an SQL query from parsed LLM response"""
# #     metric = parsed_query["metric"]
# #     operation = parsed_query["operation"]
# #     time_range = parsed_query["time_range"]
# #     condition = parsed_query.get("condition")

# #     time_condition = "time >= NOW() - INTERVAL '10 days'"
# #     if "from" in time_range and "to" in time_range:
# #         start_date, end_date = time_range.split(" to ")
# #         time_condition = f"time BETWEEN '{start_date}' AND '{end_date}'"

# #     if operation == "max":
# #         sql = f"SELECT time, value FROM metrics WHERE measurement = %s AND {time_condition} ORDER BY value DESC LIMIT 1;"
# #         return sql, (metric,)

# #     if operation == "count" and condition:
# #         sql = f"SELECT COUNT(*) FROM metrics WHERE measurement = %s AND {time_condition} AND value {condition};"
# #         return sql, (metric,)

# #     return None, None

# def predict_next_week(df):
#   """Predicts future CPU usage using ARIMA"""
#   print("📌 Performing time-series forecasting...")

#   try:
#       df["time"] = pd.to_datetime(df["time"])
#       df.set_index("time", inplace=True)

#       model = ARIMA(df["value"], order=(5,1,0))
#       model_fit = model.fit()
#       forecast = model_fit.forecast(steps=7)

#       print(f"✅ Forecast Result: {forecast.tolist()}")
#       return forecast.tolist()
  
#   except Exception as e:
#       print(f"❌ Forecasting Error: {e}")
#       return []

# @app.get("/chat")
# def chatbot(query: str = Query(..., description="Ask about time-series data")):
#   """Processes user queries"""
#   print(f"\n🔹 Received Query: {query}")


#   # Generate SQL dynamically using Llama
#   sql_query = generate_sql_from_query(query)
#   if "Error" in sql_query:
#       return {"response": "Failed to generate SQL"}

#   # Execute SQL
#   data = query_postgres(sql_query, ())
#   if not data:
#       return {"response": "No relevant data found."}

#   df = pd.DataFrame(data, columns=["time", "value"])
#   # return {"text": "Query processed successfully", "table": df.to_dict(orient="records")}

#   # Perform Forecasting if requested
#   # if "predict" in query.lower():
#   #     prediction = predict_next_week(df)
#   #     return {"prediction": prediction}

#   return {"text": "Query processed successfully", "table": df.to_dict(orient="records")}