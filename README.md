# BorderWise AI 🌐🎓
> **Cross-Border Financial Copilot for International Students (China–Bangladesh Specialization)**  
> *Competition Submission Target: October 18, 2026*

BorderWise AI is an intelligent cross-border financial copilot engineered for international students. Specialized for the China–Bangladesh academic corridor, it helps students studying in China (e.g. Tsinghua University) navigate expenses across Chinese Yuan (CNY / RMB, ¥) and Bangladeshi Taka (BDT, ৳), eliminate foreign exchange confusion, compare remittance costs (e.g. sending 1,000 CNY to Bangladesh or receiving family support from Bangladesh), forecast 90-day cash-flow runway, avoid tuition shortfalls, and receive transparent financial action plans.

---

## 🏗️ Architecture & Technology Stack

The project is structured as a clean monorepo with strict separation of concerns:

- **Backend**: Python 3.12+ with [FastAPI](https://fastapi.tiangolo.com/)
- **Validation**: [Pydantic v2](https://docs.pydantic.dev/) with strong type constraints
- **Database**: SQLite with [SQLAlchemy 2.x](https://www.sqlalchemy.org/) ORM
- **Financial Arithmetic**: Python `Decimal` with explicit half-up rounding (`ROUND_HALF_UP`) to eliminate floating-point precision loss
- **Testing**: [Pytest](https://docs.pytest.org/) and [HTTPX](https://www.python-httpx.org/)
- **AI Orchestration**: Provider-agnostic Copilot Adapter with an offline deterministic heuristic copilot (runs 100% reliably with **zero API keys required**)
- **Frontend**: [React 19](https://react.dev/), [TypeScript](https://www.typescriptlang.org/), [Vite](https://vite.dev/)
- **Styling**: Modern, responsive dark-mode fintech interface with CSS tokens and [Lucide Icons](https://lucide.dev/)

---

## 📁 Repository Structure

```text
fintech-hackathon/
├── backend/                  # FastAPI backend service
│   ├── app/
│   │   ├── api/              # Versioned API routes (/health, /calculator)
│   │   ├── core/             # Configuration & SQLAlchemy 2.x DB session
│   │   ├── models/           # Declarative models with UTC timestamps
│   │   ├── schemas/          # Pydantic validation schemas
│   │   ├── services/         # Pure Decimal business & financial logic
│   │   ├── ai/               # AI Copilot engine & offline fallback
│   │   └── main.py           # Application entrypoint & CORS middleware
│   ├── tests/                # Automated Pytest suite
│   ├── requirements.txt      # Backend Python dependencies
│   └── .env.example          # Backend configuration blueprint
│
├── frontend/                 # React 19 + TypeScript SPA
│   ├── src/
│   │   ├── services/         # Typed API client
│   │   ├── types/            # TypeScript interfaces matching backend DTOs
│   │   ├── App.tsx           # Health diagnostic & transfer probe UI
│   │   └── index.css         # Modern fintech aesthetic system
│   ├── package.json          # Frontend dependencies
│   ├── vite.config.ts        # Vite configuration & dev proxy
│   └── .env.example          # Frontend configuration blueprint
│
├── docs/                     # Architectural documentation
│   └── architecture.md       # Comprehensive system architecture blueprint
│
├── evidence/                 # Verification logs & test outputs
│   └── task1_foundation.md   # Foundation verification and test run log
│
├── .gitignore                # Global ignore rules (secrets, venv, sqlite)
├── .env.example              # Monorepo environment blueprint
└── README.md                 # Setup, run, and architecture guide
```

---

## ⚡ Quickstart Guide

### Prerequisites
- **Python 3.12+** (tested with Python 3.14)
- **Node.js 20+** and **npm**

---

### 1. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment
# Windows:
python -m venv .venv
.\.venv\Scripts\activate

# macOS / Linux:
# python3 -m venv .venv
# source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# (Optional) Copy environment file
cp .env.example .env

# Run automated tests
pytest -v

# Start development server
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

The backend interactive API documentation will be available at:
- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Diagnostic Health**: [http://127.0.0.1:8000/api/v1/health](http://127.0.0.1:8000/api/v1/health)

---

### 2. Frontend Setup

In a separate terminal:

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# (Optional) Copy environment file
cp .env.example .env

# Run TypeScript build check
npm run build

# Start Vite development server
npm run dev
```

The frontend application will be running at [http://localhost:5173](http://localhost:5173).

---

## 🛡️ Engineering & Security Standards

1. **Zero Secrets in Source Control**: All sensitive values are managed through environment variables. Safe defaults and templates are provided in `.env.example`.
2. **Reliable Offline AI**: The AI Copilot uses a deterministic heuristic adapter when no API key is supplied. The entire prototype is fully functional offline.
3. **High-Precision Money Arithmetic**: Never uses floating-point types (`float`) for currency or transfer fee math. All calculations use `Decimal` with two decimal place rounding.
4. **Standardized Timestamps & Currencies**: All stored records utilize timezone-aware UTC timestamps and explicit ISO-4217 3-letter currency codes (e.g. `CNY`, `BDT`, `USD`).
5. **Safe Demonstrations**: Uses synthetic demonstration datasets; does not make real banking payments or require live financial credentials.

---

## 🧪 Automated Testing

Run the automated test suite at any time:

```bash
cd backend
.\.venv\Scripts\pytest.exe -v
```

Current test coverage includes:
- Health diagnostics and database session availability
- Root metadata and CORS verification
- High-precision Decimal monetary rounding
- Mid-market exchange rate resolution
- Multi-provider transfer quote comparisons (wire fees vs. hidden FX markups)
- Cash-flow runway calculation and liquidity warnings

---

## 📅 Roadmap to Competition Submission (Oct 18, 2026)

- [x] **Milestone 1**: Monorepo foundation, clean architecture separation, health probes, CORS, and initial test suite.
- [x] **Milestone 2**: Core financial domain (multi-currency profile, 90-day cash flow forecast, funding gap analysis, transfer comparison, deterministic recommendation engine).
- [x] **Milestone 3**: React + TypeScript modern fintech dashboard (KPI metrics, Recharts cash flow, comparison deck, AI copilot chat, action plan, data transparency audit).
- [ ] **Milestone 4**: Exportable PDF/CSV financial action plan reports.
- [ ] **Milestone 5**: Competition submission packaging and final demo presentation walk-through.
