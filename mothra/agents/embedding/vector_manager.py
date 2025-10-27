"""
Vector Manager: Manages embeddings and semantic search with pgvector.

Handles:
- Embedding generation using sentence-transformers (local)
- Batch processing for efficiency
- Vector storage in PostgreSQL with pgvector
- Semantic similarity search
"""

import asyncio
from typing import Any
from uuid import UUID

from sentence_transformers import SentenceTransformer
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from mothra.config import settings
from mothra.db.models import CarbonEntity, EmissionFactor
from mothra.db.models_chunks import DocumentChunk
from mothra.db.session import get_db_context
from mothra.utils.logging import get_logger
from mothra.utils.retry import async_retry
from mothra.utils.text_chunker import TextChunker

logger = get_logger(__name__)


class VectorManager:
    """Manages embeddings and semantic search in PostgreSQL with pgvector."""

    def __init__(self) -> None:
        # Use local sentence-transformers model
        # all-MiniLM-L6-v2: 384 dimensions, fast, good quality
        self.model_name = "sentence-transformers/all-MiniLM-L6-v2"
        self.model = SentenceTransformer(self.model_name)
        self.dimension = 384  # Dimension for all-MiniLM-L6-v2
        self.embedding_dim = self.dimension  # Alias for consistency
        self.batch_size = 100
        self.max_seq_length = 512  # Max sequence length for the model

        # Initialize text chunker for large documents
        # Chunk size ~1500 chars fits comfortably in 512 token window
        self.chunker = TextChunker(
            chunk_size=1500,
            overlap=200,
            max_seq_length=self.max_seq_length
        )

        logger.info("vector_manager_initialized", model=self.model_name, dimension=self.dimension)

    def create_searchable_text(self, entity_data: dict[str, Any]) -> str:
        """
        Create rich text representation for embedding.

        Args:
            entity_data: Entity data dictionary

        Returns:
            Formatted text for embedding
        """
        parts = []

        # Add name and description
        if "name" in entity_data:
            parts.append(f"Name: {entity_data['name']}")

        if "description" in entity_data:
            parts.append(f"Description: {entity_data['description']}")

        # Add entity type and category
        if "entity_type" in entity_data:
            parts.append(f"Type: {entity_data['entity_type']}")

        if "category_hierarchy" in entity_data:
            categories = " > ".join(entity_data["category_hierarchy"])
            parts.append(f"Category: {categories}")

        # Add geographic scope
        if "geographic_scope" in entity_data:
            regions = ", ".join(entity_data["geographic_scope"])
            parts.append(f"Regions: {regions}")

        # Add emission value if available
        if "value" in entity_data and "unit" in entity_data:
            parts.append(f"Emission: {entity_data['value']} {entity_data['unit']}")

        # Add scope
        if "scope" in entity_data:
            parts.append(f"Scope: {entity_data['scope']}")

        # Add tags
        if "custom_tags" in entity_data:
            tags = ", ".join(entity_data["custom_tags"])
            parts.append(f"Tags: {tags}")

        return "\n".join(parts)

    @async_retry(retry_exceptions=(Exception,), max_attempts=3)
    async def generate_embedding(self, text: str) -> list[float]:
        """
        Generate embedding for text using local sentence-transformers model.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        try:
            # Truncate if text is too long (model max is 512 tokens)
            # Rough estimate: 4 chars per token
            if len(text) > self.max_seq_length * 4:
                text = text[:self.max_seq_length * 4]
                logger.debug("text_truncated", max_length=self.max_seq_length * 4)

            # Run model in executor to avoid blocking
            loop = asyncio.get_event_loop()
            embedding = await loop.run_in_executor(
                None,
                lambda: self.model.encode(text, convert_to_numpy=True)
            )

            # Convert numpy array to list
            embedding_list = embedding.tolist()

            logger.debug(
                "embedding_generated",
                text_length=len(text),
                embedding_dim=len(embedding_list)
            )

            return embedding_list

        except Exception as e:
            logger.error("embedding_generation_failed", error=str(e))
            raise

    async def embed_and_store_chunks(
        self, entity_id: UUID, text: str
    ) -> int:
        """
        Chunk large text, generate embeddings for each chunk, and store.

        Args:
            entity_id: Entity UUID
            text: Full text to chunk and embed

        Returns:
            Number of chunks created
        """
        # Generate chunks
        chunk_dicts = self.chunker.chunk_text(text, entity_id=entity_id)

        logger.info(
            "chunking_document",
            entity_id=str(entity_id),
            total_chunks=len(chunk_dicts),
            text_length=len(text)
        )

        # Generate embeddings for each chunk
        async with get_db_context() as db:
            for chunk_dict in chunk_dicts:
                # Generate embedding for chunk
                embedding = await self.generate_embedding(chunk_dict["chunk_text"])
                embedding_str = '[' + ','.join(map(str, embedding)) + ']'

                # Create DocumentChunk object
                chunk = DocumentChunk(
                    entity_id=entity_id,
                    chunk_index=chunk_dict["chunk_index"],
                    total_chunks=chunk_dict["total_chunks"],
                    chunk_text=chunk_dict["chunk_text"],
                    chunk_size=chunk_dict["chunk_size"],
                    start_position=chunk_dict["start_position"],
                    end_position=chunk_dict["end_position"],
                    overlap_before=chunk_dict["overlap_before"],
                    overlap_after=chunk_dict["overlap_after"],
                )

                # Add to session
                db.add(chunk)
                await db.flush()

                # Store embedding using raw asyncpg
                conn = await db.connection()
                raw_conn = await conn.get_raw_connection()
                sql = """
                    UPDATE document_chunks
                    SET embedding = $1::vector
                    WHERE id = $2
                """
                await raw_conn.driver_connection.execute(sql, embedding_str, chunk.id)

            await db.commit()

        logger.info(
            "chunks_embedded",
            entity_id=str(entity_id),
            chunks_created=len(chunk_dicts)
        )

        return len(chunk_dicts)

    async def embed_and_store_entity(
        self, entity_id: UUID, entity_data: dict[str, Any]
    ) -> None:
        """
        Generate embedding and store in database.
        For large documents, creates chunks with individual embeddings.

        Args:
            entity_id: Entity UUID
            entity_data: Entity data for embedding
        """
        # Create searchable text
        text_repr = self.create_searchable_text(entity_data)

        # Check if text needs chunking (threshold: ~1500 chars)
        if len(text_repr) > 1500:
            logger.info(
                "large_document_detected",
                entity_id=str(entity_id),
                text_length=len(text_repr),
                action="chunking"
            )

            # Create chunks and embed them
            await self.embed_and_store_chunks(entity_id, text_repr)

            # Also create a summary embedding for the entity itself
            # Use first 1500 chars as summary
            summary_text = text_repr[:1500]
            embedding = await self.generate_embedding(summary_text)
        else:
            # Small document - single embedding
            embedding = await self.generate_embedding(text_repr)

        # Convert embedding to pgvector format string
        embedding_str = '[' + ','.join(map(str, embedding)) + ']'

        # Store in database using raw asyncpg
        async with get_db_context() as db:
            # Get the raw asyncpg connection
            conn = await db.connection()
            raw_conn = await conn.get_raw_connection()

            # Execute UPDATE using asyncpg directly
            sql = """
                UPDATE carbon_entities
                SET embedding = $1::vector
                WHERE id = $2
            """
            await raw_conn.driver_connection.execute(sql, embedding_str, entity_id)
            await db.commit()

        logger.info("entity_embedded", entity_id=str(entity_id))

    async def embed_batch(self, entities: list[tuple[UUID, dict[str, Any]]]) -> int:
        """
        Process a batch of entities for embedding.

        Args:
            entities: List of (entity_id, entity_data) tuples

        Returns:
            Number of entities successfully embedded
        """
        success_count = 0

        for entity_id, entity_data in entities:
            try:
                await self.embed_and_store_entity(entity_id, entity_data)
                success_count += 1
            except Exception as e:
                logger.error(
                    "batch_embed_failed", entity_id=str(entity_id), error=str(e)
                )

        logger.info("batch_embedded", total=len(entities), successful=success_count)
        return success_count

    async def semantic_search(
        self,
        query: str,
        limit: int = 10,
        similarity_threshold: float = 0.7,
        entity_type: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Perform semantic similarity search.

        Args:
            query: Search query
            limit: Maximum number of results
            similarity_threshold: Minimum similarity score
            entity_type: Optional entity type filter

        Returns:
            List of search results with similarity scores
        """
        # Generate query embedding
        query_embedding = await self.generate_embedding(query)

        # Convert embedding list to pgvector format string
        embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'

        # Build SQL query with positional parameters for asyncpg
        # Note: asyncpg only supports positional parameters ($1, $2, etc.)
        if entity_type:
            sql = """
                SELECT
                    id,
                    name,
                    description,
                    entity_type,
                    geographic_scope,
                    quality_score,
                    1 - (embedding <=> $1::vector) as similarity
                FROM carbon_entities
                WHERE embedding IS NOT NULL
                    AND 1 - (embedding <=> $1::vector) > $2
                    AND entity_type = $3
                ORDER BY embedding <=> $1::vector
                LIMIT $4
            """
            params = [embedding_str, similarity_threshold, entity_type, limit]
        else:
            sql = """
                SELECT
                    id,
                    name,
                    description,
                    entity_type,
                    geographic_scope,
                    quality_score,
                    1 - (embedding <=> $1::vector) as similarity
                FROM carbon_entities
                WHERE embedding IS NOT NULL
                    AND 1 - (embedding <=> $1::vector) > $2
                ORDER BY embedding <=> $1::vector
                LIMIT $3
            """
            params = [embedding_str, similarity_threshold, limit]

        # Use raw asyncpg connection for pgvector queries
        async with get_db_context() as db:
            # Get the raw asyncpg connection from SQLAlchemy
            conn = await db.connection()
            raw_conn = await conn.get_raw_connection()

            # Execute using asyncpg directly
            rows = await raw_conn.driver_connection.fetch(sql, *params)

            results = [
                {
                    "id": str(row[0]),
                    "name": row[1],
                    "description": row[2],
                    "entity_type": row[3],
                    "geographic_scope": row[4],
                    "quality_score": row[5],
                    "similarity": row[6],
                }
                for row in rows
            ]

        logger.info(
            "semantic_search_complete",
            query=query,
            results_count=len(results),
            threshold=similarity_threshold,
        )

        return results

    async def semantic_search_with_chunks(
        self,
        query: str,
        limit: int = 10,
        similarity_threshold: float = 0.7,
        entity_type: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Perform semantic search across both entities and document chunks.
        Aggregates chunk matches to parent entities.

        Args:
            query: Search query
            limit: Maximum number of results
            similarity_threshold: Minimum similarity score
            entity_type: Optional entity type filter

        Returns:
            List of search results with similarity scores
        """
        # Generate query embedding
        query_embedding = await self.generate_embedding(query)
        embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'

        # Search both entities and chunks, aggregate by entity
        if entity_type:
            sql = """
                WITH entity_matches AS (
                    SELECT
                        id as entity_id,
                        name,
                        description,
                        entity_type,
                        geographic_scope,
                        quality_score,
                        1 - (embedding <=> $1::vector) as similarity,
                        'entity' as match_type
                    FROM carbon_entities
                    WHERE embedding IS NOT NULL
                        AND 1 - (embedding <=> $1::vector) > $2
                        AND entity_type = $3
                ),
                chunk_matches AS (
                    SELECT
                        c.entity_id,
                        e.name,
                        e.description,
                        e.entity_type,
                        e.geographic_scope,
                        e.quality_score,
                        MAX(1 - (c.embedding <=> $1::vector)) as similarity,
                        'chunk' as match_type
                    FROM document_chunks c
                    JOIN carbon_entities e ON c.entity_id = e.id
                    WHERE c.embedding IS NOT NULL
                        AND 1 - (c.embedding <=> $1::vector) > $2
                        AND e.entity_type = $3
                    GROUP BY c.entity_id, e.name, e.description, e.entity_type,
                             e.geographic_scope, e.quality_score
                ),
                all_matches AS (
                    SELECT * FROM entity_matches
                    UNION ALL
                    SELECT * FROM chunk_matches
                )
                SELECT
                    entity_id,
                    name,
                    description,
                    entity_type,
                    geographic_scope,
                    quality_score,
                    MAX(similarity) as similarity,
                    STRING_AGG(DISTINCT match_type, ', ' ORDER BY match_type) as match_types
                FROM all_matches
                GROUP BY entity_id, name, description, entity_type, geographic_scope, quality_score
                ORDER BY MAX(similarity) DESC
                LIMIT $4
            """
            params = [embedding_str, similarity_threshold, entity_type, limit]
        else:
            sql = """
                WITH entity_matches AS (
                    SELECT
                        id as entity_id,
                        name,
                        description,
                        entity_type,
                        geographic_scope,
                        quality_score,
                        1 - (embedding <=> $1::vector) as similarity,
                        'entity' as match_type
                    FROM carbon_entities
                    WHERE embedding IS NOT NULL
                        AND 1 - (embedding <=> $1::vector) > $2
                ),
                chunk_matches AS (
                    SELECT
                        c.entity_id,
                        e.name,
                        e.description,
                        e.entity_type,
                        e.geographic_scope,
                        e.quality_score,
                        MAX(1 - (c.embedding <=> $1::vector)) as similarity,
                        'chunk' as match_type
                    FROM document_chunks c
                    JOIN carbon_entities e ON c.entity_id = e.id
                    WHERE c.embedding IS NOT NULL
                        AND 1 - (c.embedding <=> $1::vector) > $2
                    GROUP BY c.entity_id, e.name, e.description, e.entity_type,
                             e.geographic_scope, e.quality_score
                ),
                all_matches AS (
                    SELECT * FROM entity_matches
                    UNION ALL
                    SELECT * FROM chunk_matches
                )
                SELECT
                    entity_id,
                    name,
                    description,
                    entity_type,
                    geographic_scope,
                    quality_score,
                    MAX(similarity) as similarity,
                    STRING_AGG(DISTINCT match_type, ', ' ORDER BY match_type) as match_types
                FROM all_matches
                GROUP BY entity_id, name, description, entity_type, geographic_scope, quality_score
                ORDER BY MAX(similarity) DESC
                LIMIT $3
            """
            params = [embedding_str, similarity_threshold, limit]

        # Execute query
        async with get_db_context() as db:
            conn = await db.connection()
            raw_conn = await conn.get_raw_connection()
            rows = await raw_conn.driver_connection.fetch(sql, *params)

            results = [
                {
                    "id": str(row[0]),
                    "name": row[1],
                    "description": row[2],
                    "entity_type": row[3],
                    "geographic_scope": row[4],
                    "quality_score": row[5],
                    "similarity": row[6],
                    "match_types": row[7],  # Shows if matched via entity, chunk, or both
                }
                for row in rows
            ]

        logger.info(
            "chunk_aware_search_complete",
            query=query,
            results_count=len(results),
            threshold=similarity_threshold,
        )

        return results

    async def reindex_all(self) -> int:
        """
        Reindex all entities without embeddings.

        Returns:
            Number of entities reindexed
        """
        async with get_db_context() as db:
            # Get entities without embeddings
            stmt = select(CarbonEntity).where(CarbonEntity.embedding.is_(None))
            result = await db.execute(stmt)
            entities = result.scalars().all()

            total = len(entities)
            logger.info("reindexing_started", total_entities=total)

            # Process in batches
            reindexed = 0
            for i in range(0, total, self.batch_size):
                batch = entities[i : i + self.batch_size]
                batch_data = [
                    (
                        entity.id,
                        {
                            "name": entity.name,
                            "description": entity.description,
                            "entity_type": entity.entity_type,
                            "category_hierarchy": entity.category_hierarchy,
                            "geographic_scope": entity.geographic_scope,
                            "custom_tags": entity.custom_tags,
                        },
                    )
                    for entity in batch
                ]

                count = await self.embed_batch(batch_data)
                reindexed += count

                logger.info(
                    "reindex_progress",
                    processed=i + len(batch),
                    total=total,
                    success=reindexed,
                )

                # Small delay between batches
                await asyncio.sleep(0.1)

        logger.info("reindex_complete", total=total, reindexed=reindexed)
        return reindexed


async def main() -> None:
    """CLI entry point for vector manager."""
    logger.info("vector_manager_starting")

    manager = VectorManager()

    # Example: Reindex all entities
    count = await manager.reindex_all()
    logger.info("vector_manager_complete", reindexed=count)


if __name__ == "__main__":
    asyncio.run(main())
