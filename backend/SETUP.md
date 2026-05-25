# PyFlow Blog Backend - Local Setup Guide

## Prerequisites

- **Python 3.12+** installed on your machine
- **PostgreSQL 15+** (one of the following):
  - Local PostgreSQL instance
  - Supabase cloud project
  - Azure Database for PostgreSQL
  - AWS RDS for PostgreSQL
- **Git** for cloning the repository

---

## 1. Clone and Enter the Project

```bash
git clone <repo-url>
cd backend
```

---

## 2. Create a Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate   # Linux/macOS
# venv\Scripts\activate    # Windows
```

---

## 3. Install Dependencies

```bash
pip install -e ".[dev]"
```

This installs FastAPI, SQLAlchemy, asyncpg, Pydantic, and all other required packages. The `[dev]` extra includes pytest and testing tools.

---

## 4. Configure the Database

Copy the example env file and edit it:

```bash
cp .env .env
```

Set `DB_MODE` to match your PostgreSQL provider:

### Option A: Local PostgreSQL

1. Install PostgreSQL locally (or use Docker: `docker run -d -p 5432:5432 -e POSTGRES_DB=pyflow -e POSTGRES_USER=pyflow_user -e POSTGRES_PASSWORD=changeme postgres:16-alpine`)
2. Set in `.env`:

```env
DB_MODE=local
DATABASE_URL=postgresql+asyncpg://pyflow_user:changeme@localhost:5432/pyflow
DATABASE_URL_SYNC=postgresql://pyflow_user:changeme@localhost:5432/pyflow
```

### Option B: Supabase Cloud

1. Create a project at [supabase.com](https://supabase.com)
2. Go to **Settings > Database** and note your database password
3. Set in `.env`:

```env
DB_MODE=supabase
SUPABASE_URL=https://<your-project-ref>.supabase.co
SUPABASE_ANON_KEY=<your-anon-key>
SUPABASE_DB_PASSWORD=<your-database-password>
```

The connection string is automatically derived from `SUPABASE_URL` and `SUPABASE_DB_PASSWORD` using Supabase's connection pooler.

### Option C: Azure Database for PostgreSQL

1. Create an Azure Database for PostgreSQL resource in the Azure Portal
2. Under **Connection security**, ensure your client IP is allowlisted and SSL is enforced
3. Set in `.env`:

```env
DB_MODE=azure
AZURE_POSTGRES_HOST=<server-name>.postgres.database.azure.com
AZURE_POSTGRES_USER=<username>@<server-name>
AZURE_POSTGRES_PASSWORD=<your-password>
AZURE_POSTGRES_DATABASE=pyflow
AZURE_POSTGRES_PORT=5432
AZURE_POSTGRES_SSL_MODE=require
```

### Option D: AWS RDS for PostgreSQL

1. Create an RDS PostgreSQL instance in the AWS Console
2. Ensure the security group allows inbound traffic on port 5432 from your IP
3. Set in `.env`:

```env
DB_MODE=aws
AWS_RDS_HOST=<your-rds-endpoint>.<region>.rds.amazonaws.com
AWS_RDS_PORT=5432
AWS_RDS_USER=<master-username>
AWS_RDS_PASSWORD=<your-password>
AWS_RDS_DATABASE=pyflow
AWS_RDS_SSL_MODE=require
```

---

## 5. Run Database Migrations

The schema is managed via Supabase migrations. If using Supabase, the tables are created automatically through the migration tool. For local/Azure/AWS PostgreSQL, apply the schema manually:

```bash
# Using psql with the sync connection string:
psql "<DATABASE_URL_SYNC>" < migrations/schema.sql
```

Or use Alembic (if configured):

```bash
alembic upgrade head
```

---

## 6. Run the Server

```bash
uvicorn app.main:app --host 0.0.0.0 --port 3001 --reload
```

The API is now available at `http://localhost:3001`.

- **Swagger docs**: http://localhost:3001/docs
- **ReDoc**: http://localhost:3001/redoc
- **Health check**: http://localhost:3001/api/v1/health

---

## 7. Verify It Works

```bash
curl http://localhost:3001/api/v1/health
```

Expected response:

```json
{
  "status": "ok",
  "timestamp": "2024-01-15T10:30:00Z",
  "database": "connected",
  "uptime": 86400
}
```

---

## 8. Seed Data

The initial migration seeds:

- **1 Super Admin**: `admin@pyflow.dev` (password: `changeme`)
- **3 Authors**: Alex Chen, Sarah Kim, Marcus Webb
- **4 Categories**: AI Engineering, Python, Automation, MLOps
- **12 Tags**: Python, LangChain, FastAPI, ML, Automation, RAG, Docker, Pydantic, OpenAI, Async Python, SQLAlchemy, TypeScript
- **Default settings** for all blog configuration sections

---

## 9. Run Tests

```bash
pytest
```

With coverage:

```bash
pytest --cov=app --cov-report=term-missing
```

---

## 10. Docker (Optional)

Build and run with Docker Compose:

```bash
docker compose up --build
```

This starts the API on port 3001 and Redis on port 6379. Uncomment the `db` service in `docker-compose.yml` if you want a local PostgreSQL container.

---

## Environment Variables Reference

| Variable | Description | Default |
|---|---|---|
| `DB_MODE` | Database provider: `local`, `supabase`, `azure`, `aws` | `local` |
| `DATABASE_URL` | Async PG connection (local mode) | `postgresql+asyncpg://...` |
| `DATABASE_URL_SYNC` | Sync PG connection (local mode) | `postgresql://...` |
| `SUPABASE_URL` | Supabase project URL | - |
| `SUPABASE_DB_PASSWORD` | Supabase DB password | - |
| `AZURE_POSTGRES_HOST` | Azure Postgres hostname | - |
| `AZURE_POSTGRES_USER` | Azure Postgres username | - |
| `AZURE_POSTGRES_PASSWORD` | Azure Postgres password | - |
| `AZURE_POSTGRES_SSL_MODE` | Azure SSL mode | `require` |
| `AWS_RDS_HOST` | RDS endpoint | - |
| `AWS_RDS_USER` | RDS username | - |
| `AWS_RDS_PASSWORD` | RDS password | - |
| `AWS_RDS_SSL_MODE` | RDS SSL mode | `require` |
| `JWT_ACCESS_SECRET` | Secret for access tokens | (change in prod) |
| `JWT_REFRESH_SECRET` | Secret for refresh tokens | (change in prod) |
| `OPENAI_API_KEY` | OpenAI API key for AI features | - |
| `UPLOAD_DIR` | Local upload directory | `./uploads` |
| `STORAGE_PROVIDER` | File storage: `local` or `s3` | `local` |

---

## Project Structure

```
backend/
  app/
    main.py                  # FastAPI app factory
    config.py                # Settings (env vars, DB mode switching)
    shared/                  # Cross-cutting concerns
      events/                # Event bus and decorators
      auth/                  # JWT, password hashing, FastAPI dependencies
      storage/               # File storage adapters
      database.py            # SQLAlchemy async engine
      exceptions.py          # Error handling
      pagination.py          # Paginated response helper
    identity/                # Auth & Users bounded context
    content/                 # Articles, Categories, Tags, Search
    media/                   # File uploads & storage
    engagement/              # Newsletter & Analytics
    intelligence/            # AI Assistant (OpenAI)
    administration/          # Settings & Activity Log
  .env                       # Environment configuration
  pyproject.toml             # Python dependencies
  Dockerfile                 # Container build
  docker-compose.yml         # Local orchestration
```

Each bounded context follows Domain-Driven Design with `domain/`, `infrastructure/`, `application/`, and `api/` layers.
