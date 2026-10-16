# BorderWise AI — Execution Evidence Catalog

This directory contains verified execution logs, mathematical proofs, and technical review evidence for BorderWise AI.

---

## 1. Evidence Files Index

| Evidence File | Milestone / Focus | Key Verified Outcomes |
| :--- | :--- | :--- |
| [`task1_foundation.md`](./task1_foundation.md) | Project Foundation & Architecture | Monorepo structure, FastAPI + React setup, health check endpoints, environment configuration. |
| [`task2_core_finance.md`](./task2_core_finance.md) | Core Financial Domain Engine | Decimal precision, 90-day cash-flow simulation, multi-currency funding gap, transfer fee decomposition. |
| [`task3_frontend.md`](./task3_frontend.md) | React + TypeScript Dashboard | Premium fintech UI, Recharts integration, 4 main dashboard views, accessibility, zero runtime crashes. |
| [`task4_ai_copilot.md`](./task4_ai_copilot.md) | AI Financial Copilot | Tool dispatch engine, prompt injection guardrail, refusal of autonomous transfers, simulation previews. |
| [`task5_demo_validation.md`](./task5_demo_validation.md) | Signature UK Competition Demo | 10-step demo workflow, Priya Patel scenario (GBP/INR), mathematical consistency, reset-demo routine. |

---

## 2. Capturing Execution Evidence

When running tests or verifying a deployment, execute the following commands to generate repeatable evidence:

### A. Backend Test Execution Evidence
```bash
# In backend directory:
.\.venv\Scripts\pytest.exe -v --tb=short
```
*Expected: 47 passed tests with zero failures.*

### B. Mathematical Seed Routine Evidence
```bash
# In backend directory:
.\.venv\Scripts\python.exe scripts/seed_demo.py
```
*Expected: Exit code 0, table of verified liquid balances, obligations, and transfer quote fee decomposition.*

### C. Frontend Build & Static Analysis Evidence
```bash
# In frontend directory:
npx oxlint
npm run build
```
*Expected: 0 errors, 0 warnings from oxlint; Vite build completes and outputs production bundle in `dist/`.*

---

## 3. Evidence Artifact Standard

When recording new milestone evidence, ensure each artifact records:
1. **Timestamp & Commit Context**: System time and branch status.
2. **Deterministic Inputs**: Explicit seed data and currency symbols used.
3. **Quantitative Assertions**: Actual calculated values compared against expected values.
4. **Command Output Transcript**: Untruncated terminal output demonstrating success or failure.
5. **Human Review Items**: Clear distinction between automated passes and visual browser checks.
