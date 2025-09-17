from fastapi import FastAPI, APIRouter
from fastapi.staticfiles import StaticFiles
from api import crear_usuario
from dotenv import load_dotenv
load_dotenv()  # carga las variables desde el archivo .env

app = FastAPI()

# Servir carpeta pubil como estáticos
app.mount("/static", StaticFiles(directory='public'), name='static')

# Incluir router de usuarios
app.include_router(crear_usuario.router, prefix="/usuarios", tags=["Usuarios"])
