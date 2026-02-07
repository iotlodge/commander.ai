"""
Graph nodes for DocumentManager agent
"""

import os
from pathlib import Path
from uuid import uuid4

from backend.agents.specialized.agent_d.state import DocumentManagerState
from backend.core.config import get_settings
from backend.core.dependencies import get_document_store
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
from backend.tools.web_search.tavily_toolset import TavilyToolset
from backend.core.llm_factory import create_llm, DEFAULT_CONFIGS


async def _format_model_deprecation_report(state: DocumentManagerState) -> str:
    """
    Analyze web search results for model deprecation info and create formatted report
    Compares against user's configured models
    """
    web_documents = state.get("web_documents", [])
    query = state.get("query", "").lower()

    if not web_documents:
        return "No information found about model deprecation."

    # Extract model information from web results
    deprecated_models = []
    model_info = {}

    # Common model patterns
    model_patterns = [
        r'gpt-4[-\w]*',
        r'gpt-3\.5[-\w]*',
        r'claude[-\s]?(?:3\.5|3|2\.1|2\.0|2|1)',
        r'claude[-\s]?(?:opus|sonnet|haiku)[-\s]?[\d.]*',
        r'text-davinci[-\w]*',
        r'text-curie[-\w]*',
    ]

    import re
    for doc in web_documents:
        content = doc.get("content", "")
        title = doc.get("metadata", {}).get("title", "")
        url = doc.get("metadata", {}).get("url", "")

        # Look for deprecation mentions
        for pattern in model_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                model_name = match.group(0).strip()
                # Check context for deprecation keywords
                context_start = max(0, match.start() - 100)
                context_end = min(len(content), match.end() + 100)
                context = content[context_start:context_end].lower()

                if any(keyword in context for keyword in ['deprecat', 'sunset', 'discontinu', 'retired', 'end of life', 'eol']):
                    if model_name not in model_info:
                        model_info[model_name] = {
                            "deprecated": True,
                            "sources": []
                        }
                    model_info[model_name]["sources"].append({"title": title, "url": url})

    # Query database for user's configured models
    configured_models = {}
    try:
        session_factory = get_session_factory()
        async with session_factory() as session:
            from backend.repositories.agent_model_repository import AgentModelRepository
            model_repo = AgentModelRepository(session)
            configs = await model_repo.list_model_configs(user_id=state["user_id"])

            for config in configs:
                agent_id = config.agent_id
                model_key = f"{config.provider}_{config.model_name}"
                configured_models[agent_id] = {
                    "provider": config.provider,
                    "model_name": config.model_name,
                    "model_key": model_key,
                    "temperature": config.temperature,
                    "enabled": config.enabled,
                }
    except Exception as e:
        print(f"[Alice] Could not fetch configured models: {e}")

    # Build formatted report
    report = []
    report.append("# 🔍 LLM Model Deprecation Analysis Report\n")
    report.append(f"**Query:** {state.get('search_query', query)}")
    report.append(f"**Generated:** {__import__('datetime').datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}\n")

    # Section 1: Deprecated Models Found
    if model_info:
        report.append("## 📊 Deprecated Models Detected\n")
        report.append("| Model | Status | Sources |")
        report.append("|-------|--------|---------|")

        for model_name, info in sorted(model_info.items()):
            sources_text = ", ".join([f"[{s['title'][:30]}...]({s['url']})" for s in info['sources'][:2]])
            report.append(f"| `{model_name}` | ⚠️ Deprecated | {sources_text} |")

        report.append("")
    else:
        report.append("## ✅ No Deprecated Models Found\n")
        report.append("Web search did not identify any specific deprecated models in the results.\n")

    # Section 2: Your Active Models
    if configured_models:
        report.append("## 🤖 Your Currently Configured Models\n")
        report.append("| Agent | Provider | Model | Status |")
        report.append("|-------|----------|-------|--------|")

        for agent_id, config in configured_models.items():
            model_full = f"{config['provider']}_{config['model_name']}"
            # Check if model appears in deprecated list
            is_deprecated = any(
                model_full.lower().replace('_', '-') in model_name.lower().replace('_', '-')
                or model_name.lower().replace('_', '-') in model_full.lower().replace('_', '-')
                for model_name in model_info.keys()
            )

            status = "⚠️ AT RISK" if is_deprecated else "✅ Active"
            emoji = "⚠️" if is_deprecated else "✅"

            report.append(
                f"| `{agent_id}` | {config['provider'].title()} | `{config['model_name']}` | {status} |"
            )

        report.append("")

    # Section 3: Recommendations
    report.append("## 💡 Recommendations\n")

    at_risk_count = sum(
        1 for agent_id, config in configured_models.items()
        if any(
            f"{config['provider']}_{config['model_name']}".lower().replace('_', '-') in model_name.lower().replace('_', '-')
            for model_name in model_info.keys()
        )
    )

    if at_risk_count > 0:
        report.append(f"⚠️ **{at_risk_count} agent(s) using potentially deprecated models**\n")
        report.append("**Suggested Actions:**")
        report.append("1. Review deprecated models and plan migration")
        report.append("2. Test replacement models (GPT-4o, Claude Sonnet 4)")
        report.append("3. Update agent configs via Mission Control (🧠 Cpu icon)")
        report.append("4. Monitor for deprecation timelines\n")
    else:
        report.append("✅ **All your configured models appear to be current**\n")
        report.append("Continue monitoring for future deprecation notices.\n")

    # Section 4: Summary
    report.append("## 📝 Executive Summary\n")

    summary_parts = []
    if model_info:
        summary_parts.append(f"Found {len(model_info)} deprecated model(s) mentioned in search results")
    else:
        summary_parts.append("No specific deprecated models identified in current search")

    if configured_models:
        summary_parts.append(f"You have {len(configured_models)} agent(s) configured with specific models")
        if at_risk_count > 0:
            summary_parts.append(f"**{at_risk_count} may need attention**")

    report.append(". ".join(summary_parts) + ".")
    report.append("\n---\n")

    # Section 5: Raw Sources
    report.append("## 📚 Sources Referenced\n")
    for idx, doc in enumerate(web_documents[:5], 1):
        title = doc.get("metadata", {}).get("title", "Untitled")
        url = doc.get("metadata", {}).get("url", "")
        report.append(f"{idx}. [{title}]({url})")

    return "\n".join(report)


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

    elif "crawl" in query_lower or "crawl site" in query_lower or "crawl website" in query_lower:
        action_type = "crawl_site"
        # Extract URL
        url_match = re.search(r'https?://[^\s]+', query)
        base_url = url_match.group(0) if url_match else None
        params = {
            "base_url": base_url,
            "collection_name": collection_name,
        }

    elif "extract" in query_lower and ("url" in query_lower or "http" in query):
        action_type = "extract_urls"
        # Extract all URLs from query
        urls = re.findall(r'https?://[^\s]+', query)
        params = {
            "urls": urls,
            "collection_name": collection_name,
        }

    elif "map site" in query_lower or "map website" in query_lower:
        action_type = "map_site"
        # Extract URL
        url_match = re.search(r'https?://[^\s]+', query)
        base_url = url_match.group(0) if url_match else None
        params = {
            "base_url": base_url,
        }

    elif "search web" in query_lower or "web search" in query_lower or "search online" in query_lower:
        action_type = "search_web"
        # Extract search query (everything after "for" or quoted string)
        search_query = query
        for_match = re.search(r'(?:for|about)\s+(.+?)(?:\s+(?:into|in)\s+|$)', query, re.IGNORECASE)
        if for_match:
            search_query = for_match.group(1).strip('"').strip("'")
        elif quoted_strings:
            search_query = quoted_strings[0]

        # Check if storing into collection
        store_match = re.search(r'(?:into|in)\s+([a-zA-Z0-9_-]+)', query_lower)
        store_collection = store_match.group(1) if store_match else None

        params = {
            "query": search_query,
            "collection_name": store_collection,
        }

    elif "search" in query_lower:
        # Determine search type based on query structure
        search_query = query
        target_collections = None
        target_collection = None

        # Pattern 1: "search for <query> in [collection1, collection2]" - Multiple collections
        multi_collection_match = re.search(r'search\s+for\s+(.+?)\s+in\s+\[([^\]]+)\]', query, re.IGNORECASE)
        if multi_collection_match:
            action_type = "search_multiple"
            search_query = multi_collection_match.group(1).strip('"').strip("'")
            collections_str = multi_collection_match.group(2)
            target_collections = [c.strip() for c in collections_str.split(',')]
            params = {
                "query": search_query,
                "collection_names": target_collections,
            }

        # Pattern 2: "search for <query> in/into <collection>" - Single collection
        elif re.search(r'search\s+for\s+.+?\s+(?:in|into)\s+[a-zA-Z0-9_-]+', query_lower):
            action_type = "search_collection"
            search_for_into = re.search(r'search\s+for\s+(.+?)\s+(?:in|into)\s+([a-zA-Z0-9_-]+)', query_lower)
            if search_for_into:
                search_query = search_for_into.group(1).strip('"').strip("'")
                target_collection = search_for_into.group(2)
            params = {
                "query": search_query,
                "collection_name": target_collection,
            }

        # Pattern 3: "search for <query>" (no collection specified) - Search ALL collections
        elif re.match(r'search\s+for\s+', query_lower):
            action_type = "search_all"
            for_match = re.search(r'search\s+for\s+(.+)$', query, re.IGNORECASE)
            if for_match:
                search_query = for_match.group(1).strip('"').strip("'")
            elif quoted_strings:
                search_query = quoted_strings[0]
            params = {"query": search_query}

        # Pattern 4: "search <collection> for <query>" - Single collection (original syntax)
        else:
            action_type = "search_collection"
            for_match = re.search(r'for\s+(.+)$', query, re.IGNORECASE)
            if for_match:
                search_query = for_match.group(1).strip('"').strip("'")
            elif quoted_strings:
                search_query = quoted_strings[0]
            target_collection = collection_name
            params = {
                "query": search_query,
                "collection_name": target_collection,
            }

    else:
        # No hardcoded pattern matched - use LLM reasoning
        action_type = "needs_reasoning"
        params = {"original_query": query}

    return {
        "action_type": action_type,
        "action_params": params,
        "collection_name": params.get("collection_name"),
        "file_path": params.get("file_path"),
        "current_step": "parse_input",
    }


async def llm_reasoning_node(state: DocumentManagerState) -> dict:
    """
    Use LLM to understand user intent and decide what action to take
    Handles queries that don't match hardcoded patterns

    Enhanced with:
    - Full action set (10+ actions)
    - Context awareness (user's collections)
    - Confidence scoring
    - Better examples and decision logic
    """
    query = state["action_params"].get("original_query", state["query"])

    # Get user's collections for context awareness
    user_collections = []
    try:
        session_factory = get_session_factory()
        async with session_factory() as session:
            from backend.repositories.collection_repository import CollectionRepository
            collection_repo = CollectionRepository(session)
            collections = await collection_repo.list_user_collections(user_id=state["user_id"])
            user_collections = [c.collection_name for c in collections]
    except Exception:
        pass  # Continue without collection context if fetch fails

    collections_context = f"User's existing collections: {', '.join(user_collections)}" if user_collections else "User has no collections yet."

    # Create LLM instance
    model_config = state.get("model_config") or DEFAULT_CONFIGS.get("agent_d")
    llm = create_llm(model_config, temperature=0.0)

    # Enhanced prompt with full action set and context
    reasoning_prompt = f"""You are Alice, an expert Document Manager and Information Retrieval agent. Analyze the user's request and decide the best action.

User Request: "{query}"

Context:
{collections_context}

Available Actions (choose the MOST appropriate):
1. "web_search" - Search internet for current/real-time information (use when user needs latest data, news, or information not in their collections)
2. "search_collection" - Search within a SPECIFIC collection by name (use when user mentions a collection name)
3. "search_multiple" - Search across MULTIPLE specific collections (use when user lists collections)
4. "search_all" - Search across ALL user's document collections (use when user wants to find info in their docs but doesn't specify which)
5. "create_collection" - Create a new document collection (use when user wants to organize or save documents)
6. "delete_collection" - Delete a collection (use when user wants to remove a collection)
7. "list_collections" - Show all collections (use when user asks "what do I have?", "show my collections")
8. "load_file" - Load a document from file path (use when user provides a file path like /path/to/file.pdf)
9. "crawl_site" - Crawl and index a website (use when user wants to save/archive a website)
10. "extract_urls" - Extract content from specific URLs (use when user provides specific URLs to process)
11. "map_site" - Map website structure without storing (use when user wants to see site structure)

Decision Criteria:
- If request mentions "latest", "current", "news", "today", "2026", or needs real-time info → web_search
- If request mentions existing collection name → search_collection
- If request is about user's documents/collections without specifics → search_all
- If request wants to save/archive web content → crawl_site or create_collection
- If request has file path (.pdf, .docx, .txt, .md) → load_file
- If user asks what they have → list_collections

Respond with ONLY a JSON object (no markdown, no explanation):
{{
  "action": "<action_name>",
  "confidence": 0.0-1.0,
  "reasoning": "why this action",
  "params": {{
    "query": "search query if needed",
    "collection_name": "collection name if applicable",
    "file_path": "file path if applicable",
    "url": "URL if applicable"
  }}
}}

Examples:
- "check for deprecated LLM models" → {{"action": "web_search", "confidence": 0.95, "reasoning": "Needs current model status from web", "params": {{"query": "deprecated LLM models OpenAI Anthropic Claude GPT 2026"}}}}
- "find documents about quantum computing" → {{"action": "search_all", "confidence": 0.90, "reasoning": "Search user's document collections", "params": {{"query": "quantum computing"}}}}
- "search my research collection for AI papers" → {{"action": "search_collection", "confidence": 0.95, "reasoning": "User specified 'research' collection", "params": {{"query": "AI papers", "collection_name": "research"}}}}
- "what collections do I have?" → {{"action": "list_collections", "confidence": 1.0, "reasoning": "User wants to see their collections", "params": {{}}}}
- "save TechCrunch articles about AI" → {{"action": "crawl_site", "confidence": 0.85, "reasoning": "User wants to archive website content", "params": {{"url": "techcrunch.com", "collection_name": "ai_news"}}}}
- "load /documents/research.pdf" → {{"action": "load_file", "confidence": 1.0, "reasoning": "User provided file path", "params": {{"file_path": "/documents/research.pdf"}}}}

Analyze and respond:"""

    try:
        response = await llm.ainvoke(reasoning_prompt)
        response_text = response.content.strip()

        # Parse JSON response
        import json
        # Remove markdown code blocks if present
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        response_text = response_text.strip()

        decision = json.loads(response_text)
        action = decision.get("action", "list_collections")
        confidence = decision.get("confidence", 0.5)
        params = decision.get("params", {})
        reasoning = decision.get("reasoning", "")

        # Log decision for debugging
        print(f"[Alice LLM Decision] Action: {action}, Confidence: {confidence}, Reasoning: {reasoning}")

        # Map LLM decision to action_type with enhanced parameter extraction
        if action == "web_search":
            search_query = params.get("query", query)
            return {
                "action_type": "search_web",
                "action_params": {
                    "query": search_query,
                    "collection_name": None,  # Don't store by default
                },
                "collection_name": None,
                "search_query": search_query,
                "current_step": "llm_reasoning",
                "reasoning": reasoning,
                "confidence": confidence,
            }

        elif action == "search_collection":
            search_query = params.get("query", query)
            collection_name = params.get("collection_name")
            return {
                "action_type": "search_collection",
                "action_params": {
                    "query": search_query,
                    "collection_name": collection_name,
                },
                "collection_name": collection_name,
                "search_query": search_query,
                "current_step": "llm_reasoning",
                "reasoning": reasoning,
                "confidence": confidence,
            }

        elif action == "search_multiple":
            search_query = params.get("query", query)
            collection_names = params.get("collection_names", [])
            return {
                "action_type": "search_multiple",
                "action_params": {
                    "query": search_query,
                    "collection_names": collection_names,
                },
                "search_query": search_query,
                "current_step": "llm_reasoning",
                "reasoning": reasoning,
                "confidence": confidence,
            }

        elif action == "search_all":
            search_query = params.get("query", query)
            return {
                "action_type": "search_all",
                "action_params": {"query": search_query},
                "search_query": search_query,
                "current_step": "llm_reasoning",
                "reasoning": reasoning,
                "confidence": confidence,
            }

        elif action == "create_collection":
            collection_name = params.get("collection_name", "new_collection")
            return {
                "action_type": "create_collection",
                "action_params": {"collection_name": collection_name},
                "collection_name": collection_name,
                "current_step": "llm_reasoning",
                "reasoning": reasoning,
                "confidence": confidence,
            }

        elif action == "delete_collection":
            collection_name = params.get("collection_name")
            return {
                "action_type": "delete_collection",
                "action_params": {"collection_name": collection_name},
                "collection_name": collection_name,
                "current_step": "llm_reasoning",
                "reasoning": reasoning,
                "confidence": confidence,
            }

        elif action == "load_file":
            file_path = params.get("file_path")
            collection_name = params.get("collection_name", "default")
            return {
                "action_type": "load_file",
                "action_params": {
                    "file_path": file_path,
                    "collection_name": collection_name,
                },
                "file_path": file_path,
                "collection_name": collection_name,
                "current_step": "llm_reasoning",
                "reasoning": reasoning,
                "confidence": confidence,
            }

        elif action == "crawl_site":
            url = params.get("url")
            collection_name = params.get("collection_name")
            return {
                "action_type": "crawl_site",
                "action_params": {
                    "base_url": url,
                    "collection_name": collection_name,
                },
                "current_step": "llm_reasoning",
                "reasoning": reasoning,
                "confidence": confidence,
            }

        elif action == "extract_urls":
            urls = params.get("urls", [])
            collection_name = params.get("collection_name")
            return {
                "action_type": "extract_urls",
                "action_params": {
                    "urls": urls,
                    "collection_name": collection_name,
                },
                "current_step": "llm_reasoning",
                "reasoning": reasoning,
                "confidence": confidence,
            }

        elif action == "map_site":
            url = params.get("url")
            return {
                "action_type": "map_site",
                "action_params": {"base_url": url},
                "current_step": "llm_reasoning",
                "reasoning": reasoning,
                "confidence": confidence,
            }

        else:  # list_collections or fallback
            return {
                "action_type": "list_collections",
                "action_params": {},
                "current_step": "llm_reasoning",
                "reasoning": reasoning,
                "confidence": confidence,
            }

    except Exception as e:
        # Fallback to web search if LLM reasoning fails
        print(f"[Alice LLM Error] {str(e)}")
        return {
            "action_type": "search_web",
            "action_params": {
                "query": query,
                "collection_name": None,
            },
            "search_query": query,
            "current_step": "llm_reasoning",
            "error": f"LLM reasoning failed: {str(e)}, falling back to web search",
            "confidence": 0.0,
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

            # Create Qdrant collection using singleton
            doc_store = await get_document_store()
            await doc_store.create_collection(
                qdrant_collection_name=collection.qdrant_collection_name,
                user_id=state["user_id"],
            )
            # Note: Do not disconnect singleton - shared across all agents

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

            # Delete from Qdrant using singleton
            doc_store = await get_document_store()
            await doc_store.delete_collection(collection.qdrant_collection_name)

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
                    **state,
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
                **state,
                "collection_list": collection_list,
                "final_response": "\n".join(response_lines),
                "current_step": "list_collections",
            }

    except Exception as e:
        return {
            **state,
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
                **state,
                "error": "No file path provided",
                "final_response": "Please provide a file path to load.",
                "current_step": "load_file",
            }

        # Check if file exists
        if not os.path.exists(file_path):
            return {
                **state,
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
                **state,
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
            **state,
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
                **state,
                "error": "No content to chunk",
                "current_step": "chunk_and_embed",
            }

        file_path = state.get("file_path", "")
        # For web searches, use search query as file name
        search_query = state.get("search_query", "")
        if search_query:
            file_name = f"web_search_{search_query[:50]}"  # Truncate long queries
        else:
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
            **state,
            "error": str(e),
            "final_response": f"Failed to chunk document: {str(e)}",
            "current_step": "chunk_and_embed",
        }


async def store_chunks_node(state: DocumentManagerState) -> dict:
    """Store chunks in collection (or skip if no collection specified)"""
    try:
        chunks = state.get("chunks")
        if not chunks:
            return {
                **state,
                "error": "No chunks to store",
                "final_response": "Failed to store chunks: No chunks generated from document",
                "current_step": "store_chunks",
            }

        # Check if we should store or just return results
        collection_name = state.get("collection_name") or state["action_params"].get("collection_name")

        # If no collection specified (None), skip storage and return web results directly
        if collection_name is None:
            # Check if this is a model-related query for intelligent formatting
            query = state.get("query", "").lower()
            search_query = state.get("search_query", "").lower()
            web_documents = state.get("web_documents", [])

            is_model_query = any(
                keyword in query or keyword in search_query
                for keyword in ['model', 'deprecated', 'llm', 'gpt', 'claude', 'deprecation', 'sunset']
            )

            if is_model_query and web_documents:
                # Generate formatted model deprecation report
                final_response = await _format_model_deprecation_report(state)
            else:
                # Standard formatting for non-model queries
                if web_documents:
                    response_parts = []
                    for idx, doc in enumerate(web_documents, 1):
                        title = doc.get("metadata", {}).get("title", "Untitled")
                        url = doc.get("metadata", {}).get("url", "")
                        content_preview = doc.get("content", "")[:500]  # First 500 chars
                        response_parts.append(f"{idx}. **{title}**\n   URL: {url}\n   {content_preview}...")

                    final_response = "Web search results:\n\n" + "\n\n".join(response_parts)
                else:
                    final_response = "Retrieved information but no results to display."

            return {
                **state,
                "final_response": final_response,
                "current_step": "store_chunks_skipped",
            }

        # Collection specified - proceed with storage
        file_path = (
            state.get("file_path") or
            state["action_params"].get("file_path") or
            ""
        )
        # For web searches, use search query as file name
        search_query = state.get("search_query", "")
        if search_query:
            file_name = f"web_search_{search_query[:50]}"  # Truncate long queries
        else:
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

                # Create Qdrant collection using singleton
                doc_store = await get_document_store()
                await doc_store.create_collection(
                    qdrant_collection_name=collection.qdrant_collection_name,
                    user_id=state["user_id"],
                )
                # Note: Do not disconnect singleton - shared across all agents

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

            # Store embeddings in Qdrant using singleton
            doc_store = await get_document_store()
            await doc_store.store_chunks(
                qdrant_collection_name=collection.qdrant_collection_name,
                chunks=chunk_creates,
            )
            # Note: Do not disconnect singleton - shared across all agents

            # Update collection chunk count
            await collection_repo.increment_chunk_count(
                collection_id=collection.id, increment=len(chunk_creates)
            )

            # TODO: Add image generation capability for complex results
            # Use image_generate_analyze_upscale.py to create visualizations when:
            # - Showing knowledge graph from web search results
            # - Visualizing document relationships in collection
            # - Creating mind maps of semantic connections
            # - Illustrating topic clusters from search results
            # Example: python image_generate_analyze_upscale.py generate \
            #   --prompt "Knowledge graph showing connections between these research topics: [topic1, topic2, topic3]" \
            #   --output output/knowledge_graph.png

            # Format final response with search results if available
            base_message = f"✓ Loaded '{file_name}' into collection '{collection_name}' ({len(chunk_creates)} chunks)."

            # If this was a web search, include formatted results
            web_documents = state.get("web_documents", [])
            if web_documents:
                results_summary = "\n\n**Search Results:**\n"
                for idx, doc in enumerate(web_documents[:5], 1):  # Show top 5
                    metadata = doc.get("metadata", {})
                    title = metadata.get("title", "No title")
                    url = metadata.get("url", "")
                    score = metadata.get("score", 0.0)
                    results_summary += f"\n{idx}. **{title}**"
                    if score:
                        results_summary += f" (relevance: {score:.2f})"
                    results_summary += f"\n   {url}\n"

                if len(web_documents) > 5:
                    results_summary += f"\n_...and {len(web_documents) - 5} more results_"

                final_response = base_message + results_summary
            else:
                final_response = base_message

            return {
                **state,
                "collection_id": str(collection.id),
                "final_response": final_response,
                "current_step": "store_chunks",
            }

    except Exception as e:
        return {
            **state,
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

            # Search in Qdrant using singleton
            doc_store = await get_document_store()
            vector_results = await doc_store.search_collection(
                qdrant_collection_name=collection.qdrant_collection_name,
                user_id=state["user_id"],
                query=query,
                limit=10,
            )
            # Note: Do not disconnect singleton - shared across all agents

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

            # Search across all collections using singleton
            qdrant_collection_names = [c.qdrant_collection_name for c in collections]

            doc_store = await get_document_store()
            all_results = await doc_store.search_all_collections(
                collection_names=qdrant_collection_names,
                user_id=state["user_id"],
                query=query,
                limit=10,
            )
            # Note: Do not disconnect singleton - shared across all agents

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
                **state,
                "search_results": search_results,
                "final_response": "\n".join(response_lines),
                "current_step": "search_all",
            }

    except Exception as e:
        return {
            **state,
            "error": str(e),
            "final_response": f"Search failed: {str(e)}",
            "current_step": "search_all",
        }


async def search_multiple_node(state: DocumentManagerState) -> dict:
    """Search specific multiple collections"""
    try:
        query = state["action_params"].get("query", state["query"])
        collection_names = state["action_params"].get("collection_names", [])

        if not collection_names:
            return {
                **state,
                "error": "No collections specified",
                "final_response": "Please specify collections to search.",
                "current_step": "search_multiple",
            }

        session_factory = get_session_factory()
        async with session_factory() as session:
            collection_repo = CollectionRepository(session)
            chunk_repo = ChunkRepository(session)

            # Get specified collections
            collections = []
            missing_collections = []
            for name in collection_names:
                collection = await collection_repo.get_collection_by_name(
                    user_id=state["user_id"], collection_name=name
                )
                if collection:
                    collections.append(collection)
                else:
                    missing_collections.append(name)

            if not collections:
                return {
                    **state,
                    "search_results": [],
                    "final_response": f"None of the specified collections exist: {', '.join(collection_names)}",
                    "current_step": "search_multiple",
                }

            # Search across specified collections using singleton
            qdrant_collection_names = [c.qdrant_collection_name for c in collections]

            doc_store = await get_document_store()
            all_results = await doc_store.search_all_collections(
                collection_names=qdrant_collection_names,
                user_id=state["user_id"],
                query=query,
                limit=10,
            )
            # Note: Do not disconnect singleton - shared across all agents

            if not all_results:
                return {
                    **state,
                    "search_results": [],
                    "final_response": f"No results found in {', '.join([c.collection_name for c in collections])} for: {query}",
                    "current_step": "search_multiple",
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
            found_in = ', '.join([c.collection_name for c in collections])
            warning = f"\n(Note: Collections not found: {', '.join(missing_collections)})" if missing_collections else ""
            response_lines = [f"Found {len(search_results)} results in [{found_in}]:{warning}"]
            for idx, result in enumerate(search_results[:5], 1):
                response_lines.append(
                    f"\n{idx}. [{result['collection_name']} / {result['file_name']} - chunk {result['chunk_index']}] (score: {result['score']:.2f})"
                )
                response_lines.append(f"   {result['content'][:200]}...")

            return {
                **state,
                "search_results": search_results,
                "final_response": "\n".join(response_lines),
                "current_step": "search_multiple",
            }

    except Exception as e:
        return {
            **state,
            "error": str(e),
            "final_response": f"Search failed: {str(e)}",
            "current_step": "search_multiple",
        }


async def fetch_web_node(state: DocumentManagerState) -> dict:
    """Fetch web content using Tavily API with cache-first pattern"""
    try:
        search_query = state["action_params"].get("query", state.get("search_query", ""))

        if not search_query:
            return {
                **state,
                "error": "No search query provided",
                "final_response": "Please provide a search query for web search.",
                "current_step": "fetch_web",
            }

        # Get settings and document store
        settings = get_settings()
        doc_store = await get_document_store()

        # Initialize TavilyToolset with cache-first pattern
        tavily = TavilyToolset(
            api_key=settings.tavily_api_key,
            document_store=doc_store,
            enable_caching=True,
        )

        # Search with cache-first pattern
        result = await tavily.search(
            query=search_query,
            user_id=state["user_id"],
            max_results=settings.tavily_max_results,
            use_cache=True,
        )

        if not result.results:
            return {
                **state,
                "web_documents": [],
                "final_response": f"No web results found for: {search_query}",
                "current_step": "fetch_web",
            }

        # Format results for document storage
        web_documents = []
        for idx, search_result in enumerate(result.results):
            # Combine title and content for better context
            content = f"# {search_result['title']}\n\n{search_result['content']}\n\nSource: {search_result['url']}"

            web_documents.append({
                "content": content,
                "metadata": {
                    "source_type": "web",
                    "url": search_result["url"],
                    "title": search_result["title"],
                    "query": search_query,
                    "score": search_result.get("score", 0.0),
                    "result_index": idx,
                    "cache_source": result.source,  # "api" or "cache"
                }
            })

        cache_info = f" (from {result.source})" if result.source == "cache" else ""

        return {
            **state,
            "search_query": search_query,
            "web_documents": web_documents,
            "final_response": f"Found {len(web_documents)} web results{cache_info}",
            "current_step": "fetch_web",
        }

    except Exception as e:
        return {
            **state,
            "error": str(e),
            "final_response": f"Web search failed: {str(e)}",
            "current_step": "fetch_web",
        }


async def crawl_site_node(state: DocumentManagerState) -> dict:
    """Crawl website using Tavily crawl operation"""
    try:
        base_url = state["action_params"].get("base_url")

        if not base_url:
            return {
                **state,
                "error": "No base URL provided",
                "final_response": "Please provide a base URL to crawl.",
                "current_step": "crawl_site",
            }

        # Get settings and document store
        settings = get_settings()
        doc_store = await get_document_store()

        # Initialize TavilyToolset
        tavily = TavilyToolset(
            api_key=settings.tavily_api_key,
            document_store=doc_store,
            enable_caching=True,
        )

        # Crawl website
        result = await tavily.crawl(
            base_url=base_url,
            user_id=state["user_id"],
            max_depth=2,
            max_breadth=20,
            limit=50,
        )

        # Format results for document storage
        web_documents = []
        for idx, page in enumerate(result.results):
            web_documents.append({
                "content": page.get("content", ""),
                "metadata": {
                    "source_type": "web_crawl",
                    "url": page.get("url", ""),
                    "title": page.get("title", ""),
                    "base_url": base_url,
                    "result_index": idx,
                }
            })

        return {
            **state,
            "web_documents": web_documents,
            "final_response": f"Crawled {len(web_documents)} pages from {base_url}",
            "current_step": "crawl_site",
        }

    except Exception as e:
        return {
            **state,
            "error": str(e),
            "final_response": f"Website crawl failed: {str(e)}",
            "current_step": "crawl_site",
        }


async def extract_urls_node(state: DocumentManagerState) -> dict:
    """Extract content from specific URLs using Tavily extract operation"""
    try:
        urls = state["action_params"].get("urls", [])

        if not urls:
            return {
                **state,
                "error": "No URLs provided",
                "final_response": "Please provide URLs to extract content from.",
                "current_step": "extract_urls",
            }

        # Get settings and document store
        settings = get_settings()
        doc_store = await get_document_store()

        # Initialize TavilyToolset
        tavily = TavilyToolset(
            api_key=settings.tavily_api_key,
            document_store=doc_store,
            enable_caching=True,
        )

        # Extract content from URLs
        results = await tavily.extract(
            urls=urls,
            user_id=state["user_id"],
            extract_depth="advanced",
        )

        # Format results for document storage
        web_documents = []
        for idx, extracted in enumerate(results):
            web_documents.append({
                "content": extracted.content,
                "metadata": {
                    "source_type": "web_extract",
                    "url": extracted.url,
                    "title": extracted.title,
                    "result_index": idx,
                }
            })

        return {
            **state,
            "web_documents": web_documents,
            "final_response": f"Extracted content from {len(web_documents)} URLs",
            "current_step": "extract_urls",
        }

    except Exception as e:
        return {
            **state,
            "error": str(e),
            "final_response": f"URL extraction failed: {str(e)}",
            "current_step": "extract_urls",
        }


async def map_site_node(state: DocumentManagerState) -> dict:
    """Map website structure using Tavily map operation"""
    try:
        base_url = state["action_params"].get("base_url")

        if not base_url:
            return {
                **state,
                "error": "No base URL provided",
                "final_response": "Please provide a base URL to map.",
                "current_step": "map_site",
            }

        # Get settings and document store
        settings = get_settings()
        doc_store = await get_document_store()

        # Initialize TavilyToolset
        tavily = TavilyToolset(
            api_key=settings.tavily_api_key,
            document_store=doc_store,
            enable_caching=True,
        )

        # Map website
        result = await tavily.map_site(
            base_url=base_url,
            user_id=state["user_id"],
            max_depth=2,
            max_breadth=20,
            limit=50,
        )

        # Format response
        url_list = "\n".join([f"  - {url}" for url in result.urls])
        response = f"Site Map for {base_url}:\n\n{url_list}\n\nTotal URLs: {len(result.urls)}"

        return {
            **state,
            "final_response": response,
            "current_step": "map_site",
        }

    except Exception as e:
        return {
            **state,
            "error": str(e),
            "final_response": f"Site mapping failed: {str(e)}",
            "current_step": "map_site",
        }


async def process_web_documents_node(state: DocumentManagerState) -> dict:
    """Chunk web documents for storage"""
    try:
        web_documents = state.get("web_documents", [])

        if not web_documents:
            return {
                **state,
                "error": "No web documents to process",
                "final_response": "No web content retrieved to process.",
                "current_step": "process_web",
            }

        # Chunk all web documents
        chunker = DocumentChunker()
        all_chunks = []

        for doc_idx, doc in enumerate(web_documents):
            doc_chunks = await chunker.chunk_document(
                content=doc["content"],
                metadata={
                    **doc["metadata"],
                    "document_index": doc_idx
                }
            )
            all_chunks.extend(doc_chunks)

        return {
            **state,
            "chunks": all_chunks,
            "current_step": "process_web",
        }

    except Exception as e:
        return {
            **state,
            "error": str(e),
            "final_response": f"Failed to process web documents: {str(e)}",
            "current_step": "process_web",
        }




async def finalize_response_node(state: DocumentManagerState) -> dict:
    """
    Format and return final response

    Enhanced to intelligently format based on query type:
    - Model deprecation queries → Formatted analysis report
    - General queries → Standard formatting
    """
    if state.get("error"):
        return {
            **state,
            "final_response": state.get("final_response", f"Error: {state['error']}"),
            "current_step": "finalize",
        }

    # Check if this is a model-related query that needs special formatting
    query = state.get("query", "").lower()
    search_query = state.get("search_query", "").lower()
    web_documents = state.get("web_documents", [])

    is_model_query = any(
        keyword in query or keyword in search_query
        for keyword in ['model', 'deprecated', 'llm', 'gpt', 'claude', 'deprecation', 'sunset']
    )

    if is_model_query and web_documents and not state.get("final_response"):
        # Generate formatted model deprecation report
        formatted_report = await _format_model_deprecation_report(state)
        return {
            **state,
            "final_response": formatted_report,
            "current_step": "finalize",
        }

    return {
        **state,
        "final_response": state.get("final_response", "Task completed."),
        "current_step": "finalize",
    }


def route_action(state: DocumentManagerState) -> str:
    """Route to appropriate action node based on action_type"""
    action_type = state.get("action_type", "search_all")

    action_map = {
        "load_file": "load_file",
        "search_web": "search_web",
        "create_collection": "create_collection",
        "delete_collection": "delete_collection",
        "list_collections": "list_collections",
        "search_collection": "search_collection",
        "search_multiple": "search_multiple",
        "search_all": "search_all",
        "needs_reasoning": "llm_reasoning",  # NEW: Route to LLM reasoning
        "crawl_site": "crawl_site",
        "extract_urls": "extract_urls",
        "map_site": "map_site",
    }

    return action_map.get(action_type, "search_all")
