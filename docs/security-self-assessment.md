# BorderWise AI — Security Self-Assessment

> **Disclaimer**: This document is an engineering self-assessment conducted for the competition review. It does not constitute a formal third-party penetration test or commercial SOC2/ISO audit. All evaluations reflect the actual, verified state of the codebase.

---

## 1. Executive Summary & Security Boundary
BorderWise AI is a decision-support copilot and multi-currency cash-flow planning tool for international students. 
- **Security Boundary**: The application is strictly advisory. It does not integrate with live bank clearing houses (e.g. SWIFT, FedNow, Faster Payments), cannot execute financial transactions, and stores no payment credentials or unhashed PII.
- **Architectural Isolation**: Financial values, forecasts, and currency conversions are computed strictly by deterministic backend domain services using Python `Decimal` arithmetic. The LLM/AI provider operates in a read-only parameter inspection role with an explicit allowlist of tools.

---

## 2. Competition Security Review Checklist

| Check Item | Status | Verification Evidence |
| :--- | :--- | :--- |
| **No secrets committed to repository** | **PASS** | Automated grep confirmed zero API keys, tokens, or private credentials committed. `.env.example` contains dummy variable declarations only. Verified via `test_no_secrets_in_environment_or_endpoints`. |
| **Environment variables loaded safely** | **PASS** | Loaded via Pydantic `BaseSettings` (`SettingsConfigDict`) in `app/core/config.py`. Missing keys fallback safely; no application crash if optional LLM keys are omitted. |
| **`.env` excluded from Git** | **PASS** | Checked `.gitignore` line 2 (`.env`, `.env.local`, `*.env`). Confirmed by `git status --ignored` that `.env` is omitted from version control. |
| **Input validation & sensible request-size limits** | **PASS** | Every API schema inherits from Pydantic `BaseModel` with strict field constraints (`gt=0`, `le=365`, `max_length=2000`). `RequestSizeLimitMiddleware` in `app/main.py` rejects payloads exceeding 1MB (1,048,576 bytes) with HTTP 413. Verified via `test_payload_too_large_rejected_with_413`. |
| **CORS restricted to intended origins** | **PASS** | `CORSMiddleware` in `app/main.py` is configured with `ALLOWED_ORIGINS` from `Settings` (defaults to local Vite dev ports `http://localhost:5173` and `http://127.0.0.1:5173`). Verified via `test_cors_headers_restricted`. |
| **Error responses do not leak stack traces** | **PASS** | Global unhandled exception handler in `app/main.py` intercepts uncaught exceptions, logs tracebacks server-side, and returns a generic sanitized error message: `{"detail": "An internal server error occurred..."}`. |
| **No arbitrary code execution / unrestricted LLM tools** | **PASS** | Tool execution uses a static dictionary registry (`APPROVED_TOOLS` in `app/ai/tools.py`). Unapproved tools (e.g. `execute_shell_command`) are rejected with `FAILED_VALIDATION`. System prompt injection attempts are rejected by `evaluate_prompt_safety()`. Verified via `test_invalid_tool_calls_rejected` and `test_prompt_injection_safety_guardrails`. |
| **Clear separation: user input, model output & calculations** | **PASS** | User inputs are treated as untrusted strings. The orchestrator invokes deterministic domain engines (`forecast_service.py`, `funding_gap_service.py`, `transfer_service.py`). The LLM never performs mathematical calculations; all numbers in responses originate from tool output payloads. |
| **SQL queries use ORM parameters / safe binding** | **PASS** | Database access uses SQLAlchemy ORM (`SessionLocal`). The only SQL statement is a parameterized connectivity probe (`SELECT 1`). No raw SQL string interpolation or user input concatenation exists. |
| **Financial amounts use explicit currencies & safe arithmetic** | **PASS** | All monetary amounts use `Decimal` with half-up rounding (`round_money_standard` / `round_rate_standard`). No floats are used in financial domain operations. Every figure is paired with an ISO-4217 code (`SupportedCurrency`). Silent cross-currency additions are blocked. |
| **Missing and stale FX data handled conservatively** | **PASS** | `get_dated_fx_quote()` enforces provenance and staleness checks. Quotes older than 24 hours trigger `is_stale=True` and generate explicit audit caveats. Stale quotes are never presented as live market rates. |
| **Simulated actions cannot call payment services** | **PASS** | Consequential simulated actions require human-in-the-loop confirmation (`requires_confirmation: True`). No payment gateway, ACH, or wire API client exists in the repository. Commands requesting money transfers are rejected by safety guardrails. Verified via `test_autonomous_money_transfer_refusal`. |
| **Dependencies documented and reviewed** | **PASS** | Backend dependencies pinned in `requirements.txt` and `pyproject.toml`; frontend packages pinned in `package-lock.json`. No unpinned major dependencies. |
| **Data retention and deletion limitations documented** | **PASS** | Current prototype operates in-memory and with local SQLite. No persistent personal data storage is deployed; sessions are ephemeral. Data retention limitations are documented below in Section 4. |
| **Synthetic demo data contains no real PII** | **PASS** | Demo data uses fictional personas (*Priya Patel*, *Aarav Sharma*), fictitious accounts (Barclays, HDFC, Chase, SBI), and synthetic dates. No actual student or banking records are present. |

---

## 3. Threat Matrix & Risk Register

| Risk ID | Threat Category | Threat Description | Severity | Mitigation Implemented | Verification Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **SEC-01** | Prompt Injection | User attempts to override system instructions or dump backend secrets via chat input. | High | Regex and keyword heuristic filters in `app/ai/safety.py` reject system prompts, jailbreaks, and dump commands prior to tool execution. | **PASS** (`test_prompt_injection_safety_guardrails`) |
| **SEC-02** | Autonomous Execution | User instructs model to "wire $5,000 to university account". | Critical | Advisory guardrail intercepts financial movement commands, refuses execution, and marks the request as advisory-only with no payment hooks. | **PASS** (`test_autonomous_money_movement_guardrail`) |
| **SEC-03** | Denial of Service (DoS) | Attacker posts gigabyte payloads to exhaust backend memory. | High | `RequestSizeLimitMiddleware` rejects any payload where `Content-Length > 1MB` with HTTP 413. | **PASS** (`test_payload_too_large_rejected_with_413`) |
| **SEC-04** | Information Leakage | Unhandled runtime crash reveals internal stack traces, library versions, or file paths. | Medium | Global `@app.exception_handler(Exception)` returns a sanitized 500 error while logging tracebacks server-side. | **PASS** (Verified in code review & middleware architecture) |
| **SEC-05** | Unauthorized Cross-Origin Access | Malicious website executes requests on user's local instance. | Medium | Strict `CORSMiddleware` restricted to whitelist configured in `settings.ALLOWED_ORIGINS`. | **PASS** (`test_cors_headers_restricted`) |
| **SEC-06** | Financial Hallucination | LLM invents favorable exchange rates or wrong tuition arithmetic. | High | LLM output is grounded in backend tool executions. All numbers are pulled directly from deterministic calculators (`forecast_service`, `funding_gap_service`). | **PASS** (`test_api_assistant_chat_tuition_affordability`) |
| **SEC-07** | Currency Confusion | Combining multi-currency accounts silently gives false runway illusions. | High | Multi-currency positions are separated in `currency_positions`. Cross-currency coverage requires explicit dated FX quotes. | **PASS** (`test_currencies_are_never_silently_combined`) |

---

## 4. User Data Retention & Privacy Limitations
- **Current Prototype Scope**: The prototype uses local in-memory session states and SQLite databases. No telemetry, third-party analytics, or external trackers are loaded.
- **Data Retention**: All financial scenario modifications are ephemeral. Users can reset their state back to pristine synthetic data at any time via `POST /api/v1/demo/reset` or the UI **Reset Demo** button.
- **Production Roadmap Requirement**: When integrating with banking data providers (e.g., Plaid, Tink, Open Banking UK), production compliance will require:
  1. AES-256 encryption at rest for user account tokens.
  2. TLS 1.3 in transit.
  3. GDPR / CCPA right-to-be-forgotten deletion workflows (`DELETE /api/v1/user/account`).
  4. Regular secret rotation and audit logging.

---

## 5. Summary of Unresolved Risks & Release Blockers
1. **External LLM Integration**: When transitioning from deterministic demo mode to live commercial LLMs (OpenAI, Gemini), API rate limiting, egress encryption, and outbound cost monitoring must be configured.
2. **Authentication / Multi-Tenancy**: The competition prototype operates as a single-student demonstration instance. Multi-tenant user authentication (OAuth 2.0 / JWT) is required prior to production multi-user deployment.
3. **Live Bank Feeds**: Current quotes and rates are synthetic benchmarks. Live execution requires certified partnership with regulated payment service providers (PSPs).
