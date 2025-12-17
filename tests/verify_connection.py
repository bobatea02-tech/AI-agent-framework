import sys
import os
from sqlalchemy import text

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from database.connection import get_db, get_db_context, engine
from database.models import WorkflowDefinition, Base 

def verify_connection():
    print("Verifying database connection...")
    
    # 1. Test get_db() generator
    print("Testing get_db() generator...")
    db_gen = get_db()
    db = next(db_gen)
    try:
        result = db.execute(text("SELECT 1"))
        val = result.scalar()
        print(f"  Query result: {val}")
        assert val == 1
    finally:
        # Simulate FastAPI dependency cleanup
        try:
            next(db_gen)
        except StopIteration:
            pass

    # 2. Test get_db_context() context manager
    print("Testing get_db_context() context manager...")
    
    # First create tables to have something to insert
    # Using the models we defined earlier to ensure integration
    Base.metadata.create_all(bind=engine)
    
    try:
        with get_db_context() as session:
            # Try to insert a simple record to test commit
            # We'll use a raw query or a model if available. 
            # Since we imported WorkflowDefinition, let's try that but keep it simple.
            # Actually raw SQL is safer to verify connection mechanics without unrelated model errors.
            session.execute(text("CREATE TABLE IF NOT EXISTS test_table (id INTEGER PRIMARY KEY, name TEXT)"))
            session.execute(text("INSERT INTO test_table (name) VALUES ('test_item')"))
            # Commit happens automatically on exit
            
        # Verify it was committed
        with get_db_context() as session:
            result = session.execute(text("SELECT name FROM test_table WHERE name='test_item'"))
            row = result.fetchone()
            print(f"  Inserted row: {row[0]}")
            assert row[0] == 'test_item'
            
            # Clean up
            session.execute(text("DROP TABLE test_table"))
            
    except Exception as e:
        print(f"  Context manager failed: {e}")
        raise

    print("Database connection verification passed!")

if __name__ == "__main__":
    verify_connection()
