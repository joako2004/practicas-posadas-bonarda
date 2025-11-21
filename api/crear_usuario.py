from fastapi import APIRouter, HTTPException
from models.user import UserCreate, UserResponse
from config.database_operations import insert_usuario
from pydantic import BaseModel, EmailStr, ValidationError
from datetime import datetime, timedelta, timezone
from config.logging_config import logger
import bcrypt
import jwt
import os

SECRET_KEY = os.getenv('JWT_SECRET', 'xPS9pT9NLXy42Q_DSHL-oYuA8WmEZoW13Kf6GvvMUW0')
ALGORITHM = 'HS256'

class UserCreateRequest(BaseModel):
    nombre: str
    apellido: str
    dni: str
    cuil_cuit: str
    email: EmailStr
    telefono: str
    password: str

router = APIRouter()

@router.post("/crear")
async def crear_usuario(request: UserCreateRequest):
    try:
        password = request.password

        logger.info(f'Password received: {repr(password)}, len chars: {len(password)}, len bytes: {len(password.encode("utf-8"))}')

        try:
            user_data = UserCreate(
                nombre=request.nombre,
                apellido=request.apellido,
                dni=request.dni,
                cuil_cuit=request.cuil_cuit,
                email=request.email,
                telefono=request.telefono,
                password=password
            )
            logger.info("DEBUG: UserCreate validation passed with plain password")
        except ValidationError as e:
            logger.error(f"DEBUG: UserCreate validation failed: {type(e).__name__}: {str(e)}")
            errors = e.errors()
            for error in errors:
                if 'email' in error.get('loc', []):
                    raise HTTPException(
                        status_code=400,
                        detail="El formato de email es inválido"
                    )
            error_msg = errors[0]['msg'] if errors else str(e)
            if error_msg.startswith("Value error, "):
                error_msg = error_msg[13:] 
            raise HTTPException(
                status_code=400,
                detail=error_msg
            )
        except Exception as e:
            logger.error(f"DEBUG: UserCreate validation failed: {type(e).__name__}: {str(e)}")
            raise HTTPException(
                status_code=400,
                detail=str(e)
            )

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        user_data.password = hashed_password
        
        logger.info(f"🔍 DIAGNOSTIC - About to call insert_usuario with data: {user_data.model_dump(exclude={'password'})}")
        user_id = insert_usuario(user_data)
        logger.info(f"🔍 DIAGNOSTIC - insert_usuario returned: type={type(user_id)}, value={user_id if not isinstance(user_id, dict) else user_id}")

        if isinstance(user_id, dict):
            error_type = user_id.get("type")
            if error_type in ["duplicate_email", "duplicate_dni", "duplicate_cuil_cuit", "duplicate_telefono", "duplicate_nombre_apellido", "duplicate_constraint"]:
                raise HTTPException(status_code=422, detail=user_id["error"])
            else:
                raise HTTPException(status_code=500, detail=user_id["error"])

        logger.info(f"🔍 DEBUG - User created with ID {user_id}, DB_HOST={os.getenv('DB_HOST', 'localhost')}, DB_NAME={os.getenv('DB_NAME', 'posada_db')}")

        logger.debug(f"JWT_SECRET used for encoding in crear_usuario: '{SECRET_KEY}' (length: {len(SECRET_KEY)})")
        token_data = {"sub": str(user_id), "exp": datetime.now(timezone.utc) + timedelta(days=30)}
        token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
        logger.debug(f"Generated token in crear_usuario (first 50 chars): {token[:50]}...")

        logger.info(f'Usuario creado exitosamente con ID {user_id}')
        
        user_response = None
        try:
            logger.info(f'Construyendo UserResponse con id={user_id}')
            logger.info(f'user_data.model_dump(exclude={{password}}): {user_data.model_dump(exclude={"password"})}')

            user_response = UserResponse(
                id=user_id,
                **user_data.model_dump(exclude={'password'}),
                activo=True,
                fecha_registro=datetime.now(timezone.utc)
            )
            logger.info(f'UserResponse creado exitosamente: {user_response}')

        except Exception as e:
            logger.error(f'Error construyendo UserResponse: {type(e).__name__}: {str(e)}')
            logger.error(f'Traceback completo:', exc_info=True)
            user_response = {
                "id": user_id,
                "nombre": request.nombre,
                "apellido": request.apellido,
                "dni": request.dni,
                "cuil_cuit": request.cuil_cuit,
                "email": request.email,
                "telefono": request.telefono,
                "activo": True,
                "fecha_registro": datetime.now(timezone.utc)
            }

        response_dict = {
            "user": user_response,
            "token": token
        }
        logger.info(f'Response dict creado: {type(response_dict)}')

        return response_dict
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'🔍 DIAGNOSTIC - Unhandled exception in crear_usuario: type={type(e).__name__}, message={str(e)}')
        logger.error(f'Error en registro: {e}', exc_info=True)
        raise HTTPException(
            status_code=500,
            detail='Error interno del servidor. Por favor, intenta de nuevo'
        )