"""
Graph nodes for DocumentManager agent
"""

import os
from pathlib import Path
from uuid import uuid4

from backend.agents.specialized.agent_d.state import DocumentManagerState
from backend.memory.document_store import DocumentStore
from backend.models.document_models import CollectionCreate, ChunkCreate
from backend.repositories.collection_repository import CollectionRepository
from backend.repositories.chunk_repository import ChunkRepository
from backend.repositories.task_repository import get_session_factory
from backend.tools.document_loaders import (
    PDFLoader,
    DocxLoader,
    TextLoader,
    DocumentChunker,
)


async def parse_input_node(state: DocumentManagerState) -> dict:
    """
    Classify user intent and extract parameters from query
    """
    import re

    query = state["query"]
    query_lower = query.lower()

    # Extract quoted strings (file paths or search queries)
    quoted_strings = re.findall(r'"([^"]+)"', query)

    # Extract collection name patterns like "into collection_name" or "search collection_name"
    collection_match = re.search(r'(?:into|collection|search)\s+([a-zA-Z0-9_-]+)', query_lower)
    collection_name = collection_match.group(1) if collection_match else None

    # Special handling for search commands: "search collection_name for query"
    search_pattern = re.search(r'search\s+([a-zA-Z0-9_-]+)\s+for', query_lower)
    if search_pattern:
        collection_name = search_pattern.group(1)

    # Extract file path (look for paths starting with / or containing file extensions)
    file_path = None
    for part in query.split():
        if part.startswith('/') or part.startswith('~') or any(ext in part for ext in ['.pdf', '.docx', '.txt', '.md', '.rtf']):
            file_path = part.strip('"').strip("'")
            break

    # If no file path found in split, check quoted strings
    if not file_path and quoted_strings:
        for quoted in quoted_strings:
            if '/' in quoted or any(ext in quoted for ext in ['.pdf', '.docx', '.txt', '.md', '.rtf']):
                file_path = quoted
                break

    # Classify action based on keywords
    if "load" in query_lower or "upload" in query_lower or "add document" in query_lower:
        action_type = "load_file"
        params = {
            "file_path": file_path,
            "collection_name": collection_name or "default",
        }

    elif "create collection" in query_lower or "new collection" in query_lower:
        action_type = "create_collection"
        # Extract collection name after "create collection"
        match = re.search(r'(?:create|new)\s+collection\s+([a-zA-Z0-9_-]+)', query_lower)
        collection_name = match.group(1) if match else "default"
        params = {"collection_name": collection_name}

    elif "delete collection" in query_lower or "remove collection" in query_lower:
        action_type = "delete_collection"
        # Extract collection name after "delete collection"
        match = re.search(r'(?:delete|remove)\s+collection\s+([a-zA-Z0-9_-]+)', query_lower)
        collection_name = match.group(1) if match else None
        params = {"collection_name": collection_name}

    elif "list collection" in query_lower or "show collection" in query_lower or "my collection" in query_lower:
        action_type = "list_collections"
        params = {}

    elif "search all" in query_lower or "search everything" in query_lower:
        action_type = "search_all"
        # Extract search query (everything after "for" or quoted string)
        search_query = query
        for_match = re.search(r'for\s+(.+)$', query, re.IGNORECASE)
        if for_match:
            search_query = for_match.group(1).strip('"').strip("'")
        elif quoted_strings:
            search_query = quoted_strings[0]
        params = {"query": search_query}

    elif "search" in query_lower:
        action_type = "search_collection"
        # Extract search query and collection
        search_query = query
        for_match = re.search(r'for\s+(.+)$', query, re.IGNORECASE)
        if for_match:
            search_query = for_match.group(1).strip('"').strip("'")
        elif quoted_strings:
            search_query = quoted_strings[0]
        params = {
            "query": search_query,
            "collection_name": collection_name,
        }

    else:
        action_type = "list_collections"
        params = {}

    return {
        "action_type": action_type,
        "action_params": params,
        "collection_name": params.get("collection_name"),
        "file_path": params.get("file_path"),
        "current_step": "parse_input",
    }


async def create_collection_node(state: DocumentManagerState) -> dict:
    """Create new document collection"""
    try:
        session_factory = get_session_factory()
        async with session_factory() as session:
            collection_repo = CollectionRepository(session)

            # Extract collection name from state (set by parse_input_node)
            collection_name = state.get("collection_name") or state["action_params"].get("collection_name") or "default_collection"

            # Check if collection already exists
            existing = await collection_repo.get_collection_by_name(
                user_id=state["user_id"], collection_name=collection_name
            )

            if existing:
                return {
                    **state,
                    "final_response": f"Collection '{collection_name}' already exists.",
                    "error": "Collection already exists",
                    "current_step": "create_collection",
                }

            # Create collection in database
            collection_create = CollectionCreate(
                user_id=state["user_id"],
                collection_name=collection_name,
                description=f"Collection for {collection_name}",
            )
            collection = await collection_repo.create_collection(collection_create)

            # Create Qdrant collection
            doc_store = DocumentStore()
            await doc_store.connect()
            await doc_store.create_collection(
                qdrant_collection_name=collection.qdrant_collection_name,
                user_id=state["user_id"],
            )
            await doc_store.disconnect()

            return {
                **state,
                "collection_id": str(collection.id),
                "collection_name": collection.collection_name,
                "final_response": f"✓ Created collection '{collection_name}' successfully.",
                "current_step": "create_collection",
            }

    except Exception as e:
        return {
            **state,
            "error": str(e),
            "final_response": f"Failed to create collection: {str(e)}",
            "current_step": "create_collection",
        }


async def delete_collection_node(state: DocumentManagerState) -> dict:
    """Delete document collection"""
    try:
        session_factory = get_session_factory()
        async with session_factory() as session:
            collection_repo = CollectionRepository(session)

            collection_name = state.get("collection_name") or state["action_params"].get("collection_name")
            if not collection_name:
                return {
                    **state,
                    "error": "No collection name specified",
                    "final_response": "Please specify which collection to delete.",
                    "current_step": "delete_collection",
                }

            # Get collection
            collection = await collection_repo.get_collection_by_name(
                user_id=state["user_id"], collection_name=collection_name
            )

            if not collection:
                return {
                    **state,
                    "error": "Collection not found",
                    "final_response": f"Collection '{collection_name}' not found.",
                    "current_step": "delete_collection",
                }

            # Delete from Qdrant
            doc_store = DocumentStore()
            await doc_store.connect()
            await doc_store.delete_collection(collection.qdrant_collection_name)
            await doc_store.disconnect()

            # Delete from database (cascades to chunks)
            await collection_repo.delete_collection(collection.id)

            return {
                **state,
                "final_response": f"✓ Deleted collection '{collection_name}' ({collection.chunk_count} chunks).",
                "current_step": "delete_collection",
            }

    except Exception as e:
        return {
            **state,
            "error": str(e),
            "final_response": f"Failed to delete collection: {str(e)}",
            "current_step": "delete_collection",
        }


async def list_collections_node(state: DocumentManagerState) -> dict:
    """List all user collections"""
    try:
        session_factory = get_session_factory()
        async with session_factory() as session:
            collection_repo = CollectionRepository(session)

            collections = await collection_repo.list_user_collections(
                user_id=state["user_id"]
            )

            if not collections:
                return {
                    "collection_list": [],
                    "final_response": "You don't have any collections yet. Create one with 'create collection <name>'.",
                    "current_step": "list_collections",
                }

            collection_list = [
                {
                    "name": c.collection_name,
                    "chunk_count": c.chunk_count,
                    "created_at": str(c.created_at),
                }
                for c in collections
            ]

            # Format response
            response_lines = ["Your document collections:"]
            for c in collections:
                response_lines.append(
                    f"  • {c.collection_name} ({c.chunk_count} chunks) - created {c.created_at.strftime('%Y-%m-%d')}"
                )

            return {
                "collection_list": collection_list,
                "final_response": "\n".join(response_lines),
                "current_step": "list_collections",
            }

    except Exception as e:
        return {
            "error": str(e),
            "final_response": f"Failed to list collections: {str(e)}",
            "current_step": "list_collections",
        }


async def load_file_node(state: DocumentManagerState) -> dict:
    """Load document from file path"""
    try:
        file_path = state.get("file_path")
        if not file_path:
            return {
                "error": "No file path provided",
                "final_response": "Please provide a file path to load.",
                "current_step": "load_file",
            }

        # Check if file exists
        if not os.path.exists(file_path):
            return {
                "error": "File not found",
                "final_response": f"File not found: {file_path}",
                "current_step": "load_file",
            }

        # Determine file type and use appropriate loader
        file_ext = Path(file_path).suffix.lower()

        if file_ext == ".pdf":
            loader = PDFLoader()
        elif file_ext == ".docx":
            loader = DocxLoader()
        elif file_ext in [".txt", ".md", ".rtf"]:
            loader = TextLoader()
        else:
            return {
                "error": "Unsupported file type",
                "final_response": f"Unsupported file type: {file_ext}. Supported: .pdf, .docx, .txt, .md, .rtf",
                "current_step": "load_file",
            }

        # Load document
        content = await loader.load(file_path)

        return {
            **state,
            "raw_content": content,
            "current_step": "load_file",
        }

    except Exception as e:
        return {
            "error": str(e),
            "final_response": f"Failed to load file: {str(e)}",
            "current_step": "load_file",
        }


async def chunk_and_embed_node(state: DocumentManagerState) -> dict:
    """Chunk document content"""
    try:
        content = state.get("raw_content")
        if not content:
            return {
                "error": "No content to chunk",
                "current_step": "chunk_and_embed",
            }

        file_path = state.get("file_path", "")
        file_name = Path(file_path).name if file_path else "unknown"

        # Chunk document
        chunker = DocumentChunker()
        chunks = await chunker.chunk_document(
            content=content,
            metadata={
                "source_file": file_name,
                "source_path": file_path,
            },
        )

        return {
            **state,
            "chunks": chunks,
            "current_step": "chunk_and_embed",
        }

    except Exception as e:
        return {
            "error": str(e),
            "final_response": f"Failed to chunk document: {str(e)}",
            "current_step": "chunk_and_embed",
        }


async def store_chunks_node(state: DocumentManagerState) -> dict:
    """Store chunks in collection"""
    try:
        chunks = state.get("chunks")
        if not chunks:
            return {
                **state,
                "error": "No chunks to store",
                "final_response": "Failed to store chunks: No chunks generated from document",
                "current_step": "store_chunks",
            }

        collection_name = (
            state.get("collection_name") or
            state["action_params"].get("collection_name") or
            "default"
        )
        file_path = (
            state.get("file_path") or
            state["action_params"].get("file_path") or
            ""
        )
        file_name = Path(file_path).name if file_path else "unknown"

        session_factory = get_session_factory()
        async with session_factory() as session:
            collection_repo = CollectionRepository(session)
            chunk_repo = ChunkRepository(session)

            # Get or create collection
            collection = await collection_repo.get_collection_by_name(
                user_id=state["user_id"], collection_name=collection_name
            )

            if not collection:
                # Create collection
                collection_create = CollectionCreate(
                    user_id=state["user_id"],
                    collection_name=collection_name,
                    description=f"Collection for {collection_name}",
                )
                collection = await collection_repo.create_collection(collection_create)

                # Create Qdrant collection
                doc_store = DocumentStore()
                await doc_store.connect()
                await doc_store.create_collection(
                    qdrant_collection_name=collection.qdrant_collection_name,
                    user_id=state["user_id"],
                )
                await doc_store.disconnect()

            # Prepare chunks for storage
            chunk_creates = []
            for chunk in chunks:
                vector_id = uuid4()
                chunk_create = ChunkCreate(
                    collection_id=collection.id,
                    user_id=state["user_id"],
                    content=chunk["content"],
                    chunk_index=chunk["chunk_index"],
                    source_type="file",
                    source_file_path=file_path,
                    file_name=file_name,
                    metadata=chunk.get("metadata", {}),
                    vector_id=vector_id,
                )
                chunk_creates.append(chunk_create)

            # Store in database
            stored_chunks = await chunk_repo.create_chunks(chunk_creates)

            # Store embeddings in Qdrant
            doc_store = DocumentStore()
            await doc_store.connect()
            await doc_store.store_chunks(
                qdrant_collection_name=collection.qdrant_collection_name,
                chunks=chunk_creates,
            )
            await doc_store.disconnect()

            # Update collection chunk count
            await collection_repo.increment_chunk_count(
                collection_id=collection.id, increment=len(chunk_creates)
            )

            return {
                "collection_id": str(collection.id),
                "final_response": f"✓ Loaded '{file_name}' into collection '{collection_name}' ({len(chunk_creates)} chunks).",
                "current_step": "store_chunks",
            }

    except Exception as e:
        return {
            "error": str(e),
            "final_response": f"Failed to store chunks: {str(e)}",
            "current_step": "store_chunks",
        }


async def search_collection_node(state: DocumentManagerState) -> dict:
    """Search specific collection"""
    try:
        query = state["action_params"].get("query", state["query"])
        collection_name = state.get("collection_name") or state["action_params"].get("collection_name")

        if not collection_name:
            return {
                **state,
                "error": "No collection specified",
                "final_response": "Please specify which collection to search.",
                "current_step": "search_collection",
            }

        session_factory = get_session_factory()
        async with session_factory() as session:
            collection_repo = CollectionRepository(session)
            chunk_repo = ChunkRepository(session)

            # Get collection
            collection = await collection_repo.get_collection_by_name(
                user_id=state["user_id"], collection_name=collection_name
            )

            if not collection:
                return {
                    **state,
                    "error": "Collection not found",
                    "final_response": f"Collection '{collection_name}' not found.",
                    "current_step": "search_collection",
                }

            # Search in Qdrant
            doc_store = DocumentStore()
            await doc_store.connect()
            vector_results = await doc_store.search_collection(
                qdrant_collection_name=collection.qdrant_collection_name,
                user_id=state["user_id"],
                query=query,
                limit=10,
            )
            await doc_store.disconnect()

            if not vector_results:
                return {
                    **state,
                    "search_results": [],
                    "final_response": f"No results found in '{collection_name}' for query: {query}",
                    "current_step": "search_collection",
                }

            # Fetch chunk details from database
            search_results = []
            for vector_id, score in vector_results:
                chunk = await chunk_repo.get_chunk_by_vector_id(vector_id)
                if chunk:
                    search_results.append(
                        {
                            "content": chunk.content[:500],  # Truncate for display
                            "score": score,
                            "file_name": chunk.file_name,
                            "chunk_index": chunk.chunk_index,
                        }
                    )

            # Format response
            response_lines = [f"Found {len(search_results)} results in '{collection_name}':"]
            for idx, result in enumerate(search_results[:5], 1):
                response_lines.append(
                    f"\n{idx}. [{result['file_name']} - chunk {result['chunk_index']}] (score: {result['score']:.2f})"
                )
                response_lines.append(f"   {result['content'][:200]}...")

            return {
                **state,
                "search_results": search_results,
                "final_response": "\n".join(response_lines),
                "current_step": "search_collection",
            }

    except Exception as e:
        return {
            **state,
            "error": str(e),
            "final_response": f"Search failed: {str(e)}",
            "current_step": "search_collection",
        }


async def search_all_node(state: DocumentManagerState) -> dict:
    """Search all user collections"""
    try:
        query = state["action_params"].get("query", state["query"])

        session_factory = get_session_factory()
        async with session_factory() as session:
            collection_repo = CollectionRepository(session)
            chunk_repo = ChunkRepository(session)

            # Get all user collections
            collections = await collection_repo.list_user_collections(user_id=state["user_id"])

            if not collections:
                return {
                    **state,
                    "search_results": [],
                    "final_response": "You don't have any collections yet.",
                    "current_step": "search_all",
                }

            # Search across all collections
            qdrant_collection_names = [c.qdrant_collection_name for c in collections]

            doc_store = DocumentStore()
            await doc_store.connect()
            all_results = await doc_store.search_all_collections(
                collection_names=qdrant_collection_names,
                user_id=state["user_id"],
                query=query,
                limit=10,
            )
            await doc_store.disconnect()

            if not all_results:
                return {
                    **state,
                    "search_results": [],
                    "final_response": f"No results found across all collections for: {query}",
                    "current_step": "search_all",
                }

            # Fetch chunk details
            search_results = []
            for qdrant_collection_name, vector_id, score in all_results:
                chunk = await chunk_repo.get_chunk_by_vector_id(vector_id)
                if chunk:
                    # Find collection name
                    coll = next(
                        (c for c in collections if c.qdrant_collection_name == qdrant_collection_name),
                        None,
                    )
                    collection_name = coll.collection_name if coll else "unknown"

                    search_results.append(
                        {
                            "content": chunk.content[:500],
                            "score": score,
                            "file_name": chunk.file_name,
                            "chunk_index": chunk.chunk_index,
                            "collection_name": collection_name,
                        }
                    )

            # Format response
            response_lines = [f"Found {len(search_results)} results across all collections:"]
            for idx, result in enumerate(search_results[:5], 1):
                response_lines.append(
                    f"\n{idx}. [{result['collection_name']} / {result['file_name']} - chunk {result['chunk_index']}] (score: {result['score']:.2f})"
                )
                response_lines.append(f"   {result['content'][:200]}...")

            return {
                "search_results": search_results,
                "final_response": "\n".join(response_lines),
                "current_step": "search_all",
            }

    except Exception as e:
        return {
            "error": str(e),
            "final_response": f"Search failed: {str(e)}",
            "current_step": "search_all",
        }


async def finalize_response_node(state: DocumentManagerState) -> dict:
    """Format and return final response"""
    if state.get("error"):
        return {
            "final_response": state.get("final_response", f"Error: {state['error']}"),
            "current_step": "finalize",
        }

    return {
        "final_response": state.get("final_response", "Task completed."),
        "current_step": "finalize",
    }


def route_action(state: DocumentManagerState) -> str:
    """Route to appropriate action node based on action_type"""
    action_type = state.get("action_type", "search_all")

    action_map = {
        "load_file": "load_file",
        "create_collection": "create_collection",
        "delete_collection": "delete_collection",
        "list_collections": "list_collections",
        "search_collection": "search_collection",
        "search_all": "search_all",
    }

    return action_map.get(action_type, "search_all")
