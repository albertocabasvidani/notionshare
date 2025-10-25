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
- `UserPermission` ↔ `RowFilter`: Many-to-many via `user_permission_row_filters` junction table
- `PageMapping` tracks source page ↔ target page relationships for sync

Critical fields:
- `DatabaseConfig.source_database_id`: Original Notion database
- `DatabaseConfig.parent_page_id`: Parent page where user subpages are created
- `UserPermission.user_page_id`: Dedicated subpage for this guest user
- `UserPermission.target_database_id`: Mirror database in user's subpage
- `UserPermission.row_filters`: User-specific row filters (many-to-many)
- `PropertyMapping.is_visible`: Show in mirror
- `PropertyMapping.is_writable`: Allow edits from mirror back to source

**Row-Level Permissions Architecture:**
- Each guest user gets a dedicated subpage under `DatabaseConfig.parent_page_id`
- Each subpage contains a mirror database with user-specific filtered data
- Row filters are associated with specific users via many-to-many relationship
- Sync engine creates/updates per-user databases with user-specific row filters applied

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

**Per-User Architecture:**
The sync engine creates and maintains separate subpages and mirror databases for each guest user.

1. **User Subpage Creation** (`_create_user_subpage`):
   - Creates dedicated subpage for each `UserPermission` under `DatabaseConfig.parent_page_id`
   - Subpage title: "Shared: {config_name} - {user_email}"
   - Stores subpage ID in `UserPermission.user_page_id`

2. **User Mirror Database Creation** (`_create_user_mirror_database`):
   - Creates mirror database within user's dedicated subpage
   - Clones only visible properties from source database schema (`PropertyMapping.is_visible`)
   - Stores database ID in `UserPermission.target_database_id`

3. **Source → User Target Sync** (`_sync_source_to_user_target`):
   - Queries source database with **user-specific row filters** from `UserPermission.row_filters`
   - Filters properties based on `PropertyMapping.is_visible`
   - Creates/updates pages in user's mirror database
   - Maintains `PageMapping` records for each user's database

4. **User Target → Source Sync** (`_sync_user_target_to_source`):
   - Reads pages from user's mirror database
   - Updates only `is_writable=True` properties back to source
   - Only runs if `UserPermission.access_level == "write"`
   - Uses `PageMapping` to match pages

5. **Page Sharing** (`_ensure_page_shared`):
   - Shares user's subpage with their email via Notion API
   - Marks `UserPermission.notified = True` when shared
   - Note: Current implementation logs sharing intent (Notion API sharing requires workspace permissions)

6. **Scheduled Sync**:
   - Celery Beat runs every 5 minutes (configurable in `celery_app.py`)
   - Syncs all configs with `sync_enabled=True`
   - Processes all `UserPermission` records for each config

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
- Tests full UI flow: registration, login, dashboard navigation, configuration creation, sync
- Find Windows host IP: `ip route | grep default | awk '{print $3}'`

## Known Issues & Fixes

**Frontend Schema Mismatch (FIXED):**
- `config-wizard.html` was sending `filter_type: 'property'` but backend expects `'property_match'`
- Fixed in config-wizard.html:218
- `config-detail.html` was using wrong field names: `source_property_name` instead of `property_name`, `filter_condition`/`filter_value` instead of `operator`/`value`
- Fixed in config-detail.html:119, 96-97

**Row Filter Behavior:**
- Row filters use Notion API query filters: https://developers.notion.com/reference/post-database-query-filter
- If no rows match the filter, ALL rows are synced (Notion API returns all results when filter matches nothing)
- Property filters work correctly: only `is_visible=True` properties are included in mirror database
