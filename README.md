# Loading Sheet

Django + React + PostgreSQL ops portal (order clerks + Esha batches).

## Setup

1. Copy `.env.example` to `.env` and set DB credentials.
   - Local smoke tests without Postgres password: `USE_SQLITE=True`
   - PostgreSQL: `USE_SQLITE=False` and set `DB_*`

2. Backend (from repo root):

```powershell
.\.venv\Scripts\python -m pip install -r backend\requirements.txt
cd backend
..\.venv\Scripts\python manage.py migrate
..\.venv\Scripts\python manage.py seed_clerks
..\.venv\Scripts\python manage.py seed_catalog
..\.venv\Scripts\python manage.py seed_batch_products
..\.venv\Scripts\python manage.py runserver
```

3. Frontend:

```powershell
cd frontend
npm install
npm run dev
```

## Logins

| Username | Password  | Portal |
|----------|-----------|--------|
| ahtisham | Clerk123! | Orders + Market Visit |
| aslam    | Clerk123! | Orders + Market Visit |
| nouman   | Clerk123! | Orders |
| javeria  | Clerk123! | Orders |
| esha     | Clerk123! | Batches (Active / New) |

- API: `http://127.0.0.1:8000/api`
- App: `http://127.0.0.1:5173`
