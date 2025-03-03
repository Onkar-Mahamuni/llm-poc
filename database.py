import psycopg2
import psycopg2.extras
import config
import logging

def execute_query(sql_query):
    """Executes the given SQL query and returns the results."""
    try:
        logging.info(f"Executing SQL Query: {sql_query}")
        conn = psycopg2.connect(
            dbname=config.DB_NAME,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            host=config.DB_HOST,
            port=config.DB_PORT
        )
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute(sql_query)
        results = [dict(row) for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        logging.info(f"Query Results: {results}")
        return results
    except Exception as e:
        logging.error(f"Database Error: {str(e)}")
        return []

# # database.py
# import psycopg2
# from config import DB_CONFIG

# def get_db_connection():
#     """Establish connection to PostgreSQL database."""
#     try:
#         conn = psycopg2.connect(**DB_CONFIG)
#         return conn
#     except Exception as e:
#         print(f"❌ Database Connection Error: {e}")
#         return None
