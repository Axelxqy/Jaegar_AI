import sqlite3
from contextlib import closing
from pathlib import Path

#Resolve Backend Dir 
BACKEND_DIR = Path(__file__).resolve().parents[1]
DATABASE_DIR = BACKEND_DIR / "database"
DB_PATH = DATABASE_DIR / "jaegar_memory.db"

def _validate_text(value: str, field_name: str) -> str:
    """Validate and Normalize empty strings"""
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string.")

    value = value.strip()

    if not value:
        raise ValueError(f"{field_name} must not be empty.")

    return value

def _validate_id(value: int, field_name: str) -> int:
    """Validate a positive database ID."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer.")

    if value <= 0:
        raise ValueError(f"{field_name} must be positive.")

    return value


def _validate_scope(scope: str, scope_id: str) -> tuple[str, str]:
    """Validate memory ownership scope and its identifier."""
    allowed_scopes = {
        "global",
        "project",
        "personal",
        "conversation",
    }

    scope = _validate_text(scope, "Scope")
    scope_id = _validate_text(scope_id, "Scope ID")

    if scope not in allowed_scopes:
        raise ValueError(f"Unsupported memory scope: {scope}")

    if scope == "global":
        if scope_id != "global":
            raise ValueError(
                "Global memory must use scope_id='global'."
            )
    elif scope_id == "global":
        raise ValueError(
            "Non-global memory cannot use scope_id='global'."
        )

    return scope, scope_id


def _validate_retention(retention: str) -> str:
    """Validate memory retention classification."""
    retention = _validate_text(retention, "Retention")

    if retention not in {"STM", "LTM"}:
        raise ValueError(
            "Retention must be either 'STM' or 'LTM'."
        )

    return retention


def _validate_optional_text(
    value: str | None,
    field_name: str,
) -> str | None:
    """Validate optional text without accepting empty strings."""
    if value is None:
        return None

    return _validate_text(value, field_name)

def _connect() -> sqlite3.Connection:
    """Connect to the SQLite database with foreign key enforcement."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_database():
    """
    Initialize the legacy memory table and structured memory schema.

    This migration is additive:
    - Existing memories are preserved.
    - Existing table structure is not changed.
    - New tables and indexes are created if absent.
    """
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)

    with closing(_connect()) as conn:
        conn.executescript("""
            BEGIN IMMEDIATE;

            -- Legacy Compatibility
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL 
                    DEFAULT CURRENT_TIMESTAMP
            );     

            -- Stable identity of a memory
            CREATE TABLE IF NOT EXISTS memory_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                
                status TEXT NOT NULL DEFAULT 'active'
                    CHECK (
                        status IN (
                            'active',
                            'superseded',
                            'archived',
                            'expired'
                        )
                    ),
                
                created_at TEXT NOT NULL
                    DEFAULT CURRENT_TIMESTAMP,
                    
                updated_at TEXT NOT NULL
                    DEFAULT CURRENT_TIMESTAMP
            );

            -- Immutable content snapshots
            CREATE TABLE IF NOT EXISTS memory_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                
                memory_id INTEGER NOT NULL,
                
                version_number INTEGER NOT NULL
                    CHECK (version_number > 0),
                
                content TEXT NOT NULL
                    CHECK (LENGTH(trim(content)) > 0),   

                change_reason TEXT,

                created_at TEXT NOT NULL
                    DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (memory_id) 
                    REFERENCES memory_records(id)
                    ON DELETE RESTRICT,

                UNIQUE (memory_id, version_number)
            );

            -- Memory versions are append-only.
            CREATE TRIGGER IF NOT EXISTS
                prevent_memory_version_update
            BEFORE UPDATE ON memory_versions
            BEGIN
                SELECT RAISE(ABORT, 'Memory versions are immutable.');
            END;

            CREATE TRIGGER IF NOT EXISTS
                prevent_memory_version_delete
            BEFORE DELETE ON memory_versions
            BEGIN
                SELECT RAISE(ABORT, 'Memory versions cannot be deleted.');
            END;

            -- Where a memory belongs and its retention level.
            -- Historical placements remain available when superseded or revoked.
            CREATE TABLE IF NOT EXISTS memory_placements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                memory_id INTEGER NOT NULL,

                scope TEXT NOT NULL
                    CHECK (
                        scope IN (
                            'global',
                            'project',
                            'personal',
                            'conversation'
                        )
                    ),
                
                scope_id TEXT NOT NULL,

                retention TEXT NOT NULL
                    CHECK (retention IN ('STM', 'LTM')),

                status TEXT NOT NULL DEFAULT 'active'
                    CHECK (
                        status IN (
                            'active',
                            'superseded',
                            'revoked'
                        )
                    ),

                created_at TEXT NOT NULL
                    DEFAULT CURRENT_TIMESTAMP,
                
                updated_at TEXT NOT NULL
                    DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (memory_id)
                    REFERENCES memory_records(id)
                    ON DELETE RESTRICT,

                CHECK (
                    (
                        scope = 'global'
                        AND scope_id = 'global'
                    )
                    OR
                    (
                        scope <> 'global'
                        AND length(trim(scope_id)) > 0
                        AND scope_id <> 'global'
                    )
                )
            );

            -- A memory can only have one active placement within the same scope and identifier.
            CREATE UNIQUE INDEX IF NOT EXISTS
                idx_memory_placements_active_unique
            ON memory_placements (
                memory_id,
                scope,
                scope_id
            )
            WHERE status = 'active';

            CREATE INDEX IF NOT EXISTS
                idx_memory_placements_scope
            ON memory_placements (
                scope,
                scope_id,
                retention,
                status
            );

            -- Explicit relationships between memory records.
            -- These link records without copying their content.
            CREATE TABLE IF NOT EXISTS memory_relationships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_memory_id INTEGER NOT NULL,
                target_memory_id INTEGER NOT NULL,

                relationship_type TEXT NOT NULL
                    CHECK (
                        relationship_type IN (
                            'derived_from',
                            'supports',
                            'contradicts',
                            'supersedes',
                            'related_to',
                            'duplicate_of'
                        )
                    ),

                created_at TEXT NOT NULL
                    DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (source_memory_id)
                    REFERENCES memory_records(id)
                    ON DELETE RESTRICT,
                
                FOREIGN KEY (target_memory_id)
                    REFERENCES memory_records(id)
                    ON DELETE RESTRICT,

                CHECK (source_memory_id <> target_memory_id),

                UNIQUE (
                    source_memory_id,
                    target_memory_id,
                    relationship_type
                )
            );

            -- Approval requests seperate from memory records.
            -- Approval of one action does not authorise future actions.
            CREATE TABLE IF NOT EXISTS memory_approvals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                memory_id INTEGER NOT NULL,

                placement_id INTEGER,

                action_type TEXT NOT NULL
                    CHECK (
                        action_type IN (
                            'promote_retention',
                            'promote_scope',
                            'modify_content',
                            'revoke_placement'
                        )
                    ),

                status TEXT NOT NULL DEFAULT 'pending'
                    CHECK (
                        status IN (
                            'pending',
                            'approved',
                            'rejected',
                            'cancelled'
                        )
                    ),

                requested_action TEXT NOT NULL
                    CHECK (LENGTH(trim(requested_action)) > 0),

                requested_at TEXT NOT NULL
                    DEFAULT CURRENT_TIMESTAMP,

                decided_at TEXT,

                decision_reason TEXT,

                FOREIGN KEY (memory_id)
                    REFERENCES memory_records(id)
                    ON DELETE RESTRICT,

                FOREIGN KEY (memory_id, placement_id)
                    REFERENCES memory_placements(memory_id, id)
                    ON DELETE RESTRICT
                );

            CREATE INDEX IF NOT EXISTS
                idx_memory_approvals_status
            ON memory_approvals (status, requested_at);

            -- Provenance of supporting source information.
            CREATE TABLE IF NOT EXISTS memory_sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                memory_id INTEGER NOT NULL,

                source_type TEXT NOT NULL
                    CHECK (length(trim(source_type)) > 0),

                source_ref TEXT,

                description TEXT,

                captured_at TEXT NOT NULL
                    DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (memory_id)
                    REFERENCES memory_records(id)
                    ON DELETE RESTRICT
            );

            CREATE INDEX IF NOT EXISTS
                idx_memory_sources_memory
            ON memory_sources (memory_id);

            COMMIT;            
        """)

def save_memory(category: str, content: str) -> int:
    """Save memory and return database ID."""
    category = _validate_text(category, "Category")
    content = _validate_text(content, "Content")

    with closing(_connect()) as conn:
        with conn:
            cursor = conn.execute(
                """
                INSERT INTO memories (category, content)
                VALUES (?, ?)
                """,
                (category, content),
            )

            return cursor.lastrowid

def get_memory(category: str | None = None) -> list[dict]:
    """Retrieve legacy memories, optionally filtered by category."""
    if category is not None:
        category = _validate_text(category, "Category")

    with closing(_connect()) as conn:
        conn.row_factory = sqlite3.Row

        if category is None:
            rows = conn.execute("""
                SELECT id, category, content, created_at
                FROM memories
                ORDER BY id
            """).fetchall()

        else:
            rows = conn.execute(
                """
                SELECT id, category, content, created_at
                FROM memories
                WHERE category = ?
                ORDER BY id
                """,
                (category,),
            ).fetchall()

        return [dict(row) for row in rows]

def create_structured_memory(
    content: str,
    scope: str,
    scope_id: str,
    retention: str = "STM",
    change_reason: str | None = None,
) -> int:
    """
    Create a structured memory with its initial version and placement.

    All three database operations succeed together or are rolled back.
    Returns the new memory record ID.
    """
    content = _validate_text(content, "Content")
    scope, scope_id = _validate_scope(scope, scope_id)
    retention = _validate_retention(retention)
    change_reason = _validate_optional_text(
        change_reason,
        "Change reason",
    )

    with closing(_connect()) as conn:
        with conn:
            conn.execute("BEGIN IMMEDIATE")

            # 1. Create stable memory identity.
            cursor = conn.execute("""
                INSERT INTO memory_records DEFAULT VALUES
            """)

            memory_id = cursor.lastrowid

            # 2. Create initial content version.
            conn.execute(
                """
                INSERT INTO memory_versions (
                    memory_id,
                    version_number,
                    content,
                    change_reason
                )
                VALUES (?, 1, ?, ?)
                """,
                (memory_id, content, change_reason),
            )

            # 3. Assign initial ownership and retention.
            conn.execute(
                """
                INSERT INTO memory_placements (
                    memory_id,
                    scope,
                    scope_id,
                    retention
                )
                VALUES (?, ?, ?, ?)
                """,
                (memory_id, scope, scope_id, retention),
            )

            return memory_id

def add_memory_version(
    memory_id: int,
    content: str,
    change_reason: str | None = None,
) -> int:
    """
    Append a new memory version without modifying previous versions.

    Returns the new version number.
    """
    memory_id = _validate_id(memory_id, "Memory ID")
    content = _validate_text(content, "Content")
    change_reason = _validate_optional_text(
        change_reason,
        "Change reason",
    )

    with closing(_connect()) as conn:
        with conn:
            conn.execute("BEGIN IMMEDIATE")

            record = conn.execute(
                """
                SELECT status
                FROM memory_records
                WHERE id = ?
                """,
                (memory_id,),
            ).fetchone()

            if record is None:
                raise LookupError(
                    f"Memory record {memory_id} does not exist."
                )

            if record[0] != "active":
                raise ValueError(
                    "Cannot add a version to a non-active memory."
                )

            current_version = conn.execute(
                """
                SELECT COALESCE(MAX(version_number), 0)
                FROM memory_versions
                WHERE memory_id = ?
                """,
                (memory_id,),
            ).fetchone()[0]

            new_version = current_version + 1

            conn.execute(
                """
                INSERT INTO memory_versions (
                    memory_id,
                    version_number,
                    content,
                    change_reason
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    memory_id,
                    new_version,
                    content,
                    change_reason,
                ),
            )

            conn.execute(
                """
                UPDATE memory_records
                SET updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (memory_id,),
            )

            return new_version

def add_memory_placement(
    memory_id: int,
    scope: str,
    scope_id: str,
    retention: str,
) -> int:
    """
    Add a placement for an existing active memory.

    Returns the new placement ID.
    """
    memory_id = _validate_id(memory_id, "Memory ID")
    scope, scope_id = _validate_scope(scope, scope_id)
    retention = _validate_retention(retention)

    with closing(_connect()) as conn:
        with conn:
            conn.execute("BEGIN IMMEDIATE")

            record = conn.execute(
                """
                SELECT status
                FROM memory_records
                WHERE id = ?
                """,
                (memory_id,),
            ).fetchone()

            if record is None:
                raise LookupError(
                    f"Memory record {memory_id} does not exist."
                )

            if record[0] != "active":
                raise ValueError(
                    "Cannot place a non-active memory."
                )

            cursor = conn.execute(
                """
                INSERT INTO memory_placements (
                    memory_id,
                    scope,
                    scope_id,
                    retention
                )
                VALUES (?, ?, ?, ?)
                """,
                (memory_id, scope, scope_id, retention),
            )

            conn.execute(
                """
                UPDATE memory_records
                SET updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (memory_id,),
            )

            return cursor.lastrowid


def _get_structured_memory_from_connection(
    conn: sqlite3.Connection,
    memory_id: int,
    include_inactive_placements: bool = False,
) -> dict | None:
    """Retrieve one structured memory and its latest version."""
    conn.row_factory = sqlite3.Row

    record = conn.execute(
        """
        SELECT
            mr.id,
            mr.status,
            mr.created_at,
            mr.updated_at,
            mv.id AS version_id,
            mv.version_number,
            mv.content,
            mv.change_reason,
            mv.created_at AS version_created_at
        FROM memory_records AS mr
        LEFT JOIN memory_versions AS mv
            ON mv.id = (
                SELECT v.id
                FROM memory_versions AS v
                WHERE v.memory_id = mr.id
                ORDER BY v.version_number DESC
                LIMIT 1
            )
        WHERE mr.id = ?
        """,
        (memory_id,),
    ).fetchone()

    if record is None:
        return None

    placement_query = """
        SELECT
            id,
            scope,
            scope_id,
            retention,
            status,
            created_at,
            updated_at
        FROM memory_placements
        WHERE memory_id = ?
    """

    if not include_inactive_placements:
        placement_query += " AND status = 'active'"

    placement_query += " ORDER BY id"

    placements = conn.execute(
        placement_query,
        (memory_id,),
    ).fetchall()

    latest_version = None

    if record["version_id"] is not None:
        latest_version = {
            "id": record["version_id"],
            "version_number": record["version_number"],
            "content": record["content"],
            "change_reason": record["change_reason"],
            "created_at": record["version_created_at"],
        }

    return {
        "id": record["id"],
        "status": record["status"],
        "created_at": record["created_at"],
        "updated_at": record["updated_at"],
        "latest_version": latest_version,
        "placements": [dict(row) for row in placements],
    }


def get_structured_memory(
    memory_id: int,
    include_inactive_placements: bool = False,
) -> dict | None:
    """
    Retrieve one structured memory by ID.

    Returns None if the record does not exist.
    Historical placements are excluded by default.
    """
    memory_id = _validate_id(memory_id, "Memory ID")

    if not isinstance(include_inactive_placements, bool):
        raise TypeError(
            "include_inactive_placements must be a boolean."
        )

    with closing(_connect()) as conn:
        return _get_structured_memory_from_connection(
            conn,
            memory_id,
            include_inactive_placements,
        )


def get_memory_versions(memory_id: int) -> list[dict]:
    """Retrieve all immutable versions of a memory chronologically."""
    memory_id = _validate_id(memory_id, "Memory ID")

    with closing(_connect()) as conn:
        conn.row_factory = sqlite3.Row

        record = conn.execute(
            """
            SELECT id
            FROM memory_records
            WHERE id = ?
            """,
            (memory_id,),
        ).fetchone()

        if record is None:
            raise LookupError(
                f"Memory record {memory_id} does not exist."
            )

        rows = conn.execute(
            """
            SELECT
                id,
                memory_id,
                version_number,
                content,
                change_reason,
                created_at
            FROM memory_versions
            WHERE memory_id = ?
            ORDER BY version_number ASC
            """,
            (memory_id,),
        ).fetchall()

        return [dict(row) for row in rows]


def get_structured_memories(
    scope: str,
    scope_id: str,
    retention: str | None = None,
    limit: int | None = None,
) -> list[dict]:
    """
    Retrieve memories through a specific ownership placement.

    Only active placements are considered.
    Scope and scope_id are mandatory to avoid unrestricted
    cross-scope retrieval at this interface.
    """
    scope, scope_id = _validate_scope(scope, scope_id)

    if retention is not None:
        retention = _validate_retention(retention)

    if limit is not None:
        if isinstance(limit, bool) or not isinstance(limit, int):
            raise TypeError("Limit must be an integer.")

        if limit <= 0:
            raise ValueError("Limit must be positive.")

    query = """
        SELECT DISTINCT mr.id
        FROM memory_records AS mr
        INNER JOIN memory_placements AS mp
            ON mp.memory_id = mr.id
        WHERE mr.status = 'active'
          AND mp.status = 'active'
          AND mp.scope = ?
          AND mp.scope_id = ?
    """

    params = [scope, scope_id]

    if retention is not None:
        query += " AND mp.retention = ?"
        params.append(retention)

    query += " ORDER BY mr.id"

    if limit is not None:
        query += " LIMIT ?"
        params.append(limit)

    with closing(_connect()) as conn:
        memory_ids = conn.execute(
            query,
            params,
        ).fetchall()

        results = []

        for (memory_id,) in memory_ids:
            memory = _get_structured_memory_from_connection(
                conn,
                memory_id,
            )

            if memory is not None:
                # Return only the placement used for this retrieval.
                memory["placements"] = [
                    placement
                    for placement in memory["placements"]
                    if (
                        placement["scope"] == scope
                        and placement["scope_id"] == scope_id
                        and (
                            retention is None
                            or placement["retention"] == retention
                        )
                    )
                ]

                results.append(memory)

        return results


def get_memory_placements(
    memory_id: int,
    include_inactive: bool = True,
) -> list[dict]:
    """Retrieve the placement history of a memory."""
    memory_id = _validate_id(memory_id, "Memory ID")

    if not isinstance(include_inactive, bool):
        raise TypeError("include_inactive must be a boolean.")

    with closing(_connect()) as conn:
        conn.row_factory = sqlite3.Row

        record = conn.execute(
            "SELECT id FROM memory_records WHERE id = ?",
            (memory_id,),
        ).fetchone()

        if record is None:
            raise LookupError(
                f"Memory record {memory_id} does not exist."
            )

        query = """
            SELECT
                id,
                memory_id,
                scope,
                scope_id,
                retention,
                status,
                created_at,
                updated_at
            FROM memory_placements
            WHERE memory_id = ?
        """

        if not include_inactive:
            query += " AND status = 'active'"

        query += " ORDER BY id"

        rows = conn.execute(query, (memory_id,)).fetchall()

        return [dict(row) for row in rows]


def change_memory_retention(
    placement_id: int,
    new_retention: str,
) -> int:
    """
    Change retention by superseding the old placement
    and creating a new placement.

    The previous placement remains in the database.
    Returns the new placement ID.
    """
    placement_id = _validate_id(placement_id, "Placement ID")
    new_retention = _validate_retention(new_retention)

    with closing(_connect()) as conn:
        with conn:
            conn.execute("BEGIN IMMEDIATE")

            placement = conn.execute(
                """
                SELECT
                    memory_id,
                    scope,
                    scope_id,
                    retention,
                    status
                FROM memory_placements
                WHERE id = ?
                """,
                (placement_id,),
            ).fetchone()

            if placement is None:
                raise LookupError(
                    f"Placement {placement_id} does not exist."
                )

            memory_id, scope, scope_id, old_retention, status = placement

            if status != "active":
                raise ValueError(
                    "Cannot change retention of an inactive placement."
                )

            if old_retention == new_retention:
                raise ValueError(
                    "New retention is identical to current retention."
                )

            record = conn.execute(
                """
                SELECT status
                FROM memory_records
                WHERE id = ?
                """,
                (memory_id,),
            ).fetchone()

            if record is None or record[0] != "active":
                raise ValueError(
                    "Cannot change placement of a non-active memory."
                )

            # Preserve the previous placement as history.
            conn.execute(
                """
                UPDATE memory_placements
                SET status = 'superseded',
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (placement_id,),
            )

            # Create the replacement placement.
            cursor = conn.execute(
                """
                INSERT INTO memory_placements (
                    memory_id,
                    scope,
                    scope_id,
                    retention
                )
                VALUES (?, ?, ?, ?)
                """,
                (memory_id, scope, scope_id, new_retention),
            )

            conn.execute(
                """
                UPDATE memory_records
                SET updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (memory_id,),
            )

            return cursor.lastrowid


def revoke_memory_placement(placement_id: int) -> None:
    """
    Revoke an active placement without deleting its history.
    """
    placement_id = _validate_id(placement_id, "Placement ID")

    with closing(_connect()) as conn:
        with conn:
            conn.execute("BEGIN IMMEDIATE")

            placement = conn.execute(
                """
                SELECT memory_id, status
                FROM memory_placements
                WHERE id = ?
                """,
                (placement_id,),
            ).fetchone()

            if placement is None:
                raise LookupError(
                    f"Placement {placement_id} does not exist."
                )

            memory_id, status = placement

            if status != "active":
                raise ValueError(
                    "Only active placements can be revoked."
                )

            conn.execute(
                """
                UPDATE memory_placements
                SET status = 'revoked',
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (placement_id,),
            )

            conn.execute(
                """
                UPDATE memory_records
                SET updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (memory_id,),
            )


# --------------------------------------------------
# Memory Relationships
# --------------------------------------------------

VALID_RELATIONSHIP_TYPES = {
    "derived_from",
    "supports",
    "contradicts",
    "supersedes",
    "related_to",
    "duplicate_of",
}


def create_memory_relationship(
    source_memory_id: int,
    target_memory_id: int,
    relationship_type: str,
) -> int:
    """
    Create a directional relationship between two memories.

    source_memory_id:
        The memory making the relationship.

    target_memory_id:
        The memory being referenced.

    Relationships can reference existing historical
    memories, including inactive memory records.
    """

    source_memory_id = _validate_id(
        source_memory_id,
        "source_memory_id",
    )

    target_memory_id = _validate_id(
        target_memory_id,
        "target_memory_id",
    )

    relationship_type = _validate_text(
        relationship_type,
        "relationship_type",
    )

    if relationship_type not in VALID_RELATIONSHIP_TYPES:
        raise ValueError("Invalid relationship type.")

    if source_memory_id == target_memory_id:
        raise ValueError(
            "A memory cannot have a relationship with itself."
        )

    with closing(_connect()) as conn:
        conn.execute("BEGIN IMMEDIATE")

        try:
            for memory_id in (
                source_memory_id,
                target_memory_id,
            ):
                row = conn.execute(
                    """
                    SELECT id
                    FROM memory_records
                    WHERE id = ?
                    """,
                    (memory_id,),
                ).fetchone()

                if row is None:
                    raise LookupError(
                        f"Memory {memory_id} does not exist."
                    )

            cursor = conn.execute(
                """
                INSERT INTO memory_relationships (
                    source_memory_id,
                    target_memory_id,
                    relationship_type
                )
                VALUES (?, ?, ?)
                """,
                (
                    source_memory_id,
                    target_memory_id,
                    relationship_type,
                ),
            )

            relationship_id = cursor.lastrowid
            conn.commit()

            return relationship_id

        except sqlite3.IntegrityError as exc:
            conn.rollback()
            raise ValueError(
                "This relationship already exists or violates "
                "a database constraint."
            ) from exc

        except Exception:
            conn.rollback()
            raise


def get_memory_relationships(
    memory_id: int,
    direction: str = "both",
    relationship_type: str | None = None,
) -> list[dict]:
    """
    Retrieve relationships involving a memory.

    direction:
        outgoing = relationships where memory is the source.
        incoming = relationships where memory is the target.
        both = all relationships involving the memory.
    """

    memory_id = _validate_id(memory_id, "memory_id")

    if direction not in {"incoming", "outgoing", "both"}:
        raise ValueError(
            "Direction must be incoming, outgoing or both."
        )

    if relationship_type is not None:
        relationship_type = _validate_text(
            relationship_type,
            "relationship_type",
        )

        if relationship_type not in VALID_RELATIONSHIP_TYPES:
            raise ValueError("Invalid relationship type.")

    with closing(_connect()) as conn:
        conn.row_factory = sqlite3.Row

        exists = conn.execute(
            """
            SELECT id
            FROM memory_records
            WHERE id = ?
            """,
            (memory_id,),
        ).fetchone()

        if exists is None:
            raise LookupError(
                f"Memory {memory_id} does not exist."
            )

        if direction == "outgoing":
            condition = "source_memory_id = ?"
        elif direction == "incoming":
            condition = "target_memory_id = ?"
        else:
            condition = (
                "source_memory_id = ? OR target_memory_id = ?"
            )

        params = (
            [memory_id, memory_id]
            if direction == "both"
            else [memory_id]
        )

        query = f"""
            SELECT
                id,
                source_memory_id,
                target_memory_id,
                relationship_type,
                created_at
            FROM memory_relationships
            WHERE ({condition})
        """

        if relationship_type is not None:
            query += " AND relationship_type = ?"
            params.append(relationship_type)

        query += " ORDER BY id ASC"

        rows = conn.execute(query, params).fetchall()

        return [dict(row) for row in rows]


# --------------------------------------------------
# Memory Provenance
# --------------------------------------------------

def add_memory_source(
    memory_id: int,
    source_type: str,
    source_ref: str | None = None,
    description: str | None = None,
) -> int:
    """
    Record the origin of a memory.

    Source records are append-only through this interface.
    """

    memory_id = _validate_id(memory_id, "memory_id")

    source_type = _validate_text(
        source_type,
        "source_type",
    )

    source_ref = _validate_optional_text(
        source_ref,
        "source_ref",
    )

    description = _validate_optional_text(
        description,
        "description",
    )

    with closing(_connect()) as conn:
        conn.execute("BEGIN IMMEDIATE")

        try:
            exists = conn.execute(
                """
                SELECT id
                FROM memory_records
                WHERE id = ?
                """,
                (memory_id,),
            ).fetchone()

            if exists is None:
                raise LookupError(
                    f"Memory {memory_id} does not exist."
                )

            cursor = conn.execute(
                """
                INSERT INTO memory_sources (
                    memory_id,
                    source_type,
                    source_ref,
                    description
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    memory_id,
                    source_type,
                    source_ref,
                    description,
                ),
            )

            source_id = cursor.lastrowid
            conn.commit()

            return source_id

        except Exception:
            conn.rollback()
            raise


def get_memory_sources(memory_id: int) -> list[dict]:
    """
    Retrieve all provenance records belonging to a memory.
    """

    memory_id = _validate_id(memory_id, "memory_id")

    with closing(_connect()) as conn:
        conn.row_factory = sqlite3.Row

        exists = conn.execute(
            """
            SELECT id
            FROM memory_records
            WHERE id = ?
            """,
            (memory_id,),
        ).fetchone()

        if exists is None:
            raise LookupError(
                f"Memory {memory_id} does not exist."
            )

        rows = conn.execute(
            """
            SELECT
                id,
                memory_id,
                source_type,
                source_ref,
                description,
                captured_at
            FROM memory_sources
            WHERE memory_id = ?
            ORDER BY id ASC
            """,
            (memory_id,),
        ).fetchall()

        return [dict(row) for row in rows]

