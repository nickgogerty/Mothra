"""
Test semantic search functionality.

This script demonstrates the semantic search capabilities by searching for
carbon-related queries and displaying results with similarity scores.
"""

import asyncio

from mothra.agents.embedding.vector_manager import VectorManager
from mothra.utils.logging import get_logger

logger = get_logger(__name__)

# Sample queries to demonstrate search
SAMPLE_QUERIES = [
    "steel production emissions",
    "electricity from renewable sources",
    "transportation by truck",
    "concrete and cement manufacturing",
    "agriculture and livestock",
    "plastic materials",
    "waste disposal and methane",
]


async def test_search_query(manager: VectorManager, query: str) -> None:
    """Test a single search query."""
    print(f"\n{'=' * 80}")
    print(f"🔍 Query: '{query}'")
    print('=' * 80)

    try:
        results = await manager.semantic_search(
            query=query,
            limit=5,
            similarity_threshold=0.3,  # Lower threshold to show more results
        )

        if not results:
            print("No results found.")
            return

        print(f"\nFound {len(results)} results:\n")

        for i, result in enumerate(results, 1):
            print(f"{i}. {result['name']}")
            print(f"   Type: {result['entity_type']}")
            print(f"   Similarity: {result['similarity']:.3f} ({result['similarity']*100:.1f}%)")
            print(f"   Quality: {result['quality_score']:.2f}")
            if result['description']:
                # Truncate long descriptions
                desc = result['description'][:200]
                if len(result['description']) > 200:
                    desc += "..."
                print(f"   Description: {desc}")
            print()

    except Exception as e:
        logger.error("search_failed", query=query, error=str(e))
        print(f"❌ Search failed: {e}")


async def main() -> None:
    """Run search tests."""
    print("=" * 80)
    print("MOTHRA Semantic Search Test")
    print("=" * 80)

    manager = VectorManager()

    # Test predefined queries
    print("\n📊 Testing sample queries...\n")
    for query in SAMPLE_QUERIES:
        await test_search_query(manager, query)
        await asyncio.sleep(0.5)  # Small delay between searches

    # Interactive mode
    print("\n" + "=" * 80)
    print("Interactive Search Mode")
    print("=" * 80)
    print("Enter search queries (or 'quit' to exit):\n")

    while True:
        try:
            query = input("🔍 Search: ").strip()

            if query.lower() in ['quit', 'exit', 'q']:
                break

            if not query:
                continue

            await test_search_query(manager, query)

        except KeyboardInterrupt:
            print("\n\nExiting...")
            break
        except EOFError:
            break

    print("\n✅ Search tests complete!")


if __name__ == "__main__":
    asyncio.run(main())
