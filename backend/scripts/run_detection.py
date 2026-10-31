
from app.database import SessionLocal
from app.services.detection_engine import run_detection


def main():
    db = SessionLocal()

    try:
        results = run_detection(db)

        print("\nSHRINKAGE DETECTION RESULTS")
        print("=" * 40)

        print("Records evaluated:", results["records_evaluated"])
        print("Actual shrinkage cases:", results["actual_shrinkage_cases"])

        print("\nRULE-BASED MODEL")
        print(results["rule_based"])

        print("\nISOLATION FOREST")
        print(results["isolation_forest"])

        print("\nDATABASE ALERT SUMMARY")
        print(results["alert_summary"])

        print("\nGENERATED FILES")
        print(results["results_file"])
        print(results["metrics_file"])

    finally:
        db.close()


if __name__ == "__main__":
    main()
