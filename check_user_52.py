#!/usr/bin/env python3
import sys
import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

# Load environment variables
load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'posada_db'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD'),
    'port': os.getenv('DB_PORT', '5432')
}

try:
    connection = psycopg2.connect(**DB_CONFIG)
    cursor = connection.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM usuarios WHERE id = 52")
    user = cursor.fetchone()
    if user:
        print(f"User found: {user}")
    else:
        print("User with ID 52 not found")
    cursor.close()
    connection.close()
except Exception as e:
    print(f"Error: {e}")