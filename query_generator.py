import requests
import config
import logging

def generate_sql_query(question: str, model=config.LLM_MODEL) -> str:
    """Generates an SQL query from a natural language question using the local Ollama API with context."""
    try:
        logging.info(f"Generating SQL for question: {question}")

        payload = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": "The database has a table called `metrics` with the following columns: id (INT, primary key), time (TIMESTAMP), measurement (TEXT) -- e.g., 'cpu', 'memory', value (FLOAT) -- Numeric value of the metric. Convert the user-provided natural language question into a PostgreSQL SQL query."
                },
                {
                    "role": "user",
                    "content": question
                }
            ],
            "stream": False
        }

        response = requests.post(config.OLLAMA_URL, json=payload)
        response.raise_for_status()
        sql_query = response.json().get("response", "").strip()
        
        # Extract only the SQL query
        # sql_query = extract_sql(sql_query)
        
        logging.info(f"Final Cleaned SQL: {sql_query}")
        return sql_query
    except Exception as e:
        logging.error(f"Query Generation Error: {str(e)}")
        return ""




# # query_generator.py
# import requests
# import re
# from config import OLLAMA_API_URL

# LLAMA_MODEL = "llama3.2:1b"

# def generate_sql_from_query(user_query: str):
#     """Use Llama to generate SQL queries dynamically based on schema context."""
#     schema_context = """
#     The database has a table called `metrics` with the following columns:
#     - id (INT, primary key)
#     - time (TIMESTAMP)
#     - measurement (TEXT) -- e.g., 'cpu', 'memory'
#     - value (FLOAT) -- Numeric value of the metric

#     Convert the following natural language question into a PostgreSQL SQL query.
#     Return ONLY the SQL query without any explanation or formatting.

#     User Question: {user_query}
#     SQL Query:
#     """

#     payload = {
#         "model": LLAMA_MODEL,
#         "prompt": schema_context,
#         "stream": False
#     }

#     try:
#         response = requests.post(OLLAMA_API_URL, json=payload)
#         sql_query = response.json().get("response", "").strip()

#         # 🛑 Handle empty response
#         if not sql_query:
#             print("❌ LLM returned an empty response!")
#             return None

#         # 🔹 Remove markdown syntax like ```sql ... ```
#         sql_query = re.sub(r"```sql|```", "", sql_query).strip()
#         print(f"✅ Cleaned SQL Query: {sql_query}")
#         return sql_query

#     except Exception as e:
#         print(f"❌ Ollama Request Error: {e}")
#         return None
