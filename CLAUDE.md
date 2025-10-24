# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**Repository:** https://github.com/albertocabasvidani/notionshare

## Project Overview

NotionShare is a web application that enables sharing filtered portions of Notion databases with external users, overcoming Notion's native sharing limitations. It creates mirror databases with row and column filters, bidirectional synchronization, and granular permissions.

## Architecture

**Stack:**
- Backend: Python 3.11+, FastAPI, SQLAlchemy
- Database: PostgreSQL (also serves as Celery message broker)
- Task Queue: Celery + Celery Beat
- Frontend: Vanilla HTML/CSS/JavaScript
- External API: notion-client SDK

**Key Design Decisions:**
- PostgreSQL is used for both data storage AND as Celery broker (no Redis required)
- Celery broker URL format: `db+postgresql://` prefix instead of `postgresql://`
- Bidirectional sync: source → target (filtered) and target → source (writable properties only)
- All tables created via SQLAlchemy models with on-the-fly creation at startup
- Custom CORS middleware for development: FastAPI's built-in CORSMiddleware has issues with wildcard origins, using SimpleCORSMiddleware instead
- Frontend auto-detects backend API URL from `window.location.hostname` for cross-environment compatibility

## Database Schema

Core relationships:
- `User` → has many `DatabaseConfig` (ownership)
- `DatabaseConfig` → has many `RowFilter`, `PropertyMapping`, `UserPermission`, `SyncLog`, `PageMapping`
- `PageMapping` tracks source page ↔ target page relationships for sync

Critical fields:
- `DatabaseConfig.source_database_id`: Original Notion database
- `DatabaseConfig.target_database_id`: Created mirror database
- `PropertyMapping.is_visible`: Show in mirror
- `PropertyMapping.is_writable`: Allow edits from mirror back to source

## Development Commands

### Initial Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with database credentials and JWT_SECRET_KEY
```

### Database Operations
```bash
# Create database (if not exists)
createdb notionshare

# Run migrations (auto-creates tables on first run via SQLAlchemy)
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "Description"

# Reset database
dropdb notionshare && createdb notionshare && alembic upgrade head
```

### Running Services

**Three processes required for full functionality:**

1. Backend API:
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

2. Celery Worker (handles async sync tasks):
```bash
cd backend
source venv/bin/activate
celery -A app.tasks.celery_app worker --loglevel=info
```

3. Celery Beat (scheduler - optional for manual sync only):
```bash
cd backend
source venv/bin/activate
celery -A app.tasks.celery_app beat --loglevel=info
```

Frontend:
```bash
cd frontend
python -m http.server 3000
```

### Testing
```bash
# Health check
curl http://localhost:8000/health

# API documentation
open http://localhost:8000/docs

# Test Celery task
python -c "from app.tasks.sync_tasks import sync_all_enabled; sync_all_enabled.delay()"

# Inspect active Celery tasks
celery -A app.tasks.celery_app inspect active
```

## Core Sync Logic

Located in `app/services/sync.py` - `NotionSyncEngine` class:

1. **Mirror Creation** (`_create_mirror_database`):
   - Creates target database in specified Notion page
   - Clones only visible properties from source database schema

2. **Source → Target Sync** (`_sync_source_to_target`):
   - Queries source database with row filters
   - Filters properties based on `PropertyMapping.is_visible`
   - Creates/updates pages in target database
   - Maintains `PageMapping` records

3. **Target → Source Sync** (`_sync_target_to_source`):
   - Reads target database pages
   - Updates only `is_writable=True` properties back to source
   - Uses `PageMapping` to match pages

4. **Scheduled Sync**:
   - Celery Beat runs every 5 minutes (configurable in `celery_app.py`)
   - Syncs all configs with `sync_enabled=True`

## API Structure

All routes under `/api/v1` prefix:
- `auth.py`: User registration, login, JWT auth, Notion token storage
- `databases.py`: List Notion databases, get schema, search pages
- `configs.py`: CRUD for DatabaseConfig (with filters, mappings, permissions)
- `sync.py`: Trigger sync, view status/logs, enable/disable sync

Authentication: JWT bearer token in `Authorization: Bearer <token>` header

## Configuration Notes

**Environment Variables (.env):**
- `DATABASE_URL`: PostgreSQL connection (used for both DB and Celery)
- `JWT_SECRET_KEY`: Must be kept consistent between sessions
- `NOTION_CLIENT_ID`, `NOTION_CLIENT_SECRET`: Optional, for OAuth flow
- `FRONTEND_URL`, `CORS_ORIGINS`: CORS configuration

**Notion Integration Setup:**
Users must:
1. Create integration at https://www.notion.so/my-integrations
2. Store token via `/api/v1/auth/notion/token` endpoint
3. Share source databases with the integration in Notion UI

## Common Issues

**ModuleNotFoundError for email-validator:**
```bash
pip install pydantic[email]
```

**PostgreSQL authentication failed:**
- Check password in DATABASE_URL matches PostgreSQL user password
- Default installation often uses `postgres:postgres`

**Celery not processing tasks:**
- Verify PostgreSQL is running (Celery uses it as broker)
- Check broker URL has `db+postgresql://` prefix in `celery_app.py`
- Ensure Celery worker process is running

**Notion API errors:**
- Verify integration token is stored for user
- Confirm databases are shared with integration in Notion
- Check token hasn't been revoked

**CORS issues in development:**
- FastAPI's CORSMiddleware doesn't properly handle `allow_origins=["*"]`
- Solution: Use custom `SimpleCORSMiddleware` in `app/main.py`
- The custom middleware manually handles OPTIONS preflight requests and adds CORS headers to all responses

## Windows-Specific Notes

- Use `venv\Scripts\activate` instead of `source venv/bin/activate`
- PostgreSQL service: `postgresql-x64-17`
- Use `python.exe` explicitly for commands when needed
- Virtual environment executables in `venv\Scripts\` (e.g., `venv\Scripts\alembic.exe`)

## Testing

**Automated Testing:**
- `test_app.py`: Automated API tests using curl from WSL to Windows
- Tests registration, login, authentication, and basic endpoints
- Run: `python test_app.py`

**Playwright Testing (WSL → Windows):**
- Playwright MCP server runs in WSL
- Accesses Windows application via host IP (e.g., `172.28.144.1:3000`)
- Tests full UI flow: registration, login, dashboard navigation
- Find Windows host IP: `ip route | grep default | awk '{print $3}'`
