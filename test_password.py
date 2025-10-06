#!/usr/bin/env python3
import bcrypt

# The stored hash from DB
stored_hash = '$2b$12$eQdPbSV7jPnNJeb20G14Y..2XJfzmIrdhx94g6LbF8L5LB1biXnn6'

# The password used during creation
password = 'joako2004'

# Encode to bytes
password_bytes = password.encode('utf-8')
hash_bytes = stored_hash.encode('utf-8')

# Check
match = bcrypt.checkpw(password_bytes, hash_bytes)
print(f"Password '{password}' matches hash: {match}")
print(f"Hash length: {len(stored_hash)}")
print(f"Password bytes length: {len(password_bytes)}")