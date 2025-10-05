import os
from dotenv import load_dotenv

print(f"CWD: {os.getcwd()}")
print(f"DB_PASSWORD before: {os.getenv('DB_PASSWORD')}")

# Try wrong path
load_dotenv('../../.env')
print(f"DB_PASSWORD after wrong path: {os.getenv('DB_PASSWORD')}")

# Try correct path
load_dotenv('.env')
print(f"DB_PASSWORD after correct path: {os.getenv('DB_PASSWORD')}")