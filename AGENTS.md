

# AGENTS.md

## Project Overview
FastAPI backend with PostgreSQL database for a hotel/posada reservation system. Frontend is served as static HTML/CSS/JS.

## 🧠 Memory & Context (Engram MCP)
Este proyecto utiliza **Engram** como sistema de memoria persistente para asegurar la continuidad entre sesiones de desarrollo.

* **Consulta Obligatoria**: Antes de realizar cambios estructurales en la API o modelos de base de datos, utiliza `search_memory` para verificar si existen decisiones previas documentadas.
* **Registro de Decisiones**: Al finalizar una implementación crítica (ej. cambios en el esquema de `posada_db` o lógica de autenticación JWT), documenta la decisión técnica utilizando `save_memory`.
* **Continuidad de Sesión**: Al iniciar una nueva interacción, ejecuta el comando `context` para recuperar el hilo de las últimas sesiones y sincronizar el estado del desarrollo.

## Running the App

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Environment Setup

Create a `.env` file with these required variables:
```
DB_HOST=localhost
DB_NAME=posada_db
DB_USER=postgres
DB_PASSWORD=your_password
DB_PORT=5432
JWT_SECRET=your_secure_random_secret_key
```

Generate `JWT_SECRET` with a secure random key (e.g., `openssl rand -hex 32`).

The app loads `.env` via `load_dotenv()` on startup (both in `main.py` and `config/database_config.py`).

## Architecture

- **Entry point**: `main.py` - FastAPI app, mounts static files from `public/`
- **API routes**: `api/` directory with routers for users, bookings, auth
- **Models**: `models/` directory
- **Config**: `config/` - database connection, logging
- **Frontend**: `public/pages/` - static HTML pages, `public/assets/` - JS/CSS/images

## Database

Uses PostgreSQL with `psycopg2-binary`. Connection config in `config/database_config.py`.

## Dependencies

```
fastapi, pydantic[email], psycopg2-binary, python-dotenv, bcrypt, PyJWT, uvicorn, jinja2
```

Install via: `pip install -r requirements.txt`

## Notes

- App loads `.env` via `load_dotenv()` at module import time in both `main.py` and `config/database_config.py`. Missing variables cause startup failures.
- `JWT_SECRET` is required for auth module to load (in `api/auth.py`).
- `pydantic[email]` is required for `EmailStr` type used in `models/user.py`.
- Database tables are auto-created on first connection via `config/database_initialization.py`.

---

### ¿Qué logramos con esto?
1.  **Contexto técnico**: El agente ahora sabe que las decisiones de base de datos y JWT deben guardarse en Engram para no repetirlas en el futuro.
2.  **Eficiencia**: Al pedirle que busque antes de proponer cambios, evitas que el agente "alucine" soluciones que ya descartaste anteriormente.
3.  **Memoria Local**: Como Engram está en modo `project`, todo lo que guarde se quedará en la base de datos local de este sistema de reservas.