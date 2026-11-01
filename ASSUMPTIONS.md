# Assumptions

- The current MySQL schema and existing records are the source of truth.
- The generated retail dataset and ground-truth file are retained as-is.
- Inventory shortage cost is estimated as the absolute negative variance multiplied by the SKU unit cost. This is an estimate, not a booked financial loss.
- The frontend reads database-backed aggregate endpoints for dashboard and analytics views.
- Model metrics are based on synthetic evaluation data unless explicitly replaced with independently validated real-world data.
