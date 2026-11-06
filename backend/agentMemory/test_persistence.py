
import sqlite3
import tempfile
from contextlib import closing
from pathlib import Path

from backend.agentMemory import persistMem


def main():
    original_database_dir = persistMem.DATABASE_DIR
    original_database_path = persistMem.DB_PATH

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            test_dir = Path(temp_dir)

            persistMem.DATABASE_DIR = test_dir
            persistMem.DB_PATH = test_dir / "test_persistence.db"

            persistMem.init_database()

            # Test 1: Create a structured memory.
            memory_id = persistMem.create_structured_memory(
                content="JAEGAR uses SQLite for memory persistence.",
                scope="project",
                scope_id="Jaegar_AI",
                retention="STM",
                change_reason="Initial creation",
            )

            assert memory_id > 0

            # Test 2: Verify initial version and placement.
            with closing(sqlite3.connect(persistMem.DB_PATH)) as conn:
                conn.execute("PRAGMA foreign_keys = ON")

                versions = conn.execute(
                    """
                    SELECT version_number, content
                    FROM memory_versions
                    WHERE memory_id = ?
                    """,
                    (memory_id,),
                ).fetchall()

                assert versions == [
                    (1, "JAEGAR uses SQLite for memory persistence.")
                ]

                placements = conn.execute(
                    """
                    SELECT scope, scope_id, retention, status
                    FROM memory_placements
                    WHERE memory_id = ?
                    """,
                    (memory_id,),
                ).fetchall()

                assert placements == [
                    ("project", "Jaegar_AI", "STM", "active")
                ]

            # Test 3: Append a new version.
            new_version = persistMem.add_memory_version(
                memory_id,
                "JAEGAR uses structured SQLite memory persistence.",
                "Clarified memory architecture",
            )

            assert new_version == 2

            # Test 4: Add another placement.
            placement_id = persistMem.add_memory_placement(
                memory_id,
                "conversation",
                "conversation_001",
                "STM",
            )

            assert placement_id > 0

            # Test 5: Reject duplicate active placement.
            try:
                persistMem.add_memory_placement(
                    memory_id,
                    "conversation",
                    "conversation_001",
                    "LTM",
                )
            except sqlite3.IntegrityError:
                pass
            else:
                raise AssertionError(
                    "Duplicate active placement was accepted."
                )

            # Test 6: Reject direct version modification.
            try:
                with closing(sqlite3.connect(
                    persistMem.DB_PATH
                )) as conn:
                    conn.execute(
                        """
                        UPDATE memory_versions
                        SET content = 'Modified historical content'
                        WHERE memory_id = ?
                          AND version_number = 1
                        """,
                        (memory_id,),
                    )
            except sqlite3.IntegrityError:
                pass
            else:
                raise AssertionError(
                    "Immutable memory version was modified."
                )

            # Test 7: Verify both versions remain intact.
            with closing(sqlite3.connect(
                persistMem.DB_PATH
            )) as conn:
                versions = conn.execute(
                    """
                    SELECT version_number, content
                    FROM memory_versions
                    WHERE memory_id = ?
                    ORDER BY version_number
                    """,
                    (memory_id,),
                ).fetchall()

                assert len(versions) == 2
                assert versions[0][0] == 1
                assert versions[1][0] == 2

            # Test 8: Reject invalid scope.
            try:
                persistMem.create_structured_memory(
                    "Invalid scope test",
                    "unknown_scope",
                    "test_001",
                )
            except ValueError:
                pass
            else:
                raise AssertionError(
                    "Invalid scope was accepted."
                )

            # Test 9: Verify failed creation left no record.
            with closing(sqlite3.connect(
                persistMem.DB_PATH
            )) as conn:
                record_count = conn.execute(
                    "SELECT COUNT(*) FROM memory_records"
                ).fetchone()[0]

                assert record_count == 1

            
            # Test 10: Retrieve structured memory.
            memory = persistMem.get_structured_memory(memory_id)

            assert memory is not None
            assert memory["id"] == memory_id
            assert memory["status"] == "active"
            assert memory["latest_version"]["version_number"] == 2
            assert memory["latest_version"]["content"] == (
                "JAEGAR uses structured SQLite memory persistence."
            )
            assert len(memory["placements"]) == 2

            # Test 11: Retrieve complete version history.
            history = persistMem.get_memory_versions(memory_id)

            assert len(history) == 2
            assert history[0]["version_number"] == 1
            assert history[1]["version_number"] == 2
            assert history[0]["content"] == (
                "JAEGAR uses SQLite for memory persistence."
            )

            # Test 12: Retrieve by project scope.
            project_memories = persistMem.get_structured_memories(
                scope="project",
                scope_id="Jaegar_AI",
            )

            assert len(project_memories) == 1
            assert project_memories[0]["id"] == memory_id

            # Test 13: Scope isolation.
            conversation_memories = (
                persistMem.get_structured_memories(
                    scope="conversation",
                    scope_id="another_conversation",
                )
            )

            assert conversation_memories == []

            # Test 14: Retention filtering.
            ltm_memories = persistMem.get_structured_memories(
                scope="project",
                scope_id="Jaegar_AI",
                retention="LTM",
            )

            assert ltm_memories == []

            # Test 15: Historical placements can be retrieved.
            all_placements = persistMem.get_structured_memory(
                memory_id,
                include_inactive_placements=True,
            )

            assert len(all_placements["placements"]) == 2

            # Test 16: Missing memory handling.
            assert persistMem.get_structured_memory(999999) is None

            try:
                persistMem.get_memory_versions(999999)
            except LookupError:
                pass
            else:
                raise AssertionError(
                    "Missing memory version history was accepted."
                )

            # Test 17: Reject unrestricted retrieval.
            try:
                persistMem.get_structured_memories(
                    scope="project",
                    scope_id="",
                )
            except ValueError:
                pass
            else:
                raise AssertionError(
                    "Invalid scope identifier was accepted."
                )

            
            # Test 18: Retrieve placement history.
            placement_history = persistMem.get_memory_placements(
                memory_id
            )
            assert len(placement_history) == 2

            # Test 19: Change retention.
            new_placement_id = persistMem.change_memory_retention(
                placement_history[0]["id"],
                "LTM",
            )
            assert new_placement_id > 0

            updated_placements = persistMem.get_memory_placements(
                memory_id
            )

            assert len(updated_placements) == 3
            assert updated_placements[0]["status"] == "superseded"
            assert updated_placements[0]["retention"] == "STM"

            assert updated_placements[2]["status"] == "active"
            assert updated_placements[2]["retention"] == "LTM"

            # Test 20: Revoke a placement.
            persistMem.revoke_memory_placement(placement_id)

            revoked_placements = persistMem.get_memory_placements(
                memory_id
            )

            revoked = next(
                p for p in revoked_placements
                if p["id"] == placement_id
            )

            assert revoked["status"] == "revoked"

            # Test 21: Revoked placement is excluded from active retrieval.
            active_placements = persistMem.get_memory_placements(
                memory_id,
                include_inactive=False,
            )

            assert all(
                p["status"] == "active"
                for p in active_placements
            )

            # Test 22: Reject repeated revocation.
            try:
                persistMem.revoke_memory_placement(placement_id)
            except ValueError:
                pass
            else:
                raise AssertionError(
                    "Repeated revocation was accepted."
                )


            # Test 23: Create a second memory for relationship tests.
            related_memory_id = persistMem.create_structured_memory(
                content="SQLite supports structured persistent storage.",
                scope="project",
                scope_id="Jaegar_AI",
            )

            # Test 24: Create a derived_from relationship.
            derived_relationship_id = (
                persistMem.create_memory_relationship(
                    related_memory_id,
                    memory_id,
                    "derived_from",
                )
            )

            assert derived_relationship_id > 0

            # Test 25: Create a supports relationship.
            supports_relationship_id = (
                persistMem.create_memory_relationship(
                    memory_id,
                    related_memory_id,
                    "supports",
                )
            )

            assert supports_relationship_id > 0

            # Test 26: Retrieve outgoing relationships.
            outgoing = persistMem.get_memory_relationships(
                memory_id,
                direction="outgoing",
            )

            assert len(outgoing) == 1
            assert outgoing[0]["relationship_type"] == "supports"

            # Test 27: Retrieve incoming relationships.
            incoming = persistMem.get_memory_relationships(
                memory_id,
                direction="incoming",
            )

            assert len(incoming) == 1
            assert incoming[0]["relationship_type"] == "derived_from"

            # Test 28: Retrieve relationships in both directions.
            both = persistMem.get_memory_relationships(
                memory_id,
                direction="both",
            )

            assert len(both) == 2

            # Test 29: Filter relationships by type.
            filtered = persistMem.get_memory_relationships(
                memory_id,
                direction="both",
                relationship_type="supports",
            )

            assert len(filtered) == 1
            assert filtered[0]["relationship_type"] == "supports"

            # Test 30: Reject duplicate relationships.
            try:
                persistMem.create_memory_relationship(
                    related_memory_id,
                    memory_id,
                    "derived_from",
                )
            except ValueError:
                pass
            else:
                raise AssertionError(
                    "Duplicate relationship was accepted."
                )

            # Test 31: Reject self-referential relationships.
            try:
                persistMem.create_memory_relationship(
                    memory_id,
                    memory_id,
                    "related_to",
                )
            except ValueError:
                pass
            else:
                raise AssertionError(
                    "Self-referential relationship was accepted."
                )

            # Test 32: Reject nonexistent memory references.
            try:
                persistMem.create_memory_relationship(
                    99999,
                    memory_id,
                    "supports",
                )
            except LookupError:
                pass
            else:
                raise AssertionError(
                    "Nonexistent memory reference was accepted."
                )

            # Test 33: Reject invalid relationship direction.
            try:
                persistMem.get_memory_relationships(
                    memory_id,
                    direction="invalid",
                )
            except ValueError:
                pass
            else:
                raise AssertionError(
                    "Invalid relationship direction was accepted."
                )

            # Test 34: Add a user-statement provenance source.
            source_id_1 = persistMem.add_memory_source(
                memory_id=memory_id,
                source_type="user_statement",
                source_ref="conversation:test",
                description="Information provided directly by the user.",
            )

            assert source_id_1 > 0

            # Test 35: Add a project-file provenance source.
            source_id_2 = persistMem.add_memory_source(
                memory_id=memory_id,
                source_type="project_file",
                source_ref="backend/agentMemory/persistMem.py",
                description="Information obtained from project source code.",
            )

            assert source_id_2 > source_id_1

            # Test 36: Retrieve all provenance records.
            sources = persistMem.get_memory_sources(memory_id)

            assert len(sources) == 2
            assert sources[0]["source_type"] == "user_statement"
            assert sources[1]["source_type"] == "project_file"

            # Test 37: Reject provenance for nonexistent memory.
            try:
                persistMem.add_memory_source(
                    memory_id=99999,
                    source_type="user_statement",
                )
            except LookupError:
                pass
            else:
                raise AssertionError(
                    "Provenance for nonexistent memory was accepted."
                )

            # Test 38: Reject retrieval for nonexistent memory.
            try:
                persistMem.get_memory_sources(99999)
            except LookupError:
                pass
            else:
                raise AssertionError(
                    "Provenance retrieval for nonexistent memory "
                    "was accepted."
                )


            print("All structured persistence tests passed.")

    finally:
        persistMem.DATABASE_DIR = original_database_dir
        persistMem.DB_PATH = original_database_path


if __name__ == "__main__":
    main()
