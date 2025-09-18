from fastapi import FastAPI, APIRouter
from fastapi.staticfiles import StaticFiles
from api import crear_usuario, autenticar_creacion_usuario
from dotenv import load_dotenv
load_dotenv()  # carga las variables desde el archivo .env

app = FastAPI()

@app.get("/")
def root():
    return {'Mensaje': 'API funcionando correctamente'}

app.mount("/static", StaticFiles(directory='public'), name='static')

app.include_router(crear_usuario.router, prefix="/usuarios", tags=["Usuarios"]) # crear el usuario en la base de datos
app.include_router(autenticar_creacion_usuario.router, prefix="/autenticar_creacion_usuario", tags=["Autenticación"])
