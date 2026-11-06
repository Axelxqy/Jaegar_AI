from unittest.mock import patch

from backend.agentMemory.contextBuilder import (
    MEMORY_CONTEXT_HEADER,
    build_memory_context,
)


def make_memory(
    memory_id: int,
    category: str,
    content: str,
) -> dict:
    return {
        "id": memory_id,
        "category": category,
        "content": content,
        "created_at": "2026-11-02 12:00:00",
    }


def main():
    memories = [
        make_memory(
            1,
            "preference",
            "Prefers concise technical explanations.",
        ),
        make_memory(
            2,
            "test",
            "Temporary test record.",
        ),
        make_memory(
            3,
            "project",
            "Building Jaegar AI.",
        ),
    ]

    with patch(
        "backend.agentMemory.contextBuilder.get_memory",
        return_value=memories,
    ):
        # Test filtering and newest-first ordering.
        context = build_memory_context()

        assert "Temporary test record." not in context
        assert "Prefers concise technical explanations." in context
        assert "Building Jaegar AI." in context

        assert context.index(
            "Building Jaegar AI."
        ) < context.index(
            "Prefers concise technical explanations."
        )

        # Test the complete output limit.
        limit = len(MEMORY_CONTEXT_HEADER) + 80
        bounded_context = build_memory_context(max_chars=limit)

        assert len(bounded_context) <= limit

        # Test an empty memory collection.
        with patch(
            "backend.agentMemory.contextBuilder.get_memory",
            return_value=[],
        ):
            assert build_memory_context() == ""

        # Test a limit too small for any complete record.
        assert build_memory_context(max_chars=1) == ""

    # Test invalid limits.
    for invalid_limit in (-1, 1.5, "4000", True):
        try:
            build_memory_context(max_chars=invalid_limit)
        except ValueError:
            pass
        else:
            raise AssertionError(
                f"Expected ValueError for {invalid_limit!r}"
            )

    print("All context-builder tests passed.")


if __name__ == "__main__":
    main()