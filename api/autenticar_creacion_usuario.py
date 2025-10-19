from fastapi import APIRouter, Request, HTTPException, status, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import EmailStr
import jwt
from datetime import datetime, timedelta, timezone
from config.database_operations import authenticate_user
from config.logging_config import logger
import os

router = APIRouter()
templates = Jinja2Templates(directory="public/pages/crear_usuario")
login_templates = Jinja2Templates(directory="public/pages/login")

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
async def login(request: Request):
    """
    Autenticar usuario y retornar JWT token
    """
    # Log raw request details
    logger.info(f"🔍 DIAGNOSTIC - RAW REQUEST RECEIVED")
    logger.info(f"🔍 DIAGNOSTIC - Method: {request.method}")
    logger.info(f"🔍 DIAGNOSTIC - URL: {request.url}")
    logger.info(f"🔍 DIAGNOSTIC - Content-Type: {request.headers.get('content-type', 'NOT SET')}")
    
    # Read and log the raw body
    try:
        body = await request.body()
        logger.info(f"🔍 DIAGNOSTIC - Raw body length: {len(body)} bytes")
        logger.info(f"🔍 DIAGNOSTIC - Raw body content: {body.decode('utf-8', errors='replace')}")
    except Exception as e:
        logger.error(f"🔍 DIAGNOSTIC - Could not read raw body: {e}")
        raise HTTPException(status_code=400, detail="Could not read request body")
    
    # Parse form data manually
    try:
        from urllib.parse import parse_qs
        body_str = body.decode('utf-8')
        form_data = parse_qs(body_str)
        logger.info(f"🔍 DIAGNOSTIC - Parsed form data: {form_data}")
        
        username = form_data.get('username', [None])[0]
        password = form_data.get('password', [None])[0]
        
        if not username or not password:
            logger.error(f"🔍 DIAGNOSTIC - Missing credentials: username={username}, password={'SET' if password else 'NOT SET'}")
            raise HTTPException(status_code=422, detail="Missing username or password")
        
        logger.info(f"🔍 DIAGNOSTIC - Form parsed successfully: username='{username}', password_length={len(password)}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"🔍 DIAGNOSTIC - Error parsing form data: {e}")
        raise HTTPException(status_code=422, detail=f"Invalid form data: {str(e)}")
    try:
        user = authenticate_user(username, password)
        if not user:
            logger.error(f"Intento de login fallido: usuario {username} no encontrado o credenciales inválidas")
            raise HTTPException(status_code=401, detail="Credenciales inválidas")

        # Crear token JWT
        secret_key = os.getenv('JWT_SECRET', 'xPS9pT9NLXy42Q_DSHL-oYuA8WmEZoW13Kf6GvvMUW0')
        logger.debug(f"JWT_SECRET used for encoding: '{secret_key}' (length: {len(secret_key)})")
        payload = {
            "sub": str(user["id"]),
            "email": user["email"],
            "exp": datetime.now(timezone.utc) + timedelta(hours=24)
        }
        token = jwt.encode(payload, secret_key, algorithm="HS256")
        logger.debug(f"Generated token (first 50 chars): {token[:50]}...")

        logger.info(f"Usuario {username} autenticado exitosamente")
        return {"access_token": token, "token_type": "bearer", "user": user}
    except Exception as e:
        logger.error(f"Error en login: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno del servidor")