# BorderWise AI - System Architecture Document

## 1. Executive Overview

**BorderWise AI** is a competition-quality cross-border financial copilot designed specifically for international students. Moving abroad introduces complex, opaque financial challenges: multi-currency cash flows, hidden foreign exchange (FX) markup, staggered tuition payment schedules, fluctuating living expenses, and confusing transfer fees.

BorderWise AI solves this by providing:
- Real-time multi-currency expense & tuition planning
- Transparent transfer cost comparison (decoupling mid-market rate, markup margin, and flat wire fees)
- Cash-flow runway forecasting across home and destination currencies
- Personalized, actionable financial recommendations generated via an AI Copilot engine (with full offline deterministic fallback)

---

## 2. Monorepo Structure

The project is structured as a modular monorepo:

```text
fintech-hackathon/
├── backend/                  # Python 3.12+ FastAPI backend service
│   ├── app/
│   │   ├── api/              # API route controllers (versioned endpoints)
│   │   │   ├── v1/
│   │   │   │   ├── health.py          # System health & diagnostic status (/health, /api/health)
│   │   │   │   ├── demo.py            # Seeded demo scenario (/demo/scenario)
│   │   │   │   ├── finance.py         # Overview, 90-day forecast, funding-gap analysis
│   │   │   │   ├── transfers.py       # Transfer comparison benchmark
│   │   │   │   ├── recommendations.py # Deterministic prioritized financial recommendations
│   │   │   │   └── calculator.py      # Quick FX calculator
│   │   │   └── router.py              # Top-level API router (/api/v1)
│   │   ├── core/             # Application configuration & database lifecycle
│   │   │   ├── config.py              # Pydantic BaseSettings & env resolution
│   │   │   └── database.py            # SQLAlchemy 2.x engine & session management
│   │   ├── models/           # SQLAlchemy 2.x ORM entity definitions
│   │   │   ├── base.py                # UTC timestamped declarative base
│   │   │   └── profile.py             # Student profile & explicit ISO currencies
│   │   ├── schemas/          # Pydantic v2 validation models
│   │   │   ├── common.py              # Currency codes, Money amounts, Dated FX quotes
│   │   │   ├── profile.py             # Balances, income, expenses, tuition, remittances
│   │   │   ├── forecast.py            # 90-day timeline, daily balances, shortfalls, completeness
│   │   │   ├── funding_gap.py         # Multi-currency positions, dated FX remedies, staleness
│   │   │   ├── transfers.py           # Provider benchmark quotes & fee decomposition
│   │   │   ├── recommendations.py     # Prioritized quantitative advice DTOs
│   │   │   └── overview.py            # Financial snapshot summary
│   │   ├── services/         # Pure business logic & financial calculations
│   │   │   ├── fx_service.py          # Dated quotes, staleness checks, provenance tracking
│   │   │   ├── demo_scenario_service.py # Seeded synthetic scenario (Aarav Sharma)
│   │   │   ├── forecast_service.py    # 90-day multi-currency timeline & shortfall engine
│   │   │   ├── funding_gap_service.py # Multi-currency obligation audit (zero silent merges)
│   │   │   ├── transfer_service.py    # Multi-provider benchmarks & SLA delivery models
│   │   │   └── recommendation_service.py # Deterministic prioritized recommendation engine
│   │   └── ai/               # AI orchestration & Copilot adapters
│   │       ├── adapter.py             # LLM interface definition
│   │       ├── mock_copilot.py        # Deterministic heuristic copilot (0 API keys needed)
│   │       └── __init__.py            # Adapter factory with offline fallback
│   ├── tests/                # Automated test suite (Pytest + HTTPX)
│   │   ├── conftest.py                # Fixtures & in-memory test DB
│   │   ├── test_api_endpoints.py      # Route integration tests for all 7 endpoints
│   │   ├── test_domain_funding_gap.py # Multi-currency separation, deadlines, zero balances
│   │   ├── test_domain_forecast_recs.py # 90-day forecast, shortfall detection, recommendations
│   │   ├── test_domain_money_fx.py    # Money arithmetic, stale FX detection, parity
│   │   ├── test_domain_transfers.py   # Fee decomposition, SLA delivery, provenance
│   │   ├── test_financial_calc.py     # Math validation tests
│   │   └── test_health.py             # Health endpoint tests
│   ├── requirements.txt      # Production dependencies
│   └── .env.example          # Backend environment template
│
├── frontend/                 # React 19 + TypeScript + Vite single page application
│   ├── src/
│   │   ├── components/       # Reusable UI components & layouts
│   │   ├── services/         # API client & backend integration
│   │   ├── types/            # TypeScript interfaces matching backend schemas
│   │   ├── App.tsx           # Main application view & dashboard
│   │   ├── App.css           # Component styles
│   │   └── index.css         # Base tokens and typography
│   ├── package.json          # Frontend dependencies & scripts
│   └── vite.config.ts        # Vite configuration & proxy settings
│
├── docs/                     # Architecture & product documentation
│   └── architecture.md       # Architectural blueprint & design decisions
│
├── evidence/                 # Verification logs, test results & submission artifacts
│   └── task1_foundation.md   # Initial foundation verification logs
│
├── .gitignore                # Global ignore rules
├── .env.example              # Monorepo environment blueprint
└── README.md                 # Complete project guide and setup instructions
```

---

## 3. Core Architectural Principles & Separation of Concerns

### A. Strict Layer Separation
1. **API Layer (`backend/app/api`)**:
   - Thin HTTP controllers.
   - Responsible strictly for status codes, request routing, dependency injection (`Depends(get_db)`), and schema serialization.
   - Zero business calculations or raw SQL queries inside route functions.

2. **Domain & Calculation Services (`backend/app/services`)**:
   - Pure, testable business logic.
   - Handles multi-currency conversions, fee breakdown, tuition payment phasing, and runway calculations.
   - **Crucial Rule**: All financial math uses Python's `Decimal` with explicit quantizing to prevent IEEE-754 floating-point inaccuracies.

3. **Data Layer (`backend/app/models` & `backend/app/core/database.py`)**:
   - SQLAlchemy 2.0 ORM with declarative mapping (`Mapped[...]` and `mapped_column[...]`).
   - Standardized UTC timestamps via a shared base mixin.
   - Normalized storage of ISO-4217 3-letter currency codes (e.g., `USD`, `INR`, `GBP`, `CAD`, `EUR`, `AUD`).

4. **AI Orchestration Layer (`backend/app/ai`)**:
   - Provider-agnostic adapter interface (`AICopilotAdapter`).
   - Built-in **Deterministic Heuristic Copilot** generates insightful, structured financial guidance using financial rules without requiring any external network calls or paid API keys.
   - Pluggable external adapters (e.g. Gemini / OpenAI) activate smoothly when valid keys are configured in the environment.

5. **Frontend Architecture (`frontend/src`)**:
   - Clean, reactive component tree in React + TypeScript.
   - Centralized typed API service layer with retry and graceful error states.
   - Live backend health monitoring indicator.

---

## 4. Financial Calculation Engine Blueprint

Cross-border calculations must be 100% transparent:
- **Mid-Market FX Rate ($R_{mid}$)**: The true interbank exchange rate.
- **Provider Exchange Rate ($R_{prov}$)**: $R_{mid} \times (1 - \text{markup})$.
- **Transfer Fee Breakdown**:
  $$\text{Total Cost} = \text{Upfront Fixed Fee} + (\text{Transfer Amount} \times \text{Markup Percentage})$$
- **True Effective Cost**: Displayed in home currency and percentage points, enabling students to compare traditional wire transfers vs. digital FX providers.
- **Runway & Cash Flow**:
  $$\text{Months of Runway} = \frac{\text{Total Available Destination Funds} - \text{Remaining Tuition}}{\text{Projected Monthly Living Expenses}}$$

---

## 5. Security & Engineering Standards

- **No Secrets in Source Control**: All configuration managed via `.env` with `.env.example` templates.
- **No Direct Banking Integrations**: Uses synthetic demonstration datasets and simulated quotes; no real PII or bank credentials required or stored.
- **CORS Safeguards**: Explicitly configured for local development (`http://localhost:5173`, `http://127.0.0.1:5173`).
- **Defensive Input Validation**: Strict Pydantic models with bounds checking (positive amounts, recognized currency codes).

---

## 6. Testing Strategy

- **Unit Testing**: Tests every financial calculation method with edge cases (zero values, high numbers, decimal rounding).
- **Integration Testing**: Tests FastAPI endpoints using `httpx.AsyncClient` / `TestClient`.
- **System Verification**: Automated health checks ensuring backend, database connection, and frontend inter-communication work smoothly.
