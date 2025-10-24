# NotionShare

Applicazione web per condividere parti filtrate di database Notion con utenti esterni, superando i limiti nativi di Notion.

## Caratteristiche

- Filtraggio avanzato di righe e colonne
- Sincronizzazione bidirezionale automatica
- Permessi granulari per utenti esterni
- Dashboard web intuitiva
- API REST completa

## Architettura

- **Backend**: Python 3.11+, FastAPI, SQLAlchemy
- **Database**: PostgreSQL (anche per Celery broker)
- **Task Queue**: Celery
- **Frontend**: HTML/CSS/JavaScript vanilla
- **API Notion**: notion-client SDK

## Setup Locale

### Prerequisiti

- Python 3.11+
- PostgreSQL
- Notion Integration Token

### 1. Clone Repository

```bash
git clone <repo-url>
cd notionshare
```

### 2. Setup Backend

```bash
cd backend

# Crea virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Installa dipendenze
pip install -r requirements.txt

# Copia .env.example e configura
cp .env.example .env
# Modifica .env con le tue credenziali
```

### 3. Configura Database

```bash
# Crea database PostgreSQL
createdb notionshare

# Aggiorna DATABASE_URL in .env
DATABASE_URL=postgresql://user:password@localhost:5432/notionshare
```

### 4. Setup Notion Integration

1. Vai su https://www.notion.so/my-integrations
2. Clicca "New integration"
3. Assegna un nome (es: "NotionShare")
4. Seleziona il workspace
5. Copia il "Internal Integration Token"
6. Condividi i database Notion con l'integration

### 5. Avvia Backend

```bash
# Terminale 1: API Server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminale 2: Celery Worker
celery -A app.tasks.celery_app worker --loglevel=info

# Terminale 3: Celery Beat (scheduler)
celery -A app.tasks.celery_app beat --loglevel=info
```

### 6. Avvia Frontend

```bash
cd ../frontend

# Opzione 1: Python HTTP server
python -m http.server 3000

# Opzione 2: Node.js http-server
npx http-server -p 3000
```

### 7. Accedi all'App

- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs
- API: http://localhost:8000/api/v1

## Utilizzo

### 1. Registrazione e Login

1. Apri http://localhost:3000
2. Registra un nuovo account
3. Fai login

### 2. Configura Notion Token

1. Nel dashboard, clicca "Setup Notion Token"
2. Incolla il tuo Integration Token
3. Salva

### 3. Crea Configurazione

1. Clicca "Create New Configuration"
2. Seleziona il database source
3. Configura filtri sulle righe (es: Status = "Public")
4. Seleziona proprietà visibili/modificabili
5. Specifica la pagina target
6. Aggiungi utenti condivisi (email)
7. Salva

### 4. Sincronizzazione

- **Automatica**: Ogni 5 minuti (configurabile)
- **Manuale**: Clicca "Sync Now" nel dashboard

## Struttura Progetto

```
notionshare/
├── backend/
│   ├── app/
│   │   ├── models/          # SQLAlchemy models
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── routers/         # API endpoints
│   │   ├── services/        # Business logic
│   │   ├── tasks/           # Celery tasks
│   │   ├── utils/           # Utilities
│   │   ├── config.py        # Settings
│   │   ├── database.py      # DB connection
│   │   └── main.py          # FastAPI app
│   ├── requirements.txt
│   ├── runtime.txt
│   └── .env.example
├── frontend/
│   ├── css/
│   ├── js/
│   ├── index.html
│   └── dashboard.html
└── README.md
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Registrazione
- `POST /api/v1/auth/login` - Login
- `GET /api/v1/auth/me` - Info utente
- `POST /api/v1/auth/notion/token` - Salva token Notion

### Databases
- `GET /api/v1/databases/list` - Lista database Notion
- `GET /api/v1/databases/{db_id}/structure` - Schema database
- `GET /api/v1/databases/pages/search` - Cerca pagine

### Configurations
- `GET /api/v1/configs/` - Lista configurazioni
- `POST /api/v1/configs/` - Crea configurazione
- `GET /api/v1/configs/{id}` - Dettagli configurazione
- `PUT /api/v1/configs/{id}` - Aggiorna configurazione
- `DELETE /api/v1/configs/{id}` - Elimina configurazione

### Sync
- `POST /api/v1/sync/{config_id}/trigger` - Trigger sync
- `GET /api/v1/sync/{config_id}/status` - Status sync
- `GET /api/v1/sync/{config_id}/logs` - Log sincronizzazioni
- `PUT /api/v1/sync/{config_id}/enable` - Abilita/disabilita sync

## Deploy Production

### Render.com

1. **Backend Web Service**
   - Build: `pip install -r requirements.txt`
   - Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

2. **Celery Worker**
   - Build: `pip install -r requirements.txt`
   - Start: `celery -A app.tasks.celery_app worker --loglevel=info`

3. **Celery Beat**
   - Start: `celery -A app.tasks.celery_app beat --loglevel=info`

4. **PostgreSQL**: Render PostgreSQL

5. **Redis**: Render Redis

### GitHub Pages (Frontend)

1. Push `frontend/` a repository GitHub
2. Settings → Pages → Source: main/root
3. Aggiorna `API_BASE_URL` in `frontend/js/api.js`

## Troubleshooting

### Database connection failed
- Verifica che PostgreSQL sia in esecuzione
- Controlla DATABASE_URL in .env

### Redis connection refused
- Verifica che Redis sia in esecuzione
- Controlla REDIS_URL in .env

### Notion API errors
- Verifica che l'Integration Token sia corretto
- Assicurati che i database siano condivisi con l'integration

### Sync non funziona
- Verifica che Celery worker e beat siano in esecuzione
- Controlla i log di Celery
- Verifica che sync_enabled sia true

## Sviluppo Futuro

- [ ] Template configurazioni predefinite
- [ ] Supporto webhook Notion
- [ ] Notifiche email
- [ ] Analytics dashboard
- [ ] Export/Import configurazioni
- [ ] Mobile app

## Licenza

MIT

## Supporto

Per problemi o domande, apri un issue su GitHub.
