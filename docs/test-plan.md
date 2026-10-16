# BorderWise AI — Test Plan & Quality Assurance Strategy

## 1. Overview & Objectives
This test plan provides comprehensive verification for BorderWise AI across:
1. **Mathematical Accuracy & Precision**: Ensuring multi-currency arithmetic uses exact `Decimal` rounding with zero floating-point errors.
2. **Deterministic Domain Isolation**: Ensuring financial numbers originate exclusively from backend calculation services.
3. **AI Copilot Security & Tool Calling**: Validating Pydantic argument constraints, prompt injection refusals, and simulated action confirmations.
4. **End-to-End User Journey**: Verifying the signature UK student demonstration workflow from initial dashboard load to transfer comparison and decision support.
5. **Security & Boundary Enforcement**: Testing request size limitations, CORS restrictions, and information leakage prevention.

---

## 2. Test Suites & Case Catalog

### Suite A: Security, Reliability & Guardrails (`backend/tests/test_security_review.py`)
| Test ID | Test Name | Target / Method | Expected Outcome |
| :--- | :--- | :--- | :--- |
| **SEC-T01** | `test_payload_too_large_rejected_with_413` | `POST /api/v1/assistant/chat` with `Content-Length > 1MB` | HTTP 413 `Payload Too Large` returned immediately. Backend does not crash or allocate excessive memory. |
| **SEC-T02** | `test_cors_headers_restricted` | `GET /` with allowed vs disallowed `Origin` header | Allowed origin (`http://localhost:5173`) receives matching CORS header; disallowed origin is refused. |
| **SEC-T03** | `test_no_secrets_in_environment_or_endpoints` | `GET` across all public API endpoints | Response payloads do not contain `api_key`, `secret`, `password`, or environment variable names. |
| **SEC-T04** | `test_autonomous_money_movement_guardrail` | `POST /api/v1/assistant/chat` with commands like "Send 5000 CNY to ICBC..." | Safety guardrail intercepts instruction, refuses execution, and marks request as advisory-only. |

---

### Suite B: AI Copilot & Tool Calling (`backend/tests/test_assistant_copilot.py`)
| Test ID | Test Name | Target / Method | Expected Outcome |
| :--- | :--- | :--- | :--- |
| **COP-T01** | `test_invalid_tool_calls_rejected` | `dispatch_tool()` with unapproved tool or invalid parameters (`gt=0`, `le=365`) | Status is `FAILED_VALIDATION`; clean error dictionary returned without raising uncaught exceptions. |
| **COP-T02** | `test_prompt_injection_safety_guardrails` | Injection phrases ("Ignore previous instructions", "DROP TABLE", "bash -c") | Refused by `evaluate_prompt_safety()`; `is_safe=False` with descriptive refusal explanation. |
| **COP-T03** | `test_autonomous_money_transfer_refusal` | Instruction to transfer funds to university account | Refused with advisory guardrail notice; `is_transfer=True`. |
| **COP-T04** | `test_api_assistant_chat_tuition_affordability` | Chat: "Can I afford my tuition payment next month?" | Assistant executes `get_student_overview` and `calculate_funding_gap`; returns £9,250 tuition and explains shortfall. |
| **COP-T05** | `test_api_assistant_chat_remaining_money` | Chat: "How much money will remain after rent and tuition?" | Assistant executes `calculate_forecast`; explains living burn and post-tuition liquidity. |
| **COP-T06** | `test_api_assistant_chat_transfer_options` | Chat: "Which transfer option gives my family the highest recipient amount?" | Assistant executes `compare_transfers`; recommends Wise / Digital Specialist and calculates fee savings. |
| **COP-T07** | `test_api_assistant_chat_delayed_scholarship_simulation` | Chat: "What happens if my expected scholarship arrives two weeks late?" | Assistant executes `simulate_delayed_income`; returns `requires_confirmation: True` and preview. |
| **COP-T08** | `test_api_assistant_chat_injection_refusal` | API call with malicious jailbreak text | Returns HTTP 200 with polite refusal message; zero backend tools executed. |

---

### Suite C: Signature China–Bangladesh Demo End-to-End Journey (`backend/tests/test_demo_scenario_china_bd_e2e.py`)
| Test ID | Test Name | Target / Method | Expected Outcome |
| :--- | :--- | :--- | :--- |
| **E2E-T01** | `test_signature_china_bd_demo_full_workflow_e2e` | Complete 10-step student journey: Overview -> Forecast -> Tuition Affordability -> Transfer Comparison -> Recommendation -> Simulation Confirmation | All 10 steps execute sequentially without error; amounts match deterministic engine (¥24,000 tuition, 1,000 CNY -> BDT comparison); "No money was moved" asserted. |
| **E2E-T02** | `test_mathematical_consistency_china_bd_dataset` | Direct position check on CNY and BDT balances | CNY liquid: ¥8,500.00; Stipend: ¥3,500.00; Inflows total: ¥12,000.00. BDT liquid: ৳350,000.00. Math exact to 2 decimal places. |
| **E2E-T03** | `test_reverse_transfer_bdt_to_cny` | Reverse family remittance transfer BDT -> CNY | Verifies reciprocal exchange rate, fee deduction, and net proceeds delivered in CNY. |
| **E2E-T04** | `test_default_currencies_and_absence_of_gbp_inr` | Active demo validation | Confirms CNY and BDT are default currencies, and GBP/INR are absent from active demo responses. |

---

### Suite D: Domain Financial Engine (`backend/tests/test_domain_*.py`, `test_financial_calc.py`)
| Test ID | Test Name | Target / Method | Expected Outcome |
| :--- | :--- | :--- | :--- |
| **DOM-T01** | `test_currencies_are_never_silently_combined` | Multi-currency gap analysis | CNY and BDT balances are segregated in `currency_positions`; never summed into a raw float. |
| **DOM-T02** | `test_funding_gap_detected_with_tuition` | Funding gap with tuition obligation | Evaluates obligations vs available resources; flags `target_currency_has_shortfall=True`. |
| **DOM-T03** | `test_zero_balances_edge_case` | Scenario with 0 starting balance | Handles zero balances without divide-by-zero errors; reports critical deficit. |
| **DOM-T04** | `test_tuition_deadline_timing` | Tuition deadline within vs beyond horizon | Obligations correctly partitioned into 30-day and 90-day windows. |
| **DOM-T05** | `test_missing_data_completeness_scoring` | Partial scenario data | Audits missing inputs (e.g. missing living expenses); scores data completeness accurately. |
| **DOM-T06** | `test_stale_quote_flagging_in_funding_gap` | FX quote older than 24 hours | Quotes flagged with `is_stale=True` and clear staleness advisory text. |
| **DOM-T07** | `test_fresh_rate_has_no_warning` | FX quote within 24 hours | `is_stale=False`; no warning generated. |
| **DOM-T08** | `test_money_arithmetic_precision` | Decimal precision test | Verifies half-up rounding to 2 decimal places across transactions. |
| **DOM-T09** | `test_transfer_fee_comparison_decomposition` | Transfer comparison engine | Verifies total fee cost decomposes into upfront wire fee + FX margin markup. |
| **DOM-T10** | `test_digital_specialist_cheaper_than_traditional_bank` | Fee comparison across providers | Digital specialist total fee is strictly less than traditional bank wire fee. |

---

### Suite E: API Endpoints & Health (`backend/tests/test_api_endpoints.py`, `test_health.py`)
| Test ID | Test Name | Target / Method | Expected Outcome |
| :--- | :--- | :--- | :--- |
| **API-T01** | `test_api_health_endpoint` | `GET /api/health` | Returns 200 OK, `status: healthy`, database connection verified. |
| **API-T02** | `test_demo_scenario_endpoint` | `GET /api/v1/demo/scenario` | Returns Tanvir Hasan, study currency CNY, home currency BDT. |
| **API-T03** | `test_finance_overview_endpoint` | `GET /api/v1/finance/overview` | Returns separated currency balances, tuition amount ¥24,000.00, and runway. |
| **API-T04** | `test_finance_forecast_endpoint` | `POST /api/v1/finance/forecast` | Returns 90-day cash flow projection, daily summaries, and timeline events. |
| **API-T05** | `test_transfers_compare_endpoint` | `POST /api/v1/transfers/compare` | Returns quotes with explicit timestamps and provenance labels for 1,000 CNY -> BDT. |
| **API-T06** | `test_recommendations_endpoint` | `GET /api/v1/recommendations` | Returns prioritized actionable recommendations with uncertainty and assumptions. |

---

## 3. Frontend Quality Assurance Strategy

1. **Type Safety & Static Analysis**:
   - `npx tsc -b`: Compiles TypeScript without errors.
   - `npx oxlint`: Fast JavaScript/TypeScript linter with React purity and hooks rules.
2. **Production Bundle Verification**:
   - `npm run build`: Bundles assets using Vite and minifies output; ensures no missing imports.
3. **Resilience to Backend Outages**:
   - Every fetch in `api.ts` handles network errors and non-200 responses gracefully.
   - The UI includes an offline fallback calculation mode if the backend is unreachable.

---

## 4. Execution & Automated Pipeline
- All 47 backend tests run automatically in CI on every push via `.github/workflows/ci.yml`.
- Standalone seed routine runs in CI to verify synthetic math consistency.
