# System Architecture

## Project

Retail Inventory Intelligence & Shrinkage Detection System (StockGuard)

## Technology and Database

- Frontend: React, Vite and Tailwind CSS
- Backend: Python and FastAPI
- ORM: SQLAlchemy
- Database: MySQL with InnoDB storage engine
- Migrations: Alembic
- Machine Learning: scikit-learn Isolation Forest

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

- PromotionSKU
- InvestigationEvent

The entity list should match the actual SQLAlchemy models and database migrations.

## Architecture Principles

- Entities use primary keys to identify records.
- Relationships are defined using foreign keys where applicable.
- Many-to-many relationships use association tables.
- Inventory changes are represented through movement records.
- Historical inventory changes are retained in movement records.
- Transfers are represented through paired transfer-out and transfer-in records.
- Ground-truth labels are maintained separately from detection input features.
- Timestamp handling should follow a consistent timezone convention.

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

Note: Returns and adjustment scenarios require further validation with populated movement data.

## Data Generation

Fixed random seed: `20261022`

Supported modes:
- Starter
- Full

The generated dataset contains:
- 100 Stores
- 5,000 SKUs
- 1,000,000 Inventory Movements
- 20,000 Cycle Counts

Existing generated data should be preserved during normal application execution.

## Evaluation

Model evaluation metrics:

- Precision
- Recall
- F1-score
- False Positive Rate
- Reproducibility
- Data Integrity

Evaluation results are based on synthetic data. Independent hold-out validation is required before making real-world model performance claims.

## Application Flow

React Frontend
↓
FastAPI Backend
↓
Application Services
↓
SQLAlchemy ORM
↓
MySQL Database

The backend provides inventory calculation, variance analysis, shrinkage detection, alert management and investigation workflows.