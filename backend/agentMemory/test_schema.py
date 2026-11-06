import sqlite3
import tempfile
from pathlib import Path
from contextlib import closing

from backend.agentMemory import persistMem


def main():
    original_database_dir = persistMem.DATABASE_DIR
    original_database_path = persistMem.DB_PATH

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            test_dir = Path(temp_dir)

            persistMem.DATABASE_DIR = test_dir
            persistMem.DB_PATH = test_dir / "test_schema.db"

            # Initialization should create all tables.
            persistMem.init_database()

            with closing(sqlite3.connect(persistMem.DB_PATH)) as conn:
                conn.execute("PRAGMA foreign_keys = ON")
                tables = {
                    row[0]
                    for row in conn.execute("""
                        SELECT name
                        FROM sqlite_master
                        WHERE type = 'table'
                    """)
                }

                expected_tables = {
                    "memories",
                    "memory_records",
                    "memory_versions",
                    "memory_placements",
                    "memory_relationships",
                    "memory_approvals",
                    "memory_sources",
                }

                assert expected_tables.issubset(tables)

                # Verify foreign keys are enabled.
                assert conn.execute(
                    "PRAGMA foreign_keys"
                ).fetchone()[0] == 1

                # Verify scope validation.
                record_id = conn.execute("""
                    INSERT INTO memory_records DEFAULT VALUES
                """).lastrowid

                conn.execute("""
                    INSERT INTO memory_versions (
                        memory_id,
                        version_number,
                        content
                    )
                    VALUES (?, 1, ?)
                """, (record_id, "Original memory"))

                conn.execute("""
                    INSERT INTO memory_placements (
                        memory_id,
                        scope,
                        scope_id,
                        retention
                    )
                    VALUES (?, 'conversation', 'conversation_1', 'STM')
                """, (record_id,))

                # Invalid global scope identifier must fail.
                try:
                    conn.execute("""
                        INSERT INTO memory_placements (
                            memory_id,
                            scope,
                            scope_id,
                            retention
                        )
                        VALUES (?, 'global', 'project_1', 'STM')
                    """, (record_id,))
                except sqlite3.IntegrityError:
                    pass
                else:
                    raise AssertionError(
                        "Invalid global scope identifier was accepted."
                    )

                # A second active placement in the same scope must fail.
                try:
                    conn.execute("""
                        INSERT INTO memory_placements (
                            memory_id,
                            scope,
                            scope_id,
                            retention
                        )
                        VALUES (?, 'conversation', 'conversation_1', 'LTM')
                    """, (record_id,))
                except sqlite3.IntegrityError:
                    pass
                else:
                    raise AssertionError(
                        "Duplicate active placement was accepted."
                    )

                # Verify that an invalid memory reference is rejected.
                try:
                    conn.execute("""
                        INSERT INTO memory_versions (
                            memory_id,
                            version_number,
                            content
                        )
                        VALUES (999999, 1, 'Invalid memory')
                    """)
                except sqlite3.IntegrityError:
                    pass
                else:
                    raise AssertionError(
                        "Invalid foreign key was accepted."
                    )

            # Initialization must be safe to repeat.
            persistMem.init_database()

            print("All structured memory schema tests passed.")

    finally:
        persistMem.DATABASE_DIR = original_database_dir
        persistMem.DB_PATH = original_database_path


if __name__ == "__main__":
    main()