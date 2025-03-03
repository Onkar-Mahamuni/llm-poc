import requests
import config
import logging
import json

def analyze_data(question: str, data: list) -> dict:
    """Uses AI to analyze data, generate insights, and respond with text, tables, or graphs as needed."""
    try:
        logging.info(f"Analyzing data for question: {question}")
        payload = {
            "model": config.ANALYSIS_MODEL,
            "prompt": f"Question: {question}\nData: {json.dumps(data)}\nProvide a detailed, data-backed response:",
            "stream": False
        }
        response = requests.post(config.OLLAMA_URL, json=payload)
        response.raise_for_status()
        analysis = response.json().get("response", "").strip()
        logging.info(f"Generated Analysis: {analysis}")
        return {"response": analysis}
    except Exception as e:
        logging.error(f"AI Analysis Error: {str(e)}")
        return {"response": "Error analyzing data."}
