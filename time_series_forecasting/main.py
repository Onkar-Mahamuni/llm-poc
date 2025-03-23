from fastapi import FastAPI, UploadFile, File
import pandas as pd
from prophet import Prophet
import matplotlib.pyplot as plt
import io
import ollama

model = "llama3.2:1b"

app = FastAPI()

def analyze_forecast(data: pd.DataFrame):
    data["ds"] = pd.to_datetime(data["DATE"])
    data["y"] = data["IPG2211A2N"]  

    model = Prophet()
    model.fit(data[["ds", "y"]])

    future = model.make_future_dataframe(periods=30, freq='D')
    forecast = model.predict(future)

    # Compute trend (last 30 days)
    recent_trend = forecast["trend"].iloc[-1] - forecast["trend"].iloc[-30]

    if recent_trend > 0:
        trend_analysis = "increasing"
        action = "Scale up resources to handle expected demand."
    elif recent_trend < 0:
        trend_analysis = "decreasing"
        action = "Optimize costs by reducing resources."
    else:
        trend_analysis = "stable"
        action = "No immediate action required. Monitor the trend."

    # Generate plot
    fig = model.plot(forecast)
    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)

    return forecast.tail(5).to_dict(orient="records"), trend_analysis, action, buf

def generate_report(forecast_data, trend, action):
    prompt = f"""
    You are an AI assistant analyzing forecast data. Forecasted data is of vm resource usage.
    
    - Trend: {trend}
    - Suggested Action: {action}
    - Forecast Data: {forecast_data}

    Generate a professional report explaining the trend and why the action is recommended.
    """

    response = ollama.chat(model=model, messages=[{"role": "user", "content": prompt}])
    return response['message']['content']

@app.post("/forecast")
async def forecast_csv():
    df = pd.read_csv("C:\\Users\\onkar\\Downloads\\Electric_Production.csv")
    forecast_data, trend, action, chart = analyze_forecast(df)

    report = generate_report(forecast_data, trend, action)

    return {
        "forecast": forecast_data,
        "trend": trend,
        "suggested_action": action,
        "report": report
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)


# import pandas as pd
# import numpy as np
# import matplotlib.pyplot as plt
# import seaborn as sns

# import xgboost as xgb
# color_pal = sns.color_palette()

# df = pd.read_csv("C:\\Users\\onkar\\Downloads\\Electric_Production.csv")
# df = df.set_index('DATE')

# df.plot(figsize=(14,6), title='Electric Production', color=color_pal[0])
# df.index = pd.to_datetime(df.index)

# plt.show()