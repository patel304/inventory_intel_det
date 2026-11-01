# AI PROMPT HISTORY
## Inventory Shrinkage Detection System – YottaFlex AI

**Project:** Inventory Shrinkage Detection API
**Candidate:** Dileep Patel
**AI Tool:** ChatGPT
**Development Period:** October 30 – November 1, 2026

---

### 1. Project Requirements and Business Understanding

**Original requirement:**

Build an Inventory Shrinkage Detection System to detect unusual inventory loss by comparing receipts, sales, transfers, adjustments, returns and physical inventory counts.

The system should identify discrepancies between expected inventory and actual counted inventory.

### 2. Database and Synthetic Data Generation

Develop a realistic synthetic inventory dataset with the following requirements:

- 100 stores
- 5,000 SKUs
- 1,000,000 inventory movements
- 20,000 cycle counts
- Fixed random seed: 20261022
- Deterministic IDs and reproducible data generation
- Ground-truth labels for shrinkage cases
- Include relevant edge cases
- Support CSV, JSON and SQL exports
- Provide schema, data dictionary and generator documentation

Required business entities included Store, SKU, InventoryMovement, CycleCount, EmployeeRole, Shift, Promotion, Return, ShrinkageAlert and Investigation.

### 3. Technology Stack and Backend

Implement the backend using FastAPI and Python with MySQL as the database.

Requirements included:

- Database models and relationships
- SQLAlchemy integration
- Database migrations using Alembic
- Inventory movement processing
- Expected stock calculation
- Inventory variance calculation
- API endpoints for inventory lookup and shrinkage detection
- Investigation and alert management

### 4. Shrinkage Detection and Machine Learning

Implement two approaches for identifying unusual inventory loss:

**Rule-Based Detection**
- Compare expected stock with physical cycle counts.
- Identify inventory discrepancies.
- Apply business rules to identify suspicious shrinkage.

**Machine Learning**
- Use Isolation Forest for anomaly detection.
- Evaluate the model against labelled test data.
- Compare precision, recall and F1-score.
- Explain the model's performance and limitations.

### 5. Frontend and Dashboard

Develop a React-based frontend with a professional dashboard.

Required functionality:

- Dashboard and analytics
- Store management and SKU catalog
- Inventory position lookup
- Shrinkage alerts
- Search and filtering
- Investigation management
- Model performance information
- System health information

### 6. Frontend and Backend Debugging

Debug the existing implementation without unnecessarily rewriting the project.

Specific issues addressed during development:

- Shrinkage Alerts search input losing focus after typing.
- Investigation modal remaining open after successful save.
- Inventory Lookup not returning results using Store ID and SKU ID.

Preserve existing database records and working functionality.

### 7. Project Completion and GitHub

Complete the project within the 72-hour recruitment assignment window.

Requirements:
- Finish the existing implementation.
- Fix necessary bugs.
- Verify frontend and backend functionality.
- Maintain a professional GitHub repository.
- Prepare project documentation and setup instructions.
- Avoid unnecessary features and oversized implementation changes.

---

## AI Usage Disclosure

ChatGPT was used for project planning, technical guidance, implementation assistance, debugging, code review and project verification.

The candidate is responsible for understanding the architecture, business logic, implementation decisions, testing results and limitations of the submitted project.

## Record Note

This document is a consolidated record of project-related requests recovered from available ChatGPT conversation history. It is not a verbatim export of every individual message or a complete export of prompts submitted to other AI tools.