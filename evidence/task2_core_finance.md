# Evidence: Task 2 - Core Financial Domain Implementation

## 1. Overview
This document records the completion, test execution, and API validation of the **Core Financial Domain** for BorderWise AI.

- **Timestamp**: 2026-10-13T01:35:00+06:00
- **Scope**: Profile, 90-day Cash Flow Forecast, Funding-Gap Analysis, Transfer Comparison, Deterministic Recommendation Engine.
- **Rule Compliance**: Zero frontend modifications; 100% backend financial domain implementation in Python/FastAPI with Decimal precision, dated FX quotes, and zero live external API claims.

---

## 2. Implemented Features & Endpoints

| Endpoint | Method | Domain Service | Key Capabilities |
| :--- | :--- | :--- | :--- |
| `/api/health` | GET | `app.api.v1.health` | Diagnostic probe verifying DB session, settings, and runtime. |
| `/api/v1/demo/scenario` | GET | `demo_scenario_service` | Seeded synthetic student profile (Aarav Sharma, Northeastern Univ, Fall 2026). |
| `/api/v1/finance/overview` | GET | `finance_service` | Separated currency balances, days to tuition, 30/90-day obligations, local runway. |
| `/api/v1/finance/forecast` | POST | `forecast_service` | 90-day projection, daily balances, shortfall event detection, data completeness audit. |
| `/api/v1/finance/funding-gap` | POST | `funding_gap_service` | Strict multi-currency separation (NEVER merged), dated FX quote with provenance, stale quote flagging. |
| `/api/v1/transfers/compare` | POST | `transfer_service` | Provider benchmark comparison (Traditional Wire Bank vs Wise vs Campus Partner vs P2P), fee decomposition, delivery time SLA. |
| `/api/v1/recommendations` | GET | `recommendation_service` | Prioritized, quantitative financial recommendations with urgency, assumptions, uncertainty, and disclaimers. |

---

## 3. Automated Test Suite Results

Command:
```powershell
.\backend\.venv\Scripts\pytest.exe -v
```

Output:
```text
============================= test session starts =============================
platform win32 -- Python 3.14.2, pytest-9.1.1, pluggy-1.6.0
rootdir: E:\programming\Projects\hackathon\Fintech hackathon\backend
plugins: anyio-4.15.1, asyncio-1.4.0
collected 31 items

tests/test_api_endpoints.py::test_api_health_endpoint PASSED             [  3%]
tests/test_api_endpoints.py::test_demo_scenario_endpoint PASSED          [  6%]
tests/test_api_endpoints.py::test_finance_overview_endpoint PASSED       [  9%]
tests/test_api_endpoints.py::test_finance_forecast_endpoint PASSED       [ 12%]
tests/test_api_endpoints.py::test_finance_funding_gap_endpoint PASSED    [ 16%]
tests/test_api_endpoints.py::test_transfers_compare_endpoint PASSED      [ 19%]
tests/test_api_endpoints.py::test_recommendations_endpoint PASSED        [ 22%]
tests/test_domain_forecast_recs.py::test_forecast_distinguishes_actual_from_projected PASSED [ 25%]
tests/test_domain_forecast_recs.py::test_forecast_detects_shortfall_event PASSED [ 29%]
tests/test_domain_forecast_recs.py::test_recommendation_engine_outputs_prioritized_items PASSED [ 32%]
tests/test_domain_funding_gap.py::test_currencies_are_never_silently_combined PASSED [ 35%]
tests/test_domain_funding_gap.py::test_funding_gap_detected_with_tuition PASSED [ 38%]
tests/test_domain_funding_gap.py::test_zero_balances_edge_case PASSED    [ 41%]
tests/test_domain_funding_gap.py::test_tuition_deadline_timing PASSED    [ 45%]
tests/test_domain_funding_gap.py::test_missing_data_completeness_scoring PASSED [ 48%]
tests/test_domain_funding_gap.py::test_stale_quote_flagging_in_funding_gap PASSED [ 51%]
tests/test_domain_money_fx.py::test_money_arithmetic_precision PASSED    [ 54%]
tests/test_domain_money_fx.py::test_currency_rate_precision PASSED       [ 58%]
tests/test_domain_money_fx.py::test_same_currency_parity PASSED          [ 61%]
tests/test_domain_money_fx.py::test_stale_rate_detection PASSED          [ 64%]
tests/test_domain_money_fx.py::test_fresh_rate_has_no_warning PASSED     [ 67%]
tests/test_domain_transfers.py::test_transfer_fee_comparison_decomposition PASSED [ 70%]
tests/test_domain_transfers.py::test_digital_specialist_cheaper_than_traditional_bank PASSED [ 74%]
tests/test_financial_calc.py::test_decimal_rounding_precision PASSED     [ 77%]
tests/test_financial_calc.py::test_mid_market_rates PASSED               [ 80%]
tests/test_financial_calc.py::test_transfer_comparison_calculation PASSED [ 83%]
tests/test_financial_calc.py::test_runway_calculation PASSED             [ 87%]
tests/test_financial_calc.py::test_api_compare_transfers_endpoint PASSED [ 90%]
tests/test_health.py::test_root_endpoint PASSED                          [ 93%]
tests/test_health.py::test_top_level_health_endpoint PASSED              [ 96%]
tests/test_health.py::test_api_v1_health_endpoint PASSED                 [100%]

======================== 31 passed in 0.22s ========================
```

---

## 4. Live Server HTTP Validation Log
All 7 routes verified live on `127.0.0.1:8000`:
- `GET /api/health` ➔ 200 OK (`status: "healthy"`)
- `GET /api/v1/demo/scenario` ➔ 200 OK (`Aarav Sharma`, `is_synthetic_demo: true`)
- `GET /api/v1/finance/overview` ➔ 200 OK (Tuition $14,500 due in 31 days)
- `POST /api/v1/finance/forecast` ➔ 200 OK (24 timeline events, 1 detected shortfall event)
- `POST /api/v1/finance/funding-gap` ➔ 200 OK (`COVERABLE_VIA_TRANSFER`, dated quote source documented)
- `POST /api/v1/transfers/compare` ➔ 200 OK (Wise recommended, 3,400 INR savings vs traditional wire bank)
- `GET /api/v1/recommendations` ➔ 200 OK (4 prioritized quantitative recommendations, zero investment claims)
