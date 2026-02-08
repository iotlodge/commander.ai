"""
DocumentManager Agent (Alice) - LangGraph Implementation
Manages document collections and semantic search
"""

from langgraph.graph import StateGraph, END

from backend.agents.base.agent_interface import (
    BaseAgent,
    AgentMetadata,
    AgentExecutionContext,
    AgentExecutionResult,
)
from backend.agents.specialized.agent_d.state import DocumentManagerState
from backend.agents.specialized.agent_d.nodes import (
    parse_input_node,
    llm_reasoning_node,
    create_collection_node,
    delete_collection_node,
    list_collections_node,
    load_file_node,
    chunk_and_embed_node,
    store_chunks_node,
    search_collection_node,
    search_multiple_node,
    search_all_node,
    fetch_web_node,
    crawl_site_node,
    extract_urls_node,
    map_site_node,
    process_web_documents_node,
    finalize_response_node,
    route_action,
)


class DocumentManagerAgent(BaseAgent):
    """
    Document Manager Agent (Alice)

    Responsibilities:
    - Load documents from local files (.pdf, .docx, .md, .txt)
    - Search web content using Tavily API with cache-first pattern
    - Crawl websites and extract content from URLs
    - Map website structure
    - Chunk and embed content for semantic search
    - Manage user-scoped document collections
    - Perform semantic search within collections or across all collections
    - Collection lifecycle management (create, delete, list)
    """

    def __init__(self):
        metadata = AgentMetadata(
            id="agent_d",
            nickname="alice",
            specialization="Document Management",
            description="Manages documents, collections, and semantic search",
            avatar_url=None,
        )
        super().__init__(metadata)

    def create_graph(self) -> StateGraph:
        """
        Build the document management workflow graph

        Graph Flow:
        parse_input → route_action → [
            llm_reasoning → route_action (if no pattern match)
            load_file → chunk_and_embed → store_chunks → finalize
            search_web → process_web_documents → store_chunks → finalize
            crawl_site → process_web_documents → store_chunks → finalize
            extract_urls → process_web_documents → store_chunks → finalize
            map_site → finalize
            search_collection → finalize
            search_all → finalize
            create_collection → finalize
            delete_collection → finalize
            list_collections → finalize
        ] → END

        NEW: llm_reasoning node uses LLM to understand intent for queries
        that don't match hardcoded patterns (e.g., "check for deprecated models")
        """
        graph = StateGraph(DocumentManagerState)

        # Add all nodes
        graph.add_node("parse_input", parse_input_node)
        graph.add_node("llm_reasoning", llm_reasoning_node)
        graph.add_node("create_collection", create_collection_node)
        graph.add_node("delete_collection", delete_collection_node)
        graph.add_node("list_collections", list_collections_node)
        graph.add_node("load_file", load_file_node)
        graph.add_node("chunk_and_embed", chunk_and_embed_node)
        graph.add_node("store_chunks", store_chunks_node)
        graph.add_node("search_collection", search_collection_node)
        graph.add_node("search_multiple", search_multiple_node)
        graph.add_node("search_all", search_all_node)
        graph.add_node("search_web", fetch_web_node)
        graph.add_node("crawl_site", crawl_site_node)
        graph.add_node("extract_urls", extract_urls_node)
        graph.add_node("map_site", map_site_node)
        graph.add_node("process_web_documents", process_web_documents_node)
        graph.add_node("finalize_response", finalize_response_node)

        # Set entry point
        graph.set_entry_point("parse_input")

        # Add conditional routing from parse_input
        graph.add_conditional_edges(
            "parse_input",
            route_action,
            {
                "load_file": "load_file",
                "search_web": "search_web",
                "crawl_site": "crawl_site",
                "extract_urls": "extract_urls",
                "map_site": "map_site",
                "create_collection": "create_collection",
                "delete_collection": "delete_collection",
                "list_collections": "list_collections",
                "search_collection": "search_collection",
                "search_multiple": "search_multiple",
                "search_all": "search_all",
                "llm_reasoning": "llm_reasoning",  # NEW: Route to LLM reasoning
            },
        )

        # Add conditional routing from llm_reasoning (re-routes based on LLM decision)
        graph.add_conditional_edges(
            "llm_reasoning",
            route_action,
            {
                "load_file": "load_file",
                "search_web": "search_web",
                "crawl_site": "crawl_site",
                "extract_urls": "extract_urls",
                "map_site": "map_site",
                "create_collection": "create_collection",
                "delete_collection": "delete_collection",
                "list_collections": "list_collections",
                "search_collection": "search_collection",
                "search_multiple": "search_multiple",
                "search_all": "search_all",
            },
        )

        # File loading workflow
        graph.add_edge("load_file", "chunk_and_embed")
        graph.add_edge("chunk_and_embed", "store_chunks")
        graph.add_edge("store_chunks", "finalize_response")

        # Web search workflows
        graph.add_edge("search_web", "process_web_documents")
        graph.add_edge("crawl_site", "process_web_documents")
        graph.add_edge("extract_urls", "process_web_documents")
        graph.add_edge("process_web_documents", "store_chunks")

        # Map site workflow (no storage, just response)
        graph.add_edge("map_site", "finalize_response")

        # Collection management workflows
        graph.add_edge("create_collection", "finalize_response")
        graph.add_edge("delete_collection", "finalize_response")
        graph.add_edge("list_collections", "finalize_response")

        # Search workflows
        graph.add_edge("search_collection", "finalize_response")
        graph.add_edge("search_multiple", "finalize_response")
        graph.add_edge("search_all", "finalize_response")

        # All paths end at finalize_response
        graph.add_edge("finalize_response", END)

        # Compile graph without checkpointer (stateless agent)
        return graph.compile(checkpointer=None)

    async def _execute_graph(
        self,
        command: str,
        context: AgentExecutionContext,
    ) -> AgentExecutionResult:
        """Execute DocumentManager graph"""
        initial_state: DocumentManagerState = {
            "query": command,
            "user_id": context.user_id,
            "thread_id": context.thread_id,
            "conversation_context": (
                context.conversation_context.model_dump()
                if context.conversation_context
                else {}
            ),
            "action_type": "",
            "action_params": {},
            "collection_id": None,
            "collection_name": None,
            "collection_list": None,
            "file_path": None,
            "raw_content": None,
            "chunks": None,
            "search_query": None,
            "web_documents": None,
            "search_results": None,
            "final_response": None,
            "error": None,
            "current_step": "starting",
            "task_callback": context.task_callback,
            "model_config": self.model_config,
            "metrics": context.metrics,
        }

        # Build config with execution tracker callbacks
        config = self._build_graph_config(context)

        try:
            final_state = await self.graph.ainvoke(initial_state, config)

            if not final_state:
                return AgentExecutionResult(
                    success=False,
                    response="",
                    error="Graph returned empty state",
                    final_state={},
                )

            success = final_state.get("error") is None
            response = final_state.get("final_response", "Task completed")
            error = final_state.get("error")

            return AgentExecutionResult(
                success=success,
                response=response,
                final_state=final_state,
                error=error,
                metadata={
                    "action_type": final_state.get("action_type"),
                    "collection_name": final_state.get("collection_name"),
                },
            )

        except Exception as e:
            import traceback

            error_details = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
            return AgentExecutionResult(
                success=False,
                response="",
                error=f"Document management failed: {error_details}",
            )
