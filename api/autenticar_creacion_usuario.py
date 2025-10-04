from fastapi import APIRouter, Request, HTTPException, status, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
import jwt
import datetime
from config.database_operations import authenticate_user
from config.logging_config import logger
import os

router = APIRouter()
templates = Jinja2Templates(directory="public/pages/crear_usuario")
login_templates = Jinja2Templates(directory="public/pages/login")

class LoginRequest(BaseModel):
    email: str
    password: str

@router.get("/registrar", response_class=HTMLResponse)
async def show_register_form(request: Request):
    """
    Mostrar el formulario de registro
    """
    return templates.TemplateResponse("crear_usuario.html", {"request": request})

@router.get("/login", response_class=HTMLResponse)
async def show_login_form(request: Request):
    """
    Mostrar el formulario de login
    """
    return login_templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Autenticar usuario y retornar JWT token
    """
    try:
        user = authenticate_user(form_data.username, form_data.password)
        if not user:
            logger.error(f"Intento de login fallido: usuario {form_data.username} no encontrado o credenciales inválidas")
            raise HTTPException(status_code=401, detail="Credenciales inválidas")
        
        # Crear token JWT
        payload = {
            "sub": str(user["id"]),
            "email": user["email"],
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }
        token = jwt.encode(payload, os.getenv('JWT_SECRET', 'tu_jwt_secreto'), algorithm="HS256")
        
        logger.info(f"Usuario {form_data.username} autenticado exitosamente")
        return {"access_token": token, "token_type": "bearer", "user": user}
    except Exception as e:
        logger.error(f"Error en login: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno del servidor")