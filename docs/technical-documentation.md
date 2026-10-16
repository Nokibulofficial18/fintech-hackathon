# BorderWise AI — Comprehensive Technical Documentation
**AI-Powered Cross-Border Financial Command Center & Decision-Support Copilot for International Students**

---

## 1. Executive Summary & Problem Domain

### 1.1 The Cross-Border Student Dilemma
International students living abroad face a uniquely stressful financial problem: **fragmented, multi-currency cash flows operating across mismatched banking regimes**. For a Bangladeshi student studying in China (the core scenario modeled in BorderWise AI):
1. **Currency Fracture**: Daily living expenses and university tuition are denominated in **Chinese Yuan (CNY / RMB)**, while the student's family support, personal savings, or sponsor pledges originate in **Bangladeshi Taka (BDT)** in Dhaka.
2. **Asymmetric Timing & Deadlines**: University tuition (e.g., ¥24,000.00 CNY) carries strict administrative deadlines. Missing a payment triggers enrollment holds, late penalties, or visa status reviews. However, cross-border remittances typically take 2 to 5 business days to clear correspondent banking channels.
3. **Deceptive Fee Structures & Hidden Markups**: Remittance providers and commercial banks frequently advertise "Zero Commission" or "Low Fixed Wire Fees," while hiding significant profit margins in opaque foreign exchange (FX) markups (the spread between mid-market rates and customer buy rates).
4. **Funding Gap Ambiguity**: Traditional banking portals show only current account balances. They fail to project whether available funds plus expected stipends will cover upcoming living expenses *and* large semester tuition commitments over a 90-day planning horizon.

### 1.2 BorderWise AI Solution Overview
BorderWise AI acts as a **grounded financial copilot and command center**. It combines:
- **Pure Decimal Financial Modeling**: Eliminates IEEE-754 floating-point inaccuracies using exact decimal arithmetic.
- **90-Day Multi-Currency Cash-Flow Forecasting**: Segregates verified liquid starting balances from projected income and expenditures.
- **Transparent Fee Decomposition**: Deconstructs transfer quotes into upfront flat fees, correspondent deductions, and hidden FX margins.
- **AI-Driven Advisory with Deterministic Guardrails**: A Google Gemini–powered Copilot orchestrating deterministic calculation tools, with zero autonomous payment capabilities and 100% offline fallback reliability.
- **Trilingual Localization Engine**: Native support for English (`en`), Bengali (`bn`, বাংলা), and Simplified Chinese (`zh`, 简体中文) with Latin digit preservation for wire security.

---

## 2. System Architecture & Monorepo Topology

### 2.1 Monorepo Structure
```text
Fintech hackathon/
├── backend/                             # Python 3.12+ / 3.14 FastAPI Application
│   ├── app/
│   │   ├── ai/                          # AI Copilot & LLM Orchestration
│   │   │   ├── orchestrator.py          # Gemini API adapter & function-calling engine
│   │   │   ├── mock_copilot.py          # Deterministic offline heuristic engine
│   │   │   └── tools.py                 # Structured tool declarations
│   │   ├── api/                         # API Controllers & Routing
│   │   │   ├── router.py                # Central API router aggregation (/api/v1)
│   │   │   └── v1/
│   │   │       ├── health.py            # Diagnostic health endpoints (/health, /api/v1/health)
│   │   │       ├── demo.py              # Synthetic scenario seeding & reset (/demo/scenario)
│   │   │       ├── finance.py           # Overview, 90-day forecast, funding-gap analysis
│   │   │       ├── transfers.py         # Multi-provider transfer comparison
│   │   │       ├── recommendations.py   # Prioritized actionable financial advice
│   │   │       ├── assistant.py         # AI copilot chat interface
│   │   │       └── calculator.py        # Currency conversion utilities
│   │   ├── core/                        # Configuration & Database Lifecycle
│   │   │   ├── config.py                # Pydantic BaseSettings & environment loading
│   │   │   └── database.py              # SQLAlchemy engine & session factory
│   │   ├── models/                      # SQLAlchemy 2.0 ORM Declarations
│   │   │   ├── base.py                  # Declarative base with UTC timestamps
│   │   │   └── profile.py               # Student profile & currency entities
│   │   ├── schemas/                     # Pydantic v2 Serialization & Validation Schemas
│   │   │   ├── common.py                # Currency enums, Money amounts, FX quotes
│   │   │   ├── profile.py               # Balances, income, expenses, tuition, remittances
│   │   │   ├── forecast.py              # 90-day cash flow, timeline events, completeness
│   │   │   ├── funding_gap.py           # Shortfall analysis, remedy breakdown, staleness
│   │   │   ├── transfers.py             # Transfer quotes, fee breakdown, SLA models
│   │   │   ├── recommendations.py       # Actionable roadmap recommendation DTOs
│   │   │   └── overview.py              # Financial snapshot summary
│   │   └── services/                    # Pure Domain Logic & Financial Calculations
│   │       ├── demo_scenario_service.py # Synthetic scenario generator (Tanvir Hasan)
│   │       ├── financial_calc.py        # Decimal FX & conversion calculations
│   │       ├── fx_service.py            # Central FX rate cache & staleness checks
│   │       ├── forecast_service.py      # 90-day timeline & daily balance projection
│   │       ├── funding_gap_service.py   # Mathematical funding gap derivation
│   │       ├── transfer_service.py      # Benchmark comparison & fee decomposition
│   │       └── recommendation_service.py# Prioritized roadmap generator
│   ├── tests/                           # Pytest Automated Test Suite (63 tests)
│   │   ├── conftest.py                  # Pytest fixtures & test clients
│   │   ├── test_api_endpoints.py        # Controller integration tests
│   │   ├── test_assistant_copilot.py    # Copilot & tool execution tests
│   │   ├── test_demo_scenario_china_bd_e2e.py # China-BD scenario E2E tests
│   │   ├── test_domain_forecast_recs.py # Forecast & recommendation tests
│   │   ├── test_domain_funding_gap.py   # Shortfall calculation tests
│   │   ├── test_domain_money_fx.py      # FX math & staleness tests
│   │   ├── test_domain_transfers.py     # Fee decomposition & quote tests
│   │   ├── test_financial_calc.py       # Arithmetic validation tests
│   │   ├── test_health.py               # Health probe tests
│   │   └── test_security_review.py      # Security boundary & validation tests
│   └── requirements.txt                 # Backend Python dependencies
│
├── frontend/                            # React 19 + TypeScript + Vite Client
│   ├── src/
│   │   ├── components/                  # UI Components
│   │   │   ├── TopBar.tsx               # Top header, profile, breadcrumbs, language selector
│   │   │   ├── Sidebar.tsx              # Desktop & mobile navigation drawer
│   │   │   ├── TabNav.tsx               # Top-level tab navigation switcher
│   │   │   ├── FinancialOverview.tsx    # Dashboard, KPI cards, countdown, chart, timeline
│   │   │   ├── TransferComparison.tsx   # Calculator, provider cards, fee breakdown table
│   │   │   ├── AICopilot.tsx            # Interactive chat, prompt chips, tool inspection
│   │   │   ├── ActionPlan.tsx           # Prioritized roadmap, simulation controls
│   │   │   ├── DataTransparencyModal.tsx# Provenance matrix & audit breakdown
│   │   │   └── LanguageSelector.tsx     # Compact accessible language dropdown
│   │   ├── i18n/                        # Multilingual Internationalization System
│   │   │   ├── types.ts                 # Supported languages & language metadata
│   │   │   ├── context.ts               # React I18nContext definition
│   │   │   ├── useTranslation.ts        # Fast-refresh compliant consumer hook
│   │   │   ├── I18nContext.tsx          # I18nProvider component with localStorage sync
│   │   │   ├── translations/
│   │   │   │   ├── en.ts                # English canonical schema dictionary
│   │   │   │   ├── bn.ts                # Bengali translation dictionary (100% parity)
│   │   │   │   └── zh.ts                # Simplified Chinese dictionary (100% parity)
│   │   │   └── __tests__/
│   │   │       └── i18nParity.ts        # Automated key coverage & numeral safety tests
│   │   ├── services/
│   │   │   └── api.ts                   # Typed HTTP client communicating with backend
│   │   ├── types/
│   │   │   └── api.ts                   # TypeScript interfaces matching backend models
│   │   ├── utils/
│   │   │   └── formatters.ts            # Intl.NumberFormat & Intl.DateTimeFormat utilities
│   │   ├── App.tsx                      # Root component & tab orchestrator
│   │   ├── main.tsx                     # Entry point & I18nProvider mounting
│   │   └── index.css                    # Design system tokens, typography, component styles
│   ├── index.html                       # HTML5 entry with Google Fonts preloads
│   ├── package.json                     # Frontend scripts & dependencies
│   ├── tsconfig.json                    # TypeScript compiler configuration
│   └── vite.config.ts                   # Vite bundler configuration & proxy settings
│
├── docs/                                # Project Specifications & Blueprints
│   ├── architecture.md                  # High-level architecture summary
│   ├── technical-documentation.md       # Full technical documentation (this document)
│   ├── security-self-assessment.md      # Threat modeling & security posture
│   └── test-plan.md                     # Verification plan & test matrix
│
├── evidence/                            # Task validation logs & test runs
└── README.md                            # Quickstart & onboarding guide
```

---

## 3. Data Models & API Specifications

### 3.1 Currency & Enumeration Standards
- **Supported ISO-4217 Currency Codes**:
  - `CNY`: Chinese Yuan (RMB) — Primary study currency in China.
  - `BDT`: Bangladeshi Taka — Primary home currency in Bangladesh.
  - Secondary/Reference: `USD`, `EUR`, `GBP`, `INR`, `CAD`, `AUD`, `SGD`.
- **Quote Types**: `SIMULATED` (deterministic reference rates), `INDICATIVE` (partner market benchmark).
- **Recommendation Priorities**: `CRITICAL`, `HIGH`, `MEDIUM`.

### 3.2 Key Data Schemas (Pydantic v2 / TypeScript Interfaces)

#### 1. Student Profile Data (`StudentProfileData`)
```typescript
interface StudentProfileData {
  student_id: string;             // e.g. "demo-student-china-tanvir"
  full_name: string;              // "Tanvir Hasan"
  home_country: string;           // "Bangladesh"
  study_country: string;          // "China"
  home_currency: 'BDT';
  study_currency: 'CNY';
  university_name: string;        // "Tsinghua University"
  program_name: string;           // "M.Sc. in Computer Science and Technology"
  intake_term: string;            // "Fall 2026"
}
```

#### 2. Account Balance (`AccountBalance`)
```typescript
interface AccountBalance {
  account_name: string;           // e.g. "China Student Living Account (ICBC Beijing)"
  currency: 'CNY' | 'BDT';
  actual_balance: string;         // Exact stringified decimal: "8500.00"
  as_of_date: string;             // "2026-10-15"
  is_projected: boolean;          // false for verified liquid starting balances
}
```

#### 3. Funding Gap Analysis (`FundingGapResponse`)
```typescript
interface FundingGapResponse {
  as_of_date: string;
  study_currency: 'CNY';
  home_currency: 'BDT';
  target_currency_tuition_due: string;         // "24000.00"
  target_currency_liquid_balance: string;      // "8500.00"
  target_currency_expected_income: string;     // "3500.00"
  target_currency_shortfall_amount: string;    // "15300.00"
  target_currency_has_shortfall: boolean;      // true
  home_currency_liquid_balance: string;        // "350000.00"
  home_currency_planned_remittance: string;    // "250000.00"
  home_currency_shortfall_equivalent: string;  // "257805.00"
  is_covered_by_home_funds: boolean;           // true
  applied_exchange_rate: string;               // "16.8500"
  rate_timestamp_utc: string;
  has_stale_rate_warning: boolean;             // false
  rate_warnings: string[];
  remedy_summary: string;
}
```

#### 4. Transfer Compare Response (`TransferCompareResponse`)
```typescript
interface TransferCompareResponse {
  send_amount: string;                        // "1000.00"
  send_currency: 'CNY';
  receive_currency: 'BDT';
  mid_market_rate: string;                    // "16.8500"
  quotes: TransferQuoteItem[];
  quotes_timestamp_utc: string;
  recommended_cheapest: string;               // Provider name
  recommended_fastest: string;                // Provider name
  potential_savings_vs_bank: string;          // Net saving in send_currency
  is_simulated_benchmark: boolean;            // true
}

interface TransferQuoteItem {
  provider_id: string;                        // "alipay-global"
  provider_name: string;                      // "Alipay Cross-Border Remittance"
  service_tier: string;                       // "Mobile Wallet Direct"
  quote_type: 'SIMULATED' | 'INDICATIVE';
  source_amount: string;                      // "1000.00"
  upfront_fee: string;                        // "12.00"
  correspondent_deduction: string;            // "0.00"
  total_fees_send_currency: string;           // "12.00"
  applied_exchange_rate: string;              // "16.7800"
  fx_markup_margin_percent: string;           // "0.42"
  fx_hidden_cost_send_currency: string;       // "4.15"
  net_send_amount: string;                    // "988.00"
  estimated_received_amount: string;          // "16578.64"
  estimated_delivery_time: string;            // "10-30 minutes"
  delivery_sla_minutes: number;               // 30
  is_cheapest: boolean;
  is_fastest: boolean;
  guaranteed_quote_window_seconds: number;    // 1800
}
```

---

## 4. API Endpoints Reference

All endpoints are versioned under `/api/v1` and return standard JSON payloads.

| Method | Endpoint | Description | Request Body / Parameters |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/health` | Comprehensive system health check and component diagnostics. | None |
| `GET` | `/api/v1/demo/scenario` | Retrieves active synthetic student scenario (defaults to Tanvir Hasan). | `?scenario_key=china` (optional) |
| `POST` | `/api/v1/demo/reset` | Resets active in-memory scenario back to pristine synthetic state. | None |
| `GET` | `/api/v1/finance/overview` | Retrieves student overview: balances, tuition, burn, shortfall, runway. | None |
| `GET` | `/api/v1/finance/funding-gap` | Mathematical funding gap model, currency breakdown, and remedies. | None |
| `GET` | `/api/v1/finance/forecast` | 90-day daily projected timeline positions and data completeness score. | None |
| `GET` | `/api/v1/finance/recommendations` | Prioritized financial actions (CRITICAL, HIGH, MEDIUM) with numbers. | None |
| `POST` | `/api/v1/transfers/compare` | Compares multi-provider transfer quotes, calculating transparent fee breakdown. | `TransferCompareRequest`: `{ send_amount, send_currency, receive_currency }` |
| `POST` | `/api/v1/assistant/chat` | AI Copilot conversational engine executing backend analytical tools. | `ChatRequest`: `{ prompt, student_id? }` |

---

## 5. Financial Mathematics & Deterministic Engine

### 5.1 Pure Decimal Arithmetic (Zero IEEE-754 Drift)
In financial engineering, binary floating-point representation (`float` / `double`) creates catastrophic roundoff inaccuracies (e.g., `0.1 + 0.2 = 0.30000000000000004`). In cross-border tuition planning, small roundoff discrepancies can trigger false shortfall warnings.

**BorderWise AI mandates Python's `Decimal` standard throughout:**
- All domain entity amounts (`amount`, `balance`, `rate`, `fee`) are instances of `decimal.Decimal`.
- Serialized to string (`"15300.00"`) across HTTP boundaries.
- Stored and rounded with `ROUND_HALF_UP` to strictly 2 decimal places for currencies and 4 decimal places for exchange rates.

### 5.2 Deterministic Funding Gap Formulation
The funding gap model evaluates in-country liquidity against pending commitments without blending foreign currencies prematurely:

$$\text{Local Liquidity} = \text{Liquid Balance}_{\text{CNY}} + \text{Expected Stipend}_{\text{CNY}}$$

$$\text{Local Commitments} = \text{Tuition Due}_{\text{CNY}} + \text{Monthly Living Burn}_{\text{CNY}}$$

$$\text{Direct Shortfall}_{\text{CNY}} = \max\left(0, \text{Local Commitments} - \text{Local Liquidity}\right)$$

For the active Tanvir Hasan baseline:
- $\text{Tuition Due} = ¥24,000.00$
- $\text{Living Burn} = ¥3,300.00$
- $\text{Liquid Account (ICBC)} = ¥8,500.00$
- $\text{CSC Stipend} = ¥3,500.00$
- $\text{Direct Shortfall} = (24,000.00 + 3,300.00) - (8,500.00 + 3,500.00) = ¥15,300.00\text{ CNY}$

To determine if family funds can remediate the gap:
$$\text{Remittance Equivalent}_{\text{BDT}} = \text{Direct Shortfall}_{\text{CNY}} \times \text{Mid-Market Rate} = 15,300.00 \times 16.8500 = ৳257,805.00\text{ BDT}$$

Since Tanvir's family holds $৳350,000.00\text{ BDT}$ in DBBL Dhaka, the system confirms:
$$\text{is\_covered\_by\_home\_funds} = \text{true}$$

### 5.3 Transfer Fee Decomposition Engine
Traditional transfer applications display only the upfront wire fee and an all-in rate, concealing the true cost of transfer. BorderWise AI decomposes every quote into three explicit components:

1. **Upfront Fee ($F_{\text{upfront}}$)**: Flat transfer charges collected at origination.
2. **Correspondent Fee ($F_{\text{corr}}$)**: Intermediary bank deductions in international SWIFT wires.
3. **Hidden FX Markup Cost ($C_{\text{FX}}$)**: The hidden fee derived from the exchange rate spread relative to mid-market benchmark:
$$C_{\text{FX}} = (A_{\text{send}} - F_{\text{upfront}}) \times \left(1 - \frac{\text{Rate}_{\text{applied}}}{\text{Rate}_{\text{mid}}}\right)$$

4. **Net Received Amount ($A_{\text{receive}}$)**:
$$A_{\text{receive}} = (A_{\text{send}} - F_{\text{upfront}} - F_{\text{corr}}) \times \text{Rate}_{\text{applied}}$$

---

## 6. AI Copilot Orchestrator & Tool Calling Engine

### 6.1 Copilot Operational Architecture
The Copilot operates on a **grounded tool-calling architecture**:
1. **User Query Ingestion**: The student sends a query (e.g. *"Can I cover my upcoming tuition?"*).
2. **Gemini Tool Invocation**: If a `GEMINI_API_KEY` is present, the model evaluates available financial tool schemas:
   - `get_student_overview`
   - `get_funding_gap_analysis`
   - `compare_transfers`
   - `get_action_recommendations`
3. **Execution Sandbox**: The backend executes the deterministic domain service matching the tool call.
4. **Grounded Response Generation**: The LLM synthesizes the structured tool output into clear, grounded student advice accompanied by:
   - **Tool Provenance Tag**: Explaining which mathematical tool was run.
   - **Explicit Assumptions Strip**: Highlighting FX rates and timelines used.
   - **Action Step Deep-Link**: Navigating the student directly to actionable roadmap items.
5. **Deterministic Offline Fallback**: If the external Gemini API is unreachable, times out, or has no API key configured, the system immediately switches to `mock_copilot.py`. This heuristic engine parses key intents and generates mathematically verified responses directly from the live scenario state without throwing runtime errors.

---

## 7. Multilingual Internationalization (i18n) Engine

### 7.1 Architecture & Design Principles
- **Languages Supported**:
  1. **English (`en`)**: Default international language.
  2. **Bengali (`bn`, বাংলা)**: Primary home language for Bangladeshi students.
  3. **Simplified Chinese (`zh`, 简体中文)**: Primary host language for students studying in China.
- **Zero Heavy Dependencies**: Built using pure React 19 Context (`I18nContext`), avoiding dependency version deadlocks.
- **Strict Key Parity**: Enforced by TypeScript's `TranslationSchema` in [en.ts](file:///e:/programming/Projects/hackathon/Fintech%20hackathon/frontend/src/i18n/translations/en.ts), guaranteeing 100% dictionary match across all languages.
- **Dynamic Parameter Interpolation**: Replaces `{paramName}` tokens cleanly within translated text.
- **Persistence**: Remembers student preference in `localStorage` (`'borderwise_lang'`) and synchronizes `<html lang="...">`.

### 7.2 Numeral Safety with `bn-BD-u-nu-latn`
Standard Bengali locales in browser `Intl.NumberFormat` convert numbers to Eastern Bengali numerals (`১,০০০.০০`), which introduces serious risk of user misinterpretation in cross-border wire transfers (e.g. confusing 1,000 with 10,000).

BorderWise AI resolves this by enforcing the BCP 47 locale extension `bn-BD-u-nu-latn`:
- **Dates, labels, badges, and headers**: Render in native Bengali script (`নভেম্বর ১৫, ২০২৬`, `কমান্ড সেন্টার`).
- **Financial numbers**: Retain unambiguous Latin digits (`¥1,000.00 CNY`, `৳350,000.00 BDT`).
- **Currency Symbols & Codes**: `¥ CNY` and `৳ BDT` remain explicitly paired to guarantee transfer direction is never ambiguous.

---

## 8. Frontend Component Hierarchy & State Management

```text
App (App.tsx)
├── I18nProvider (I18nContext.tsx)
│   ├── Sidebar (Sidebar.tsx)
│   │   ├── Active Corridor Pill [Beijing (CNY) ⇄ Dhaka (BDT)]
│   │   ├── Navigation Menu List
│   │   └── Sync / Reset Demo Controls
│   │
│   └── App Main Content Body
│       ├── TopBar (TopBar.tsx)
│       │   ├── Breadcrumb Hierarchy
│       │   ├── Student Context Badge
│       │   ├── Latency & Health Indicator
│       │   ├── Notifications Drawer
│       │   └── LanguageSelector (LanguageSelector.tsx)
│       │
│       ├── FinancialOverview (FinancialOverview.tsx)
│       │   ├── KPI Summary Cards (CNY Living, BDT Family, Tuition, Shortfall)
│       │   ├── Tuition Countdown Banner
│       │   ├── 90-Day Cash-Flow Area Chart (Recharts)
│       │   └── Timeline Events Filter & List
│       │
│       ├── TransferComparison (TransferComparison.tsx)
│       │   ├── Transfer Calculator Form (Send Amount, Currencies, Swap)
│       │   ├── Quick-Amount Pills (500, 1000, 2500, 5000)
│       │   ├── Central Benchmark Rate Banner
│       │   ├── Potential Savings Callout Banner
│       │   ├── Provider Quote Cards (Alipay, WeChat, Bank of China, RemitAsia)
│       │   ├── Transparent Fee Decomposition Breakdown
│       │   └── Comparison Table View Toggle
│       │
│       ├── AICopilot (AICopilot.tsx)
│       │   ├── Header & Deterministic Mode Badge
│       │   ├── Message History Stream
│       │   │   ├── Formatted Text Parser (Markdown & Bullets)
│       │   │   ├── Executed Tool Inspection Accordion
│       │   │   ├── Assumptions & Disclaimers Strip
│       │   │   └── Action Plan Shortcut Link
│       │   ├── Suggested Question Chips
│       │   └── Prompt Input & Submission Controls
│       │
│       ├── ActionPlan (ActionPlan.tsx)
│       │   ├── Prioritized Roadmap Header (Critical, High)
│       │   ├── Recommendation Cards with Supporting Numbers Matrix
│       │   ├── Interactive Simulation & Acknowledgement Controls
│       │   └── Reset / Restore Dismissed Actions
│       │
│       ├── DataTransparencyModal (DataTransparencyModal.tsx)
│       │   ├── Provenance Matrix Cards (Student Balances, FX Rates, Provider Data)
│       │   ├── Data Completeness Audit Grid
│       │   └── Modeling Assumptions List
│       │
│       └── Global Footer
│           └── Pure Decimal Arithmetic & Zero Autonomous Payment Disclaimers
```

---

## 9. Security, Privacy & Compliance Posture

### 9.1 Zero Autonomous Payment Execution
BorderWise AI strictly operates as an **advisory decision-support platform**:
- It contains **zero integration** with live payment rails (no direct debit, no SWIFT transfer execution, no automated balance deductions).
- All simulation buttons ("Simulate Strategy", "Confirm Scenario") are strictly educational in-browser state updates that display projected impacts without moving real money.

### 9.2 Data Isolation & Privacy
- **Strict Sandbox**: Does not request or store real student banking credentials, bank login cookies, or OAuth tokens.
- **Read-Only Models**: Financial models consume synthetic scenarios or user-supplied planning amounts.
- **CORS Restrictions**: Configured via FastAPI middleware to restrict API access to verified origin endpoints.
- **Input Validation**: Strict Pydantic v2 schemas reject negative amounts, NaN inputs, and unsupported currencies before reaching domain calculations.

---

## 10. Verification, Automated Testing & QA Matrix

The system undergoes strict multi-tier verification before build:

### 10.1 Backend Test Matrix (Pytest: 63 Tests)
- `test_api_endpoints.py`: Integration tests for all 8 REST endpoints (status codes, response schemas).
- `test_assistant_copilot.py`: Evaluates Copilot tool invocation, fallback heuristics, and schema compliance.
- `test_demo_scenario_china_bd_e2e.py`: End-to-end verification of Tanvir Hasan's China-BD scenario, ensuring complete absence of legacy GBP/INR fixtures.
- `test_domain_funding_gap.py`: Validates mathematical shortfall derivation and remedy identification.
- `test_domain_forecast_recs.py`: Tests 90-day daily balance projections and recommendation prioritization.
- `test_domain_money_fx.py`: Evaluates bidirectional currency conversions and stale quote detection (>24 hours).
- `test_domain_transfers.py`: Verifies fee decomposition math, SLA delivery times, and provider sorting.
- `test_financial_calc.py`: Validates pure Decimal arithmetic against floating-point reference tests.
- `test_health.py`: Validates diagnostic health probes.
- `test_security_review.py`: Tests input boundaries, negative transfer values, and CORS headers.

### 10.2 Frontend Quality Checks
- **Linting (`oxlint`)**: Passed with **0 errors and 0 warnings** across 24 files with 116 active rules.
- **Compilation (`tsc -b && vite build`)**: Type-checks all TypeScript files and bundles production assets into `frontend/dist/`.
- **I18n Parity Suite (`i18nParity.ts`)**: Automated TypeScript assertion confirming 100% key parity across `en`, `bn`, and `zh` translation dictionaries.

---

## 11. Local Deployment & Run Guide

### 11.1 Prerequisites
- **Node.js**: v18.0.0 or higher
- **Python**: v3.12 or higher (tested with Python 3.14.2)
- **PowerShell** / Bash

### 11.2 Backend Startup
```powershell
cd backend
# Create virtual environment if needed
python -m venv .venv
& ".venv/Scripts/Activate.ps1"

# Install dependencies
pip install -r requirements.txt

# Start backend server on port 8000
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```
*Backend runs on: `http://127.0.0.1:8000` (API docs at `/docs`).*

### 11.3 Frontend Startup
```powershell
cd frontend
# Install dependencies
npm install

# Start Vite development server on port 5173
npm run dev -- --host 127.0.0.1 --port 5173
```
*Frontend runs on: `http://127.0.0.1:5173`.*

### 11.4 Environment Configuration (`.env`)
Create `.env` in `backend/` if utilizing live Gemini AI:
```ini
ENVIRONMENT=development
CORS_ORIGINS=["http://127.0.0.1:5173","http://localhost:5173"]
GEMINI_API_KEY=your_gemini_api_key_here
```
*(If `GEMINI_API_KEY` is omitted, the backend automatically uses the deterministic heuristic engine without error.)*
