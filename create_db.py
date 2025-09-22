"""
Simple script to create the database tables for the app using SQLModel.
Run this in the project root with the same Python environment used to run the app.
"""
from sqlmodel import SQLModel, create_engine

# Import the Student model from the app so the metadata includes it
from resultdashboard_reflex.resultdashboard_reflex import Student

DB_URL = "sqlite:///resultdashboard.db"

if __name__ == "__main__":
    engine = create_engine(DB_URL, echo=True)
    # Ensure the Student model is imported so its table is registered on metadata
    assert hasattr(Student, "__table__"), "Student model table not available"
    SQLModel.metadata.create_all(engine)
    print(f"Created tables in {DB_URL}")
