# app/logger.py

import logging

logging.basicConfig(
    filename="query.log",
    level=logging.INFO,
    format="%(asctime)s - %(message)s"
)

def log_query(question, sql, result):
    logging.info(f"QUESTION: {question}")
    logging.info(f"SQL: {sql}")
    logging.info(f"RESULT: {str(result)[:200]}")
    logging.info("----")