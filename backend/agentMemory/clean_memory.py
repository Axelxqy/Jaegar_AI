
import sqlite3

from backend.agentMemory.persistMem import DB_PATH


def main():
    confirmation = input(
        "Delete all memories in category 'test'? (y/N): "
    ).strip().lower()

    if confirmation != "y":
        print("Cleanup cancelled.")
        return

    with sqlite3.connect(DB_PATH) as connection:
        cursor = connection.execute(
            "DELETE FROM memories WHERE category = ?",
            ("test",)
        )

        print(f"Deleted {cursor.rowcount} test memories.")


if __name__ == "__main__":
    main()
