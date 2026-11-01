# StockGuard Implementation Plan

This plan follows the audit in `docs/PROJECT_AUDIT.md`. Work proceeds autonomously except at safety checkpoints (schema changes, destructive SQL, file deletion, git commit/push).

## Constraints (unchanged)

- Do not drop/truncate/delete MySQL data.
- Do not regenerate movements or overwrite `ground_truth.csv`.
- Do not run generator `--reset` (not present; do not add a destructive reset).
- Do not change MySQL credentials or `.env`.
- Do not migrate schema without approval.
- Tests must use isolated SQLite fixtures.

## Phase 2 — Backend

1. Add `pydantic-settings` config, CORS from env, structured logging, session rollback.
2. Extract shared movement sign rules (`ADJUSTMENT_IN` / `ADJUSTMENT_OUT` included).
3. Expected stock supports optional `as_of` (`effective_at <= as_of`).
4. Routers with stable existing paths plus missing read APIs:
   - `/alerts/{id}`
   - paginated `/alerts`, `/investigations`, `/stores`, `/skus`, `/cycle-counts`
   - `/dashboard/summary`
   - `/analytics/summary`
   - `/metrics/model`
5. Alert create: duplicate open-alert guard; richer serialized fields (including `variance` alias).
6. Investigations: conflict on active duplicate; sync alert status; `assigned_to` on update; `id` on events.
7. Health DB endpoint returns HTTP 503 on failure without raw internals.

No Alembic revision in this pass.

## Phase 3 — Detection and data quality

1. Resolve data paths from the backend package root.
2. Historical balances via per-(store, sku) prefix sums (memory-efficient vs cartesian join).
3. Features: existing plus movement frequency; labels never used as features.
4. Isolation Forest: stratified 70/30 split; fit on train; metrics on test only; report accuracy.
5. Keep rule-based metrics on the full labelled set (no training) and document why they are tautological on synthetic data.
6. Read-only `scripts/validate_data.py` writing `docs/DATA_VALIDATION_REPORT.md`.

Do not re-run full detection against MySQL during this pass (would be long-running and would attempt alert inserts; duplicate skip exists but is unnecessary risk).

## Phase 4 — Frontend

1. Environment-driven API base URL.
2. Pages: Dashboard, Stores, Products, Inventory, Alerts, Investigations, Analytics, Model Performance, System Health.
3. Real API data, loading/error/empty states, search/filter, responsive sidebar.
4. Fix `variance_quantity` mapping.
5. Synthetic-data disclaimer on model metrics.

## Phase 5 — Security / quality

1. Populate `.env.example` with placeholders only.
2. Trim `requirements.txt` to actual runtime + test deps.
3. Validate enums and string lengths (respect `resolution` VARCHAR(100)).
4. Document auth as not implemented.

## Phase 6 — Tests

1. pytest + httpx + in-memory SQLite.
2. Inventory math, variance, alerts, duplicate prevention, investigations, events, API validation, detection hold-out on tiny fixtures.
3. Vitest component/API-service tests for loading/error/alert rendering.

## Phase 7 — Performance

1. COUNT aggregations for dashboard (no movement download).
2. Pagination defaults (page size cap 100).
3. Prefix-sum detection loader.
4. No new indexes without approval (recommend only in docs).

## Phase 8–9 — Docs and GitHub

Update architecture, API, data dictionary, testing, deployment, model evaluation, README, progress log. Suggest commits; do not commit or push.


============================== docs/architecture.md ==============================

# System Architecture

## Project
Retail Inventory Intelligence & Shrinkage Detection System

## Database
MySQL 8 with InnoDB storage engine.

## Core Entities
1. Store
2. SKU
3. InventoryMovement
4. CycleCount
5. EmployeeRole
6. Shift
7. Promotion
8. Return
9. ShrinkageAlert
10. Investigation

## Supporting Entities
- StoreSKUOpeningBalance
- PromotionSKU
- InvestigationEvent

## Architecture Principles
- Every entity has a deterministic primary key.
- All relationships use foreign keys.
- Many-to-many relationships use bridge tables.
- Inventory movements are append-only.
- Historical changes are preserved.
- Transfers are represented by paired movement records.
- Ground truth is kept separate from detection inputs.
- All timestamps are stored in UTC.

## Inventory Reconciliation
Expected Stock =
Opening Stock
+ Receipts
+ Returns
+ Transfers In
- Sales
- Transfers Out
- Damage
+/- Adjustments

Variance = Physical Stock - Expected Stock

## Data Generation
Fixed random seed: 20261022

Supported modes:
- Starter
- Full

## Evaluation
- Precision
- Recall
- F1-score
- False Positive Rate
- Reproducibility
- Data Integrity
