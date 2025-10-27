#!/usr/bin/env python3
"""
EPD Vector Store Query Example
==============================
Demonstrates how to query the EPD vector store using semantic search.

Usage:
    python scripts/query_epd_vector_store.py "low carbon concrete"
    python scripts/query_epd_vector_store.py "recycled steel" --limit 20
    python scripts/query_epd_vector_store.py "sustainable wood products" --with-chunks
"""

import asyncio
import argparse
import sys
from pathlib import Path
from typing import Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mothra.agents.embedding.vector_manager import VectorManager
from mothra.db.session import AsyncSessionLocal
from mothra.db.models import CarbonEntity
from mothra.db.models_verification import CarbonEntityVerification


class EPDQueryInterface:
    """Interactive interface for querying EPD vector store."""

    def __init__(self):
        self.vector_manager = VectorManager()

    async def search_entities(
        self,
        query: str,
        limit: int = 10,
        similarity_threshold: float = 0.7,
        entity_type: Optional[str] = "product"
    ):
        """Search for EPD entities using semantic search."""
        print(f"\n{'='*80}")
        print(f"SEMANTIC SEARCH: {query}")
        print(f"{'='*80}\n")

        async with AsyncSessionLocal() as session:
            results = await self.vector_manager.semantic_search(
                query=query,
                session=session,
                entity_type=entity_type,
                limit=limit,
                similarity_threshold=similarity_threshold
            )

            if not results:
                print("No results found. Try lowering the similarity threshold.")
                return

            print(f"Found {len(results)} results:\n")

            for idx, (entity, similarity) in enumerate(results, 1):
                await self._print_entity_result(entity, similarity, idx, session)

    async def search_with_chunks(
        self,
        query: str,
        limit: int = 10,
        similarity_threshold: float = 0.7
    ):
        """Search EPDs with chunk-level details."""
        print(f"\n{'='*80}")
        print(f"CHUNK-BASED SEARCH: {query}")
        print(f"{'='*80}\n")

        async with AsyncSessionLocal() as session:
            results = await self.vector_manager.semantic_search_with_chunks(
                query=query,
                session=session,
                limit=limit,
                similarity_threshold=similarity_threshold
            )

            if not results:
                print("No results found. Try lowering the similarity threshold.")
                return

            print(f"Found {len(results)} chunk matches:\n")

            for idx, (entity, chunk, similarity) in enumerate(results, 1):
                print(f"{idx}. {entity.name}")
                print(f"   Similarity: {similarity:.3f}")
                print(f"   Chunk: {chunk.chunk_index + 1}/{chunk.total_chunks}")
                print(f"   Text: {chunk.chunk_text[:200]}...")
                print()

    async def _print_entity_result(
        self,
        entity: CarbonEntity,
        similarity: float,
        idx: int,
        session
    ):
        """Pretty print an entity result."""
        print(f"{idx}. {entity.name}")
        print(f"   Similarity: {similarity:.3f}")

        # Get verification data if available
        from sqlalchemy import select
        result = await session.execute(
            select(CarbonEntityVerification).where(
                CarbonEntityVerification.entity_id == entity.id
            )
        )
        verification = result.scalar_one_or_none()

        if verification:
            if verification.gwp_total:
                print(f"   GWP Total: {verification.gwp_total:.2f} kg CO2e")

            if verification.epd_registration_number:
                print(f"   EPD #: {verification.epd_registration_number}")

            if verification.third_party_verified:
                print(f"   Third-party verified: Yes")

            if verification.lca_stages_included:
                stages = ", ".join(verification.lca_stages_included)
                print(f"   LCA Stages: {stages}")

        if entity.category_hierarchy:
            categories = " > ".join(entity.category_hierarchy)
            print(f"   Categories: {categories}")

        if entity.geographic_scope:
            print(f"   Geography: {entity.geographic_scope}")

        if entity.description:
            desc = entity.description[:150]
            if len(entity.description) > 150:
                desc += "..."
            print(f"   Description: {desc}")

        print()

    async def interactive_mode(self):
        """Interactive query mode."""
        print("\n" + "="*80)
        print("EPD VECTOR STORE - INTERACTIVE MODE")
        print("="*80)
        print("\nCommands:")
        print("  search <query>          - Search for EPDs")
        print("  chunks <query>          - Search with chunk details")
        print("  limit <n>               - Set result limit (default: 10)")
        print("  threshold <0.0-1.0>     - Set similarity threshold (default: 0.7)")
        print("  help                    - Show this help")
        print("  quit                    - Exit")
        print("\nType your queries or commands below:")
        print("="*80 + "\n")

        limit = 10
        threshold = 0.7

        while True:
            try:
                query = input("> ").strip()

                if not query:
                    continue

                if query.lower() in ('quit', 'exit', 'q'):
                    print("Goodbye!")
                    break

                if query.lower() == 'help':
                    print("\nCommands:")
                    print("  search <query>          - Search for EPDs")
                    print("  chunks <query>          - Search with chunk details")
                    print("  limit <n>               - Set result limit")
                    print("  threshold <0.0-1.0>     - Set similarity threshold")
                    print("  help                    - Show this help")
                    print("  quit                    - Exit\n")
                    continue

                if query.startswith('limit '):
                    try:
                        limit = int(query.split()[1])
                        print(f"Result limit set to: {limit}\n")
                    except (IndexError, ValueError):
                        print("Usage: limit <number>\n")
                    continue

                if query.startswith('threshold '):
                    try:
                        threshold = float(query.split()[1])
                        if 0 <= threshold <= 1:
                            print(f"Similarity threshold set to: {threshold}\n")
                        else:
                            print("Threshold must be between 0.0 and 1.0\n")
                    except (IndexError, ValueError):
                        print("Usage: threshold <0.0-1.0>\n")
                    continue

                if query.startswith('chunks '):
                    search_query = query[7:].strip()
                    await self.search_with_chunks(
                        search_query,
                        limit=limit,
                        similarity_threshold=threshold
                    )
                    continue

                if query.startswith('search '):
                    search_query = query[7:].strip()
                else:
                    search_query = query

                await self.search_entities(
                    search_query,
                    limit=limit,
                    similarity_threshold=threshold
                )

            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {e}\n")


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Query EPD vector store using semantic search"
    )
    parser.add_argument(
        'query',
        nargs='*',
        help='Search query (omit for interactive mode)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=10,
        help='Maximum number of results (default: 10)'
    )
    parser.add_argument(
        '--threshold',
        type=float,
        default=0.7,
        help='Similarity threshold 0.0-1.0 (default: 0.7)'
    )
    parser.add_argument(
        '--with-chunks',
        action='store_true',
        help='Show chunk-level details'
    )
    parser.add_argument(
        '--interactive',
        action='store_true',
        help='Start interactive mode'
    )

    args = parser.parse_args()

    interface = EPDQueryInterface()

    # Interactive mode
    if args.interactive or not args.query:
        await interface.interactive_mode()
        return

    # Single query mode
    query_text = ' '.join(args.query)

    if args.with_chunks:
        await interface.search_with_chunks(
            query_text,
            limit=args.limit,
            similarity_threshold=args.threshold
        )
    else:
        await interface.search_entities(
            query_text,
            limit=args.limit,
            similarity_threshold=args.threshold
        )


if __name__ == "__main__":
    asyncio.run(main())
