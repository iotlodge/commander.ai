"""
Test script for DocumentManager Agent (Alice)
Tests collection management, document loading, and search functionality
"""

import asyncio
from uuid import UUID, uuid4
from pathlib import Path

from backend.agents.specialized.agent_d.graph import DocumentManagerAgent
from backend.agents.base.agent_interface import AgentExecutionContext
from backend.repositories.collection_repository import CollectionRepository
from backend.repositories.chunk_repository import ChunkRepository
from backend.repositories.task_repository import get_session_factory
from backend.memory.document_store import DocumentStore


# Test user ID (using MVP user)
TEST_USER_ID = UUID("00000000-0000-0000-0000-000000000001")
TEST_THREAD_ID = uuid4()


async def cleanup_test_collections():
    """Clean up any existing test collections"""
    print("🧹 Cleaning up existing test collections...")
    session_factory = get_session_factory()
    async with session_factory() as session:
        collection_repo = CollectionRepository(session)
        collections = await collection_repo.list_user_collections(TEST_USER_ID)

        doc_store = DocumentStore()
        await doc_store.connect()

        for collection in collections:
            if collection.collection_name.startswith("test_"):
                print(f"   Deleting: {collection.collection_name}")
                try:
                    await doc_store.delete_collection(collection.qdrant_collection_name)
                except Exception as e:
                    print(f"   Warning: Could not delete Qdrant collection: {e}")
                await collection_repo.delete_collection(collection.id)

        await doc_store.disconnect()
    print("✓ Cleanup complete\n")


async def test_create_collection():
    """Test 1: Create a new collection"""
    print("📦 Test 1: Creating test collection...")

    alice = DocumentManagerAgent()
    await alice.initialize()

    context = AgentExecutionContext(
        user_id=TEST_USER_ID,
        thread_id=TEST_THREAD_ID,
        command="create collection test_research_papers",
    )

    # Manually set collection name in state for testing
    initial_state = {
        "query": "create collection test_research_papers",
        "user_id": TEST_USER_ID,
        "thread_id": TEST_THREAD_ID,
        "conversation_context": {},
        "action_type": "create_collection",
        "action_params": {},
        "collection_name": "test_research_papers",
        "collection_id": None,
        "collection_list": None,
        "file_path": None,
        "raw_content": None,
        "chunks": None,
        "search_results": None,
        "final_response": None,
        "error": None,
        "current_step": "starting",
        "task_callback": None,
    }

    from backend.agents.specialized.agent_d.nodes import create_collection_node
    result_state = await create_collection_node(initial_state)

    if result_state.get("error"):
        print(f"✗ Failed: {result_state['error']}")
        return False

    print(f"✓ {result_state['final_response']}")
    print(f"   Collection ID: {result_state.get('collection_id')}\n")
    return True


async def test_list_collections():
    """Test 2: List all collections"""
    print("📋 Test 2: Listing collections...")

    from backend.agents.specialized.agent_d.nodes import list_collections_node

    initial_state = {
        "query": "list my collections",
        "user_id": TEST_USER_ID,
        "thread_id": TEST_THREAD_ID,
        "conversation_context": {},
        "action_type": "list_collections",
        "action_params": {},
        "collection_name": None,
        "collection_id": None,
        "collection_list": None,
        "file_path": None,
        "raw_content": None,
        "chunks": None,
        "search_results": None,
        "final_response": None,
        "error": None,
        "current_step": "starting",
        "task_callback": None,
    }

    result_state = await list_collections_node(initial_state)

    if result_state.get("error"):
        print(f"✗ Failed: {result_state['error']}")
        return False

    print(f"✓ {result_state['final_response']}\n")
    return True


async def test_load_document():
    """Test 3: Load a sample document"""
    print("📄 Test 3: Loading sample document...")

    # Create a sample markdown file for testing
    test_file_path = Path("/tmp/test_document.md")
    test_content = """# Sample Research Document

## Introduction
This is a test document for the DocumentManager agent.
It contains multiple sections to test the chunking functionality.

## Background
Artificial intelligence has made significant progress in recent years.
Machine learning models can now perform complex tasks like natural language processing,
computer vision, and decision making.

## Methodology
Our research uses a novel approach combining traditional methods with modern AI techniques.
We collected data from various sources and processed it using state-of-the-art algorithms.

## Results
The results show promising improvements over baseline methods.
Our system achieved 95% accuracy on the test dataset.

## Conclusion
This research demonstrates the effectiveness of combining AI with domain expertise.
Future work will explore additional applications and optimizations.
"""

    test_file_path.write_text(test_content)
    print(f"   Created test file: {test_file_path}")

    # Test file loading
    from backend.agents.specialized.agent_d.nodes import load_file_node

    initial_state = {
        "query": f"load {test_file_path} into test_research_papers",
        "user_id": TEST_USER_ID,
        "thread_id": TEST_THREAD_ID,
        "conversation_context": {},
        "action_type": "load_file",
        "action_params": {},
        "collection_name": "test_research_papers",
        "collection_id": None,
        "collection_list": None,
        "file_path": str(test_file_path),
        "raw_content": None,
        "chunks": None,
        "search_results": None,
        "final_response": None,
        "error": None,
        "current_step": "starting",
        "task_callback": None,
    }

    result_state = await load_file_node(initial_state)

    if result_state.get("error"):
        print(f"✗ Failed to load file: {result_state['error']}")
        return False

    print(f"✓ File loaded successfully")
    print(f"   Content length: {len(result_state['raw_content'])} characters")

    # Test chunking
    from backend.agents.specialized.agent_d.nodes import chunk_and_embed_node

    result_state = await chunk_and_embed_node(result_state)

    if result_state.get("error"):
        print(f"✗ Failed to chunk: {result_state['error']}")
        return False

    print(f"✓ Document chunked successfully")
    print(f"   Number of chunks: {len(result_state['chunks'])}")

    # Test storing chunks
    from backend.agents.specialized.agent_d.nodes import store_chunks_node

    result_state = await store_chunks_node(result_state)

    if result_state.get("error"):
        print(f"✗ Failed to store chunks: {result_state['error']}")
        return False

    print(f"✓ {result_state['final_response']}\n")
    return True


async def test_search_collection():
    """Test 4: Search within collection"""
    print("🔍 Test 4: Searching collection...")

    from backend.agents.specialized.agent_d.nodes import search_collection_node

    initial_state = {
        "query": "search test_research_papers for artificial intelligence",
        "user_id": TEST_USER_ID,
        "thread_id": TEST_THREAD_ID,
        "conversation_context": {},
        "action_type": "search_collection",
        "action_params": {"query": "artificial intelligence machine learning"},
        "collection_name": "test_research_papers",
        "collection_id": None,
        "collection_list": None,
        "file_path": None,
        "raw_content": None,
        "chunks": None,
        "search_results": None,
        "final_response": None,
        "error": None,
        "current_step": "starting",
        "task_callback": None,
    }

    result_state = await search_collection_node(initial_state)

    if result_state.get("error"):
        print(f"✗ Failed: {result_state['error']}")
        return False

    print(f"✓ Search completed")
    print(f"{result_state['final_response']}\n")
    return True


async def test_search_all_collections():
    """Test 5: Search across all collections"""
    print("🔍 Test 5: Searching all collections...")

    from backend.agents.specialized.agent_d.nodes import search_all_node

    initial_state = {
        "query": "search all for methodology research",
        "user_id": TEST_USER_ID,
        "thread_id": TEST_THREAD_ID,
        "conversation_context": {},
        "action_type": "search_all",
        "action_params": {"query": "methodology research results"},
        "collection_name": None,
        "collection_id": None,
        "collection_list": None,
        "file_path": None,
        "raw_content": None,
        "chunks": None,
        "search_results": None,
        "final_response": None,
        "error": None,
        "current_step": "starting",
        "task_callback": None,
    }

    result_state = await search_all_node(initial_state)

    if result_state.get("error"):
        print(f"✗ Failed: {result_state['error']}")
        return False

    print(f"✓ Search completed")
    print(f"{result_state['final_response']}\n")
    return True


async def test_delete_collection():
    """Test 6: Delete collection"""
    print("🗑️  Test 6: Deleting test collection...")

    from backend.agents.specialized.agent_d.nodes import delete_collection_node

    initial_state = {
        "query": "delete collection test_research_papers",
        "user_id": TEST_USER_ID,
        "thread_id": TEST_THREAD_ID,
        "conversation_context": {},
        "action_type": "delete_collection",
        "action_params": {},
        "collection_name": "test_research_papers",
        "collection_id": None,
        "collection_list": None,
        "file_path": None,
        "raw_content": None,
        "chunks": None,
        "search_results": None,
        "final_response": None,
        "error": None,
        "current_step": "starting",
        "task_callback": None,
    }

    result_state = await delete_collection_node(initial_state)

    if result_state.get("error"):
        print(f"✗ Failed: {result_state['error']}")
        return False

    print(f"✓ {result_state['final_response']}\n")
    return True


async def main():
    """Run all tests"""
    print("=" * 60)
    print("DocumentManager Agent (Alice) - Test Suite")
    print("=" * 60)
    print()

    try:
        # Cleanup first
        await cleanup_test_collections()

        # Run tests
        results = []

        results.append(("Create Collection", await test_create_collection()))
        results.append(("List Collections", await test_list_collections()))
        results.append(("Load Document", await test_load_document()))
        results.append(("Search Collection", await test_search_collection()))
        results.append(("Search All Collections", await test_search_all_collections()))
        results.append(("Delete Collection", await test_delete_collection()))

        # Summary
        print("=" * 60)
        print("Test Summary")
        print("=" * 60)

        passed = sum(1 for _, result in results if result)
        total = len(results)

        for test_name, result in results:
            status = "✓ PASS" if result else "✗ FAIL"
            print(f"{status}: {test_name}")

        print()
        print(f"Results: {passed}/{total} tests passed")

        if passed == total:
            print("🎉 All tests passed!")
            return 0
        else:
            print("⚠️  Some tests failed")
            return 1

    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
