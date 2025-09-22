"""
Simple script to create the database tables for the app using SQLModel.
Run this in the project root with the same Python environment used to run the app.
"""
import sys
from pathlib import Path

try:
    from sqlmodel import SQLModel, create_engine
except Exception:
    print("Missing dependency: sqlmodel is required to run this script. Install with 'pip install sqlmodel'.")
    raise

# Attempt to import the Student model from the app. If this script is run
# from a different working directory, add the project root to sys.path.
try:
    from resultdashboard_reflex.resultdashboard_reflex import Student
except Exception:
    # Add project root (parent of this file) to sys.path and retry.
    project_root = Path(__file__).resolve().parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    try:
        from resultdashboard_reflex.resultdashboard_reflex import Student
    except Exception:
        print("Failed to import the Student model from the app. Make sure you're running this script from the project root and that the package is accessible.")
        raise

DB_URL = "sqlite:///resultdashboard.db"

def main() -> None:
    engine = create_engine(DB_URL, echo=True)
    # Ensure the Student model is imported so its table is registered on metadata
    if not hasattr(Student, "__table__"):
        raise RuntimeError("Student model table not available on import")
    SQLModel.metadata.create_all(engine)
    print(f"Created tables in {DB_URL}")


if __name__ == "__main__":
    main()
