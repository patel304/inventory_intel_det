
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