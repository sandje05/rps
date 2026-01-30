import os
import mysql.connector

def get_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "db"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "rps"),
        password=os.getenv("DB_PASSWORD", "rps"),
        database=os.getenv("DB_NAME", "rpsdb"),
        autocommit=True
    )
