# QuickStart - NotionShare

Guida rapida per avviare NotionShare in locale.

## Setup in 5 Minuti

### 1. Prerequisiti

```bash
# Installa PostgreSQL
# macOS: brew install postgresql
# Ubuntu: sudo apt install postgresql
# Windows: Scarica da https://www.postgresql.org/download/windows/

# Python 3.11+
python --version
```

### 2. Setup Database

```bash
# Crea database
createdb notionshare

# Verifica
psql -l | grep notionshare
```

### 3. Backend Setup

```bash
cd notionshare/backend

# Virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Installa dipendenze
pip install -r requirements.txt

# Configura environment
cp .env.example .env

# Modifica .env (usa il tuo editor preferito)
# Cambia almeno:
# - DATABASE_URL
# - JWT_SECRET_KEY (genera una stringa random)
# - NOTION_CLIENT_ID e NOTION_CLIENT_SECRET (opzionale per OAuth)
```

### 4. Avvia Servizi

Apri 3 terminali:

**Terminale 1 - Backend API**
```bash
cd notionshare/backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminale 2 - Celery Worker**
```bash
cd notionshare/backend
source venv/bin/activate
celery -A app.tasks.celery_app worker --loglevel=info
```

**Terminale 3 (opzionale) - Celery Beat**
```bash
cd notionshare/backend
source venv/bin/activate
celery -A app.tasks.celery_app beat --loglevel=info
```

### 5. Frontend

**Terminale 4**
```bash
cd notionshare/frontend
python -m http.server 3000
```

### 6. Primo Accesso

1. Apri http://localhost:3000
2. Clicca "Register" e crea un account
3. Login
4. Clicca "Setup Notion Token"
5. Vai su https://www.notion.so/my-integrations
6. Crea una "New integration"
7. Copia il token e incollalo nell'app
8. Condividi i tuoi database Notion con l'integration
9. Torna all'app e crea la tua prima configurazione!

## Test API

```bash
# Health check
curl http://localhost:8000/health

# API docs (browser)
open http://localhost:8000/docs
```

## Comandi Utili

```bash
# Crea migrazione database
cd backend
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head

# Reset database
dropdb notionshare
createdb notionshare
alembic upgrade head

# Logs Celery
celery -A app.tasks.celery_app inspect active

# Test Celery task
python -c "from app.tasks.sync_tasks import sync_all_enabled; sync_all_enabled.delay()"
```

## Troubleshooting

### "ModuleNotFoundError"
```bash
# Assicurati di essere nel venv
source venv/bin/activate
pip install -r requirements.txt
```

### "Connection refused" (PostgreSQL)
```bash
# Verifica che PostgreSQL sia in esecuzione
pg_isready

# Windows: verifica nei servizi Windows
# macOS/Linux: brew services list
```

### "Invalid token"
- Il JWT_SECRET_KEY in .env deve essere lo stesso tra sessioni
- Fai logout e login di nuovo

### Notion API errors
- Verifica che l'Integration Token sia corretto
- Assicurati di aver condiviso i database con l'integration:
  1. Apri il database in Notion
  2. Click "•••" in alto a destra
  3. "Add connections"
  4. Seleziona la tua integration

## Prossimi Passi

- Leggi [README.md](README.md) per dettagli completi
- Consulta [notion-share-project.md](../notion-share-project.md) per l'architettura
- Esplora le API su http://localhost:8000/docs
