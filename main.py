from fastapi import FastAPI, APIRouter, Request
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from api import crear_usuario, autenticar_creacion_usuario
from dotenv import load_dotenv
load_dotenv()  # carga las variables desde el archivo .env

app = FastAPI()

# Handler personalizado para errores de validación
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Extraer los errores y formatear mensajes
    errors = []
    for error in exc.errors():
        field = '.'.join(str(loc) for loc in error['loc'])
        msg = error['msg'] # Mensaje de Pydantic o validator
        errors.append(f'Error en {field}: {msg}')
    
    return JSONResponse(
        status_code=422,
        content={'detail': 'Datos inválidos. Por favor revise: ', 'errors': errors}
    )

# Handler para HTTPException general (errores como password corta)
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={'detail': exc.detail}
    )

@app.get("/")
def root():
    return FileResponse("public/pages/home/home.html")

@app.get("/crear_usuario")
def crear_usuario_page():
    return FileResponse("public/pages/crear_usuario/crear_usuario.html")

app.mount("/static", StaticFiles(directory='public'), name='static')

app.include_router(crear_usuario.router, prefix="/usuarios", tags=["Usuarios"]) # crear el usuario en la base de datos
app.include_router(autenticar_creacion_usuario.router, prefix="/autenticar_creacion_usuario", tags=["Autenticación"])
