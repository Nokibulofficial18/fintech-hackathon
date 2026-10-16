# Evidence: Task 1 - Monorepo Foundation & Verification

## 1. Overview
This document records the foundational setup and automated verification of **BorderWise AI** for competition judging.

- **Timestamp**: 2026-10-13T01:20:00+06:00
- **Deadline**: October 18, 2026
- **Architecture**: Monorepo with `/backend`, `/frontend`, `/docs`, `/evidence`

---

## 2. Completed Foundation Requirements

1. **Monorepo Structure**:
   - `/backend`: Python 3.12+ / FastAPI, SQLAlchemy 2.x, Pydantic v2, Pytest
   - `/frontend`: React 19, TypeScript, Vite
   - `/docs`: Architecture blueprint and system diagrams
   - `/evidence`: Verification logs, test reports, and validation records
2. **Security & Clean Secrets**:
   - `.gitignore` configured to prevent committing `.env`, virtual environments, SQLite databases, and node_modules.
   - `.env.example` templates provided at monorepo root, backend, and frontend.
   - Zero hardcoded secrets in codebase.
3. **Layer Separation**:
   - `backend/app/api`: HTTP controllers and routers (`/health`, `/api/v1/health`, `/api/v1/calculator`).
   - `backend/app/services`: Pure business logic using Python `Decimal` with `ROUND_HALF_UP` for currency operations (no floating-point rounding errors).
   - `backend/app/models`: SQLAlchemy 2.x models with standardized UTC timestamps and explicit ISO-4217 currency codes.
   - `backend/app/ai`: Decoupled AI Copilot adapter interface with an offline deterministic heuristic copilot that functions without any external API keys.
4. **CORS & Connection**:
   - Configured for local development (`http://localhost:5173`, `http://127.0.0.1:5173`).
   - Health diagnostic probe verifying API, runtime settings, and database query (`SELECT 1`).
5. **Initial Test Suite**:
   - 8 tests passing with Pytest and FastAPI TestClient in `<0.3s`.

---

## 3. Test Run Log

```text
============================= test session starts =============================
platform win32 -- Python 3.14.2, pytest-9.1.1, pluggy-1.6.0
rootdir: E:\programming\Projects\hackathon\Fintech hackathon\backend
plugins: anyio-4.15.1, asyncio-1.4.0
collected 8 items

tests/test_financial_calc.py::test_decimal_rounding_precision PASSED     [ 12%]
tests/test_financial_calc.py::test_mid_market_rates PASSED               [ 25%]
tests/test_financial_calc.py::test_transfer_comparison_calculation PASSED [ 37%]
tests/test_financial_calc.py::test_runway_calculation PASSED             [ 50%]
tests/test_financial_calc.py::test_api_compare_transfers_endpoint PASSED [ 62%]
tests/test_health.py::test_root_endpoint PASSED                          [ 75%]
tests/test_health.py::test_top_level_health_endpoint PASSED              [ 87%]
tests/test_health.py::test_api_v1_health_endpoint PASSED                 [100%]

======================== 8 passed in 0.11s =========================
```
