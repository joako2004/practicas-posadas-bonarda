from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pydantic import BaseModel
import bcrypt
import os
from dotenv import load_dotenv
from config.database_operations import get_user_by_id
from config.logging_config import logger

# Cargar variables de entorno desde .env
load_dotenv()

# Obtener SECRET_KEY del .env
SECRET_KEY = os.getenv('JWT_SECRET')
if not SECRET_KEY:
    raise ValueError("JWT_SECRET no está configurado en el archivo .env")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: int | None = None

class User(BaseModel):
    id: int
    nombre: str
    apellido: str
    email: str
    activo: bool

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_password(plain_password: str, hashed_password: str | bytes) -> bool:
    """Verifica que la contraseña coincida con el hash"""
    if isinstance(hashed_password, str):
        hashed_password = hashed_password.encode('utf-8')
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password)

def get_password_hash(password: str) -> str:
    """Genera un hash bcrypt de la contraseña"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Crea un token JWT con tiempo de expiración"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> User:
    """Obtiene el usuario actual desde el token JWT"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido o expirado. Por favor, regístrese nuevamente.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Decodificar el token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        
        if user_id is None:
            logger.warning("Token sin user_id en el campo 'sub'")
            raise credentials_exception
        
        # Convertir a int de forma segura
        try:
            user_id = int(user_id)
        except (ValueError, TypeError):
            logger.warning(f"user_id no válido en token: {user_id}")
            raise credentials_exception
            
        token_data = TokenData(user_id=user_id)
        
    except InvalidTokenError as e:
        logger.warning(f"Token inválido: {str(e)}")
        raise credentials_exception
    
    # Obtener usuario de la base de datos
    try:
        user = get_user_by_id(user_id=token_data.user_id)
    except Exception as e:
        logger.error(f"Error al obtener usuario {token_data.user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener información del usuario"
        )
    
    if user is None:
        logger.warning(f"Usuario {token_data.user_id} no encontrado")
        raise credentials_exception
    
    # Convertir a modelo User
    try:
        if isinstance(user, dict):
            return User(**user)
        else:
            return User(
                id=user.id,
                nombre=user.nombre,
                apellido=user.apellido,
                email=user.email,
                activo=user.activo
            )
    except Exception as e:
        logger.error(f"Error al crear objeto User: {str(e)}")
        raise credentials_exception

async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Verifica que el usuario esté activo"""
    if not current_user.activo:
        logger.warning(f"Intento de acceso con usuario inactivo: {current_user.id}")
        raise HTTPException(status_code=400, detail="Usuario inactivo")
    return current_user