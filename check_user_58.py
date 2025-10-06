#!/usr/bin/env python3
import sys
import os
import psycopg2
from psycopg2.extras import RealDictCursor

DB_CONFIG = {
    'host': 'localhost',
    'database': 'posada_db',
    'user': 'postgres',
    'password': 'Joako2004@',
    'port': '5432'
}

try:
    connection = psycopg2.connect(**DB_CONFIG)
    cursor = connection.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT id, nombre, apellido, dni, email, password, activo FROM usuarios WHERE id = 58")
    user = cursor.fetchone()
    if user:
        print(f"User found: {user}")
        print(f"Password hash length: {len(user['password'])}")
        print(f"Password hash starts with: {user['password'][:20]}...")
    else:
        print("User with ID 58 not found")
    cursor.close()
    connection.close()
except Exception as e:
    print(f"Error: {e}")