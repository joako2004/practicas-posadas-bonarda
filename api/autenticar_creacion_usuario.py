from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="public/pages/crear_usuario")

@router.get("/registrar", response_class=HTMLResponse)
async def show_register_form(request: Request):
    """
    Mostrar el formulario de registro
    """
    return templates.TemplateResponse("crear_usuario.html", {"request": request})

# http://127.0.0.1:8000/autenticar_creacion_usuario/registrar