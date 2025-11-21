from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jwt import decode as jwt_decode, PyJWTError
from datetime import datetime, timedelta, date
import psycopg2
from psycopg2.extras import RealDictCursor
from config.logging_config import logger
from models.booking import BookingCreate, BookingResponse
from config.database_operations import execute_query, insert_reserva
from config.database_config import get_database_config, validate_database_config
from dotenv import load_dotenv
import os
# from twilio.rest import Client  # Descomentar si usas Twilio

load_dotenv()

router = APIRouter()

SECRET_KEY = os.getenv('JWT_SECRET', 'xPS9pT9NLXy42Q_DSHL-oYuA8WmEZoW13Kf6GvvMUW0')
ALGORITHM = 'HS256'
logger.debug(f"JWT_SECRET used for decoding: '{SECRET_KEY}' (length: {len(SECRET_KEY)})")
DB_CONFIG = get_database_config()

logger.debug(f"DB_CONFIG loaded: host={DB_CONFIG['host']}, database={DB_CONFIG['database']}, user={DB_CONFIG['user']}, port={DB_CONFIG['port']}")
logger.debug(f"DB_PASSWORD from env: {'SET' if DB_CONFIG['password'] else 'NOT SET'}")
if not DB_CONFIG['password']:
    logger.warning("DB_PASSWORD no seteada")

is_valid, validation_msg = validate_database_config(DB_CONFIG)
if not is_valid:
    logger.error(f"Falló en la configuración de la base de datos: {validation_msg}")
else:
    logger.info("Configuración de la base de datos válida")

# Twilio 
# TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "tu_twilio_account_sid")
# TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "tu_twilio_auth_token")
# TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")
# ADMIN_WHATSAPP_NUMBER = os.getenv("ADMIN_WHATSAPP_NUMBER", "whatsapp:+numero_admin")
# twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        logger.debug(f"Token recibido (primeros 50 chars): {token[:50]}...")
        payload = jwt_decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str | None = payload.get('sub')
        exp = payload.get('exp')
        current_time = datetime.utcnow().timestamp()
        logger.debug(f"Token payload: sub={user_id}, exp={exp}, current_time={current_time}")
        if user_id is None:
            logger.error("Token inválido: sub no encontrado")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Token Inválido')
        logger.debug(f"Usuario autenticado: ID {user_id}")
        return {'id': int(user_id)}
    except PyJWTError as e:
        logger.error(f"Error decodificando token: {str(e)}")
        logger.error(f"Token that failed: {token[:100]}...")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Token Inválido')

@router.get("/reservas", response_model=list[BookingResponse])
async def get_reservas(current_user: dict = Depends(get_current_user)):
    try:
        user_id = current_user["id"]
        connection = psycopg2.connect(**DB_CONFIG)
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        query = """
            SELECT r.id, r.fecha_check_in AS fecha_entrada, r.fecha_check_out AS fecha_salida,
                    r.cantidad_habitaciones AS huespedes, u.email AS contacto,
                    r.estado, r.precio_total, r.fecha_creacion
            FROM reservas r
            JOIN usuarios u ON r.usuario_id = u.id
            WHERE r.usuario_id = %s
        """
        reservas = execute_query(cursor, query, (user_id,))
        cursor.close()
        connection.close()
        logger.info(f"Usuario {user_id} consultó sus reservas")
        return reservas
    except Exception as e:
        logger.error(f"Error en GET /api/reservas para usuario {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al obtener reservas")

# POST /api/reservas - Crear una nueva reserva
@router.post("/reservas", response_model=BookingResponse)
async def create_reserva(reserva: BookingCreate, current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    
    try:
        if reserva.cantidad_habitaciones < 1 or reserva.cantidad_habitaciones > 4:
            raise HTTPException(status_code=400, detail="El número de habitaciones debe estar entre 1 y 4")
        if reserva.fecha_check_in < datetime.today().date():
            raise HTTPException(status_code=400, detail="La fecha de check-in no puede ser anterior a hoy")
        if reserva.fecha_check_out <= reserva.fecha_check_in + timedelta(days=1):
            raise HTTPException(status_code=400, detail="La reserva debe ser por al menos dos noches")
    except ValueError as e:
        logger.error(f"Error de validación: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

    try:
        connection = psycopg2.connect(**DB_CONFIG)
        cursor = connection.cursor(cursor_factory=RealDictCursor)

        query = """
            SELECT SUM(cantidad_habitaciones) as total_habitaciones
            FROM reservas
            WHERE (fecha_check_in <= %s AND fecha_check_out >= %s)
            AND estado NOT IN ('Cancelada', 'Finalizada')
        """
        cursor.execute(query, (reserva.fecha_check_out, reserva.fecha_check_in))
        result = cursor.fetchone()
        total_habitaciones = result['total_habitaciones'] or 0
        max_habitaciones = 4
        if total_habitaciones + reserva.cantidad_habitaciones > max_habitaciones:
            cursor.close()
            connection.close()
            raise HTTPException(status_code=400, detail="No hay suficientes habitaciones disponibles en esas fechas")

        logger.info(f"🔍 DEBUG - DB_CONFIG in create_reserva: {DB_CONFIG}")
        logger.info(f"🔍 DEBUG - user_id from token: {user_id}")
        logger.debug(f"Attempting to fetch user with ID: {user_id}")
        cursor.execute("SELECT email FROM usuarios WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        logger.debug(f"User fetch result for ID {user_id}: {user}")
        logger.info(f"🔍 DEBUG - User query result: {user}")
        if not user:
            logger.error(f"User with ID {user_id} not found in database")
            cursor.close()
            connection.close()
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        user_email = user['email']

        dias = (reserva.fecha_check_out - reserva.fecha_check_in).days
        precio_total = dias * reserva.cantidad_habitaciones * 100.0

        observaciones = f"Contacto: {user_email}"
        reserva_id = insert_reserva(
            cursor, connection, user_id, reserva.fecha_check_in,
            reserva.fecha_check_out, reserva.cantidad_habitaciones, precio_total, observaciones
        )
        if not reserva_id:
            cursor.close()
            connection.close()
            raise HTTPException(status_code=500, detail="Error al crear reserva")

        cursor.execute(
            """
            SELECT r.id, r.fecha_check_in AS fecha_entrada, r.fecha_check_out AS fecha_salida,
                    r.cantidad_habitaciones AS huespedes, u.email AS contacto,
                    r.estado, r.precio_total, r.fecha_creacion
            FROM reservas r
            JOIN usuarios u ON r.usuario_id = u.id
            WHERE r.id = %s
            """,
            (reserva_id,)
        )
        nueva_reserva = cursor.fetchone()
        cursor.close()
        connection.close()

        # Log para notificación manual vía WhatsApp
        # logger.info(f"Nueva reserva pendiente: ID {reserva_id}, Contacto: {user_email}, Fechas: {reserva.fecha_check_in} a {reserva.fecha_check_out}, Habitaciones: {reserva.cantidad_habitaciones}. Contactar vía WhatsApp para pago.")

        # Enviar mensaje WhatsApp (comentado)
        # try:
        #     twilio_client.messages.create(
        #         body=f"Nueva reserva: {reserva.fecha_check_in} a {reserva.fecha_check_out}, {reserva.cantidad_habitaciones} habitaciones, Contacto: {user_email}",
        #         from_=TWILIO_WHATSAPP_NUMBER,
        #         to=ADMIN_WHATSAPP_NUMBER
        #     )
        #     logger.info(f"Usuario {user_id} creó reserva {reserva_id} y se envió WhatsApp")
        # except Exception as twilio_err:
        #     logger.error(f"Error al enviar WhatsApp para reserva {reserva_id}: {str(twilio_err)}")

        return nueva_reserva
    except Exception as e:
        logger.error(f"Error en POST /api/reservas para usuario {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al crear reserva")

# GET /api/reservas/pendientes - Obtener reservas pendientes (para admin)
@router.get("/reservas/pendientes", response_model=list[BookingResponse])
async def get_reservas_pendientes():
    try:
        connection = psycopg2.connect(**DB_CONFIG)
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        query = """
            SELECT r.id, r.fecha_check_in AS fecha_entrada, r.fecha_check_out AS fecha_salida,
                    r.cantidad_habitaciones AS huespedes, u.email AS contacto,
                    r.estado, r.precio_total, r.fecha_creacion
            FROM reservas r
            JOIN usuarios u ON r.usuario_id = u.id
            WHERE r.estado = 'Pendiente'
        """
        reservas = execute_query(cursor, query)
        cursor.close()
        connection.close()
        return reservas
    except Exception as e:
        logger.error(f"Error en GET /api/reservas/pendientes: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al obtener reservas pendientes")

# GET /api/disponibilidad - Obtener reservas para calendario interactivo -> Pendiente
@router.get("/disponibilidad")
async def get_disponibilidad(start_date: date, end_date: date):
    try:
        connection = psycopg2.connect(**DB_CONFIG)
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        query = """
            SELECT fecha_check_in, fecha_check_out, cantidad_habitaciones
            FROM reservas
            WHERE fecha_check_in <= %s AND fecha_check_out >= %s
            AND estado NOT IN ('Cancelada', 'Finalizada')
        """
        reservas = execute_query(cursor, query, (end_date, start_date))
        cursor.close()
        connection.close()
        return reservas
    except Exception as e:
        logger.error(f"Error en GET /api/disponibilidad: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al obtener disponibilidad")