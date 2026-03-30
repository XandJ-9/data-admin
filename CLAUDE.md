# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Data Admin** is a unified data management platform with Django + DRF backend and Vue3 + Element Plus frontend (RuoYi-Vue3 style). Features include data source management, metadata catalog, online SQL query, data interface services, ETL orchestration, and system administration.

- **Backend**: Django 5.2 + DRF 3.16 + SimpleJWT + drf-spectacular
- **Frontend**: Vue 3.5 + Element Plus 2.10 + Vite 6 + Pinia
- **Database**: SQLite (dev), supports connecting to external MySQL/PostgreSQL/Presto/StarRocks
- **Package Managers**: `uv` (backend Python), `pnpm` (frontend Node.js)

## Quick Start

```bash
# Backend
cd backend && uv pip install -r requirements.txt
python manage.py migrate && python manage.py init_system
python manage.py runserver 0.0.0.0:8000

# Frontend
cd frontend && pnpm install && pnpm dev
```

Default credentials: `admin / admin123`

## Convention Files

| File | Description |
|------|-------------|
| [.claude/rules/backend-conventions.md](.claude/rules/backend-conventions.md) | Backend development patterns, naming, API patterns |
| [.claude/rules/frontend-conventions.md](.claude/rules/frontend-conventions.md) | Frontend API wrappers, component patterns, naming |
| [.claude/rules/creating-modules.md](.claude/rules/creating-modules.md) | Step-by-step guide for creating new modules |
| [.claude/rules/quick-reference.md](.claude/rules/quick-reference.md) | Quick command reference, file locations, endpoints |

## External Documentation

- [backend/README.md](backend/README.md) - Backend API details
- [frontend/README.md](frontend/README.md) - Frontend architecture
- [docs/development-guide.md](docs/development-guide.md) - Full development guide
