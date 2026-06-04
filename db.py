import os
import psycopg2

DB_CONFIG = {
    "dbname": "postgres",
    "user": "postgres",
    "password": os.environ.get("DB_PASSWORD"),
    "host": "localhost",
    "port": "5432",
}


def get_db():
    return psycopg2.connect(**DB_CONFIG)
