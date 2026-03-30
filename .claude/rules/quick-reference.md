# Quick Reference

## Project Overview

- **Backend**: Django 5.2 + DRF 3.16 + SimpleJWT
- **Frontend**: Vue 3.5 + Element Plus 2.10 + Vite 6 + Pinia
- **Package Managers**: `uv` (backend), `pnpm` (frontend)

## Startup Commands

### Backend
```bash
cd backend
uv pip install -r requirements.txt
python manage.py migrate
python manage.py init_system
python manage.py runserver 0.0.0.0:8000
```

### Frontend
```bash
cd frontend
pnpm install
pnpm dev
```

## Default Credentials

- Username: `admin`
- Password: `admin123`

## API Endpoints

- Backend API: `http://localhost:8000/data-api/`
- Swagger Docs: `http://localhost:8000/api/docs/`
- Frontend Dev: `http://localhost:80` (proxies to backend)

## Backend Modules

| Module | Purpose |
|--------|---------|
| `system` | User, Role, Menu, Dept, Dict, Config |
| `datasource` | External DB connections |
| `dataasset` | Metadata collection, table lineage |
| `dataservice` | SQL query, data interfaces |
| `dataetl` | ETL tasks, executors |
| `monitor` | Server monitoring, logs |
| `dbutils` | Database executor abstraction |

## Key File Locations

| File | Purpose |
|------|---------|
| `apps/system/models.py` | BaseModel (audit fields) |
| `apps/system/views/core.py` | BaseViewSet |
| `apps/system/serializers.py` | BaseModelSerializer (camelCase) |
| `apps/dbutils/factory.py` | Executor factory |
| `apps/common/mixins.py` | Response helpers |
| `config/settings.py` | Django settings |

## Response Format

Success: `{code: 200, msg: '...', data: {...}}` or `{code: 200, rows: [...], total: N}`
Error: `{code: 400|404|500, msg: '...'}`

## External Docs

- Backend: `backend/README.md`
- Frontend: `frontend/README.md`
- Development: `docs/development-guide.md`
