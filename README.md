# Event Discovery API

FastAPI backend for a location-based social event discovery app.

## Prerequisites

- Python 3.11+
- PostgreSQL 14+ with PostGIS extension
- (Optional) Cloudinary or S3 account for image hosting

## Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

pip install -r requirements.txt

# Copy and edit environment variables
cp .env.example .env
```

### Database

```sql
CREATE DATABASE eventdiscovery;
\c eventdiscovery
CREATE EXTENSION IF NOT EXISTS postgis;
```

### Run migrations

```bash
alembic upgrade head
```

### Start the server

```bash
uvicorn app.main:app --reload --port 8000 --host 0.0.0.0
```

API docs are available at `http://localhost:8000/docs`.

## Deploy on Railway (new project)

This repository is pre-configured for Railway with:

- `railway.toml` (build and deploy settings)
- `Procfile` (web start command)
- PostgreSQL driver in `requirements.txt`

### 1) Push code to GitHub

Commit and push this backend repository.

### 2) Create Railway project

1. Open Railway and select **New Project**.
2. Choose **Deploy from GitHub repo** and select this repository.
3. Add a **PostgreSQL** service in the same project.

### 3) Configure variables

In your backend service, add/update these variables:

- `DATABASE_URL` = Railway Postgres connection URL (or reference variable from the Postgres service)
- `JWT_SECRET_KEY` = strong random secret
- `JWT_ALGORITHM` = `HS256` (optional, default already set)
- `ACCESS_TOKEN_EXPIRE_MINUTES` = `60` (optional)

### 4) Deploy

Railway will use `railway.toml` and start with:

```bash
alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

### 5) Verify

Open:

- `https://<your-service>.up.railway.app/health`
- `https://<your-service>.up.railway.app/docs`

If `/health` returns `{"status": "ok"}`, deployment is successful.