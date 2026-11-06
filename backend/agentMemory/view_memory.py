from backend.agentMemory.persistMem import get_memory


def main():
    memories = get_memory()

    print("\n===== STORED MEMORIES =====")

    if not memories:
        print("No memories found.")
    else:
        for memory in memories:
            print(f"\nID: {memory['id']}")
            print(f"Category: {memory['category']}")
            print(f"Content: {memory['content']}")
            print(f"Created At: {memory['created_at']}")

    print("\n===========================\n")


if __name__ == "__main__":
    main()
