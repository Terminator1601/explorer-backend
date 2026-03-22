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
uvicorn app.main:app --reload --port 8000
```

API docs are available at `http://localhost:8000/docs`.


uvicorn app.main:app --reload --port 8000 --host 0.0.0.0