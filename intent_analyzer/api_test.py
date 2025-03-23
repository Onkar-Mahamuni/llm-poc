import ollama
import asyncpg
import pandas as pd
from prophet import Prophet
import asyncio
from datetime import date, datetime
import json
import matplotlib.pyplot as plt
from fastapi import FastAPI, WebSocket, BackgroundTasks, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

todays_date = "2025-01-11"
intent_model = "intent-analyzer3"
summary_model = "llama3.2:1b"

# Placeholder scale functions
def scale_up():
    print("Scaling up VMs...")

def scale_down():
    print("Scaling down VMs...")

## Format
def analyze_and_format_results(data, user_query, intent):
    """
    Analyze forecast or retrieved data and format results.
    """
    prompt = f"""
    Given the following resource usage data, analyze the trend and suggest whether to scale up, scale down, or do nothing.
    Format the response as a JSON object with keys: summary, action, graph_data, and markdown_table.
    
    Data: {data}
    Query: {user_query}
    Intent: {intent}
    """
    
    response = ollama.chat(model=summary_model, messages=[{"role": "user", "content": prompt}])
    result = response['message']['content']
    
    return result

# Function to detect intent
def detect_intent(query):
    messages = [{"role": "user", "content": f"{query}, Today's Date: {todays_date}"}] 
    response = ollama.chat(model=intent_model, messages=messages)
    # Extract content from the response
    raw_content = response.message.content.strip("")  # Remove backticks if any

    try:
        intent_data = json.loads(raw_content)  # Parse JSON
        return intent_data
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        return None  # Handle the error gracefully

# Async function to fetch data from PostgreSQL
async def fetch_data(start_date, end_date):
    start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
    end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
    conn = await asyncpg.connect(database="llm_poc", user="postgres", password="Transflash", host="localhost", port="5432")
    query = """
        SELECT time AS timestamp, value AS cpu_usage FROM public.metrics
        WHERE measurement = 'cpu' AND time BETWEEN $1 AND $2
    """
    rows = await conn.fetch(query, start_date, end_date)
    await conn.close()
    df = pd.DataFrame(rows, columns=["timestamp", "cpu_usage"])
    print(f"Fetched data: {df.tail()}")
    return df

# Function to forecast resource usage
def forecast_usage(df, forecast_days):
    df['cap'] = 100
    df['floor'] = 2
    df = df[['timestamp', 'cpu_usage', 'cap', 'floor']]
    df.rename(columns={"timestamp": "ds", "cpu_usage": "y"}, inplace=True)
    model = Prophet(
        # growth='linear',
        # seasonality_mode='additive',  # Adjusts seasonality impact better
        # changepoint_prior_scale=0.2  # Adjust trend flexibility
    )

    model.fit(df)
    future = model.make_future_dataframe(periods=24*forecast_days, freq='H')

    # Add cap and floor to future data
    future['cap'] = 100
    future['floor'] = 2

    forecast = model.predict(future)
    return forecast

# Function to analyze forecast and suggest actions
def analyze_forecast(forecast):
    last_forecast = forecast.iloc[-1]["yhat"]
    if last_forecast > 80:  # Assuming 80% CPU usage as threshold
        return "scale_up"
    elif last_forecast < 30:
        return "scale_down"
    return "keep_same"

# Function to visualize data
def visualize_forecast(df):
    # Define the split point for real vs forecast data
    split_date = pd.Timestamp(todays_date)  # Change this to your actual forecast start date
    df_past = df[df["ds"] < split_date]  # Real past data
    df_future = df[df["ds"] >= split_date]  # Forecasted data

    # Plot real past data (solid line)
    plt.figure(figsize=(12, 6))
    plt.plot(df_past["ds"], df_past["yhat"], label="Real Data", color="blue", linewidth=2)

    # Plot forecasted data (dotted line)
    plt.plot(df_future["ds"], df_future["yhat"], label="Forecast", color="red", linestyle="dotted", linewidth=2)

    # Formatting the plot
    plt.xlabel("Date")
    plt.ylabel("Predicted Value (yhat)")
    plt.title("Real vs Forecasted CPU Utilization")
    plt.legend()
    plt.xticks(rotation=45)
    plt.grid(True)

    # Show plot
    plt.show()

# Main function to process queries
async def process_query(query):
    intent_data = detect_intent(query)
    print(f"fetched intent: {intent_data}")
    if "data_retrieval" in intent_data["intent"]:
        data = await fetch_data(intent_data["start_date"], intent_data["end_date"])
    else:
        data = None
    print(f"fetched data: {data}")
    if "forecast" in intent_data["intent"] and data is not None:
        forecast = forecast_usage(data, intent_data["forecast_days"])
    else:
        forecast = None
    print(f"forecast: {forecast}")
    # visualize_forecast(forecast)
    analyzed_resp = analyze_and_format_results(forecast, query, intent_data)
    # if "action" in intent_data["intent"]:
    #     suggested_action = analyze_forecast(forecast)
    #     print(f"Suggested action: {suggested_action}")
    #     confirmation = input("Confirm action? (yes/no): ")
    #     if confirmation.lower() == "yes":
    #         if suggested_action == "scale_up":
    #             scale_up()
    #         elif suggested_action == "scale_down":
    #             scale_down()
    visualize_forecast(forecast)
    return {"intent": intent_data, "forecast": forecast, "analyzed_resp": analyzed_resp}

# Example usage
# query = "Give me cpu usage from 31st Nov 2024 to 15th Jan 2025"
query = "Forecast cpu usage of next 1 month"
result = asyncio.run(process_query(query))
print(result)

# app = FastAPI()

# # Allow WebSocket connections from any origin
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# connections = set()

# async def send_status(status: str):
#     message = json.dumps({"status": status})
#     for conn in connections:
#         await conn.send_text(message)

# @app.websocket("/ws")
# async def websocket_endpoint(websocket: WebSocket):
#     await websocket.accept()
#     connections.add(websocket)
#     for line in ['line']:
#         await websocket.send_text(line)
#     try:
#         while True:
#             data = await websocket.receive_text()
#             print(f"Received: {data}")
#     except WebSocketDisconnect:
#         print("WebSocket disconnected")
#     except Exception as e:
#         print(f"WebSocket error: {e}")
#     finally:
#         connections.remove(websocket)


# class QueryRequest(BaseModel):
#     query: str

# @app.post("/query")
# async def handle_query(request: QueryRequest):
#     # query = request.get("query")
#     # background_tasks.add_task(process_query_with_status, query)
#     # return {"message": "Processing started"}
#     resp = process_query(request.query)
#     return resp

# async def process_query_with_status(query):   
#     await send_status("Thinking...")
#     intent_data = detect_intent(query)
#     await send_status("Fetching historical data...")
    
#     if "data_retrieval" in intent_data["intent"]:
#         data = await fetch_data(intent_data["start_date"], intent_data["end_date"])
#     else:
#         data = None
    
#     await send_status("Forecasting...")
#     if "forecast" in intent_data["intent"] and data is not None:
#         forecast = forecast_usage(data, intent_data["forecast_days"])
#     else:
#         forecast = None
    
#     await send_status("Analyzing results...")
#     analyzed_resp = analyze_and_format_results(forecast, query, intent_data)
    
#     await send_status("Done")
#     return {"intent": intent_data, "forecast": forecast, "analyzed_resp": analyzed_resp}

# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=8000)