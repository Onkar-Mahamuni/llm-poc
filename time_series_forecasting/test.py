from fastapi import FastAPI, Depends
from pydantic import BaseModel
import asyncpg
import pandas as pd
from prophet import Prophet
import requests

app = FastAPI()
DATABASE_URL = "postgresql://user:password@localhost:5432/metrics_db"
OLLAMA_API_URL = "http://localhost:11434/v1/chat"

async def get_db():
    return await asyncpg.create_pool(DATABASE_URL)

class QueryRequest(BaseModel):
    query: str

async def fetch_data(db, query):
    return await db.fetch(query)

async def forecast_cpu_usage(db):
    records = await fetch_data(db, "SELECT timestamp, cpu_usage FROM metrics")
    df = pd.DataFrame(records, columns=['timestamp', 'cpu_usage'])
    df.rename(columns={'timestamp': 'ds', 'cpu_usage': 'y'}, inplace=True)
    model = Prophet()
    model.fit(df)
    future = model.make_future_dataframe(periods=7)
    forecast = model.predict(future)
    return forecast[['ds', 'yhat']].to_dict(orient='records')

@app.post("/query")
async def process_query(query: str, db=Depends(get_db)):
    response = requests.post(OLLAMA_API_URL, json={"message": query})
    intent = response.json().get("intent")
    
    if intent == "fetch_data":
        sql_query = response.json().get("query")
        records = await fetch_data(db, sql_query)
        return [{"timestamp": r["timestamp"], "cpu_usage": r["cpu_usage"], "memory_usage": r["memory_usage"]} for r in records]
    
    elif intent == "forecast":
        forecast_data = await forecast_cpu_usage(db)
        return {"forecast": forecast_data}
    
    elif intent == "scale":
        forecast_data = await forecast_cpu_usage(db)
        return {"action": "Scaling up VM based on forecasted demand.", "forecast": forecast_data}
    
    return {"error": "Unknown intent"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)