# Loading Sheet — Phase 1

Django + React + PostgreSQL order-entry portal for order clerks.

## Setup

1. Copy `.env.example` to `.env` and set DB credentials.
   - Local smoke tests without Postgres password: `USE_SQLITE=True`
   - PostgreSQL: `USE_SQLITE=False` and set `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`

2. Backend (from repo root):

```powershell
.\.venv\Scripts\python -m pip install -r backend\requirements.txt
cd backend
..\.venv\Scripts\python manage.py migrate
..\.venv\Scripts\python manage.py seed_clerks
..\.venv\Scripts\python manage.py seed_catalog
..\.venv\Scripts\python manage.py runserver
```

3. Frontend:

```powershell
cd frontend
npm install
npm run dev
```

## Clerk logins (same portal)

| Username | Password  | Market Visit |
|----------|-----------|--------------|
| ahtisham | Clerk123! | Yes |
| aslam    | Clerk123! | Yes |
| nouman   | Clerk123! | No |
| javeria  | Clerk123! | No |

- API: `http://127.0.0.1:8000/api`
- App: `http://127.0.0.1:5173`
- Each clerk only sees their own orders (and own market visits when enabled).
