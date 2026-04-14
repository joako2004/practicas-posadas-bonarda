# AGENTS.md

## Project Overview
FastAPI backend with PostgreSQL database for a hotel/posada reservation system. Frontend is served as static HTML/CSS/JS.

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
