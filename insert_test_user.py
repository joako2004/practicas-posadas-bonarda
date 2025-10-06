#!/usr/bin/env python3
"""
Script to insert a test user with ID 52 into the database.
This resolves the "Usuario no encontrado" error by ensuring user 52 exists.
"""

import sys
import os
from datetime import datetime
import bcrypt

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.database_connection import connect_postgresql, close_connection
from config.logging_config import logger

def insert_test_user():
    """Insert test user with ID 52"""

    # Test user data
    user_data = {
        'id': 52,
        'nombre': 'Test',
        'apellido': 'User',
        'dni': '12345678',
        'cuil_cuit': '20123456789',
        'email': 'test@example.com',
        'telefono': '1234567890',
        'password_plain': 'TestPassword123',  # Plain password to hash
        'activo': True
    }

    connection, cursor = None, None

    try:
        logger.info("🔗 Connecting to database...")
        connection, cursor = connect_postgresql()

        if not connection or not cursor:
            logger.error("❌ Failed to connect to database")
            return False

        # Hash the password
        logger.info("🔐 Hashing password...")
        hashed_password = bcrypt.hashpw(
            user_data['password_plain'].encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')

        # Check if user already exists
        cursor.execute("SELECT id FROM usuarios WHERE id = %s", (user_data['id'],))
        existing_user = cursor.fetchone()

        if existing_user:
            logger.info(f"✅ User with ID {user_data['id']} already exists")
            return True

        # Insert the test user with specific ID
        logger.info(f"📝 Inserting test user with ID {user_data['id']}...")

        insert_query = """
        INSERT INTO usuarios (id, nombre, apellido, dni, cuil_cuit, email, telefono, password, fecha_registro, activo)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        cursor.execute(insert_query, (
            user_data['id'],
            user_data['nombre'],
            user_data['apellido'],
            user_data['dni'],
            user_data['cuil_cuit'],
            user_data['email'],
            user_data['telefono'],
            hashed_password,
            datetime.now(),
            user_data['activo']
        ))

        # Update the sequence to avoid conflicts with future inserts
        cursor.execute("SELECT setval('usuarios_id_seq', (SELECT MAX(id) FROM usuarios))")

        connection.commit()

        logger.info(f"✅ Test user inserted successfully with ID {user_data['id']}")
        logger.info(f"   Email: {user_data['email']}")
        logger.info(f"   Password: {user_data['password_plain']} (hashed in database)")

        return True

    except Exception as error:
        logger.error(f"❌ Error inserting test user: {error}", exc_info=True)
        if connection:
            connection.rollback()
        return False

    finally:
        if connection and cursor:
            close_connection(connection, cursor)

if __name__ == "__main__":
    logger.info("🚀 Starting test user insertion script...")

    success = insert_test_user()

    if success:
        logger.info("🎉 Test user insertion completed successfully!")
        sys.exit(0)
    else:
        logger.error("💥 Test user insertion failed!")
        sys.exit(1)