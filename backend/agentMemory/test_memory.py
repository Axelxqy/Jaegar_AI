import tempfile
from pathlib import Path

from backend.agentMemory import persistMem

def main():
    # Peserve the original database paths
    original_database_dir = persistMem.DATABASE_DIR
    original_database_path = persistMem.DB_PATH

    try:
        # Create a temporary isolated database path for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            test_dir = Path(temp_dir)

            persistMem.DATABASE_DIR = test_dir
            persistMem.DB_PATH = test_dir / "test_memory.db"

            # Initialize the temp database
            persistMem.init_database()

            # Insert test memory
            memory_id = persistMem.save_memory(
                "test", 
                "This is a test memory."
            )

            # Verify that the memory was saved correctly
            memories = persistMem.get_memory()

            assert len(memories) == 1
            assert memories[0]["id"] == memory_id
            assert memories[0]["category"] == "test"
            assert memories[0]["content"] == (
                "This is a test memory."
            )

            print(f"Saved Memory ID: {memory_id}")
            print(f"Category: {memories[0]['category']}")
            print(f"Content: {memories[0]['content']}")
            print("Memory saved and verified successfully.")

    finally:
        # Restore the original database paths
        persistMem.DATABASE_DIR = original_database_dir
        persistMem.DB_PATH = original_database_path

if __name__ == "__main__":
    main()