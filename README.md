# Loading Sheet

Django + React + PostgreSQL ops portal (order clerks, Esha batches, Ali dispatch, Rashid loading).

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
..\.venv\Scripts\python manage.py seed_packaging_materials
..\.venv\Scripts\python manage.py seed_bundle_compositions
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
| esha     | Clerk123! | Batches + Packaging inventory |
| ali      | Clerk123! | Dispatch trips & orders |
| rashid   | Clerk123! | Loading sheet batch assignment |

- API: `http://127.0.0.1:8000/api`
- App: `http://127.0.0.1:5173`

## Standard carton weights (Rashid ±8% check)

`seed_catalog` sets `Product.standard_carton_weight_kg` and `fill_volume_liters`
(see maps in `backend/catalog/management/commands/seed_catalog.py`).
On the loading sheet, a full standard carton whose entered weight is outside
±8% of the standard blocks save. Rhino 250/500/750 ml B2G1 have no standard
weight yet, so they are not checked.

## Esha fill → Ready stock → Deliver

- Ready stock fill from an active Esha batch deducts liters immediately
  (`bottles × fill_volume_liters`). Free-text batches do not.
- Loading sheet can assign Ready stock or an Esha batch (assign only).
- **Mark delivered** on the Rashid trip deducts Ready stock on-hand and/or
  Esha liters for direct-assign lines.
