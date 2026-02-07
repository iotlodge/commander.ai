"""
Category Classifier - Auto-detect Task Objectives

Classifies user commands into categories:
- research: Information gathering, web search, fact-finding
- analysis: Data analysis, pattern detection, interpretation
- writing: Content creation, documentation, communication
- compliance: Policy review, risk assessment, regulations
- planning: Strategy, coordination, task breakdown
- chat: Conversational, Q&A, general help

Used by IntelligentRouter to select best agent for each task type.

**Cost**: 1 LLM call per classification (~150 tokens input, ~10 tokens output)
**Per Task**: ~$0.00002 (GPT-4o-mini)
"""

import logging
from typing import Optional
from enum import Enum

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

from backend.core.config import get_settings

logger = logging.getLogger(__name__)


class TaskCategory(str, Enum):
    """Task objective categories"""
    RESEARCH = "research"
    ANALYSIS = "analysis"
    WRITING = "writing"
    COMPLIANCE = "compliance"
    PLANNING = "planning"
    CHAT = "chat"
    UNKNOWN = "unknown"


class CategoryClassifier:
    """
    Classify user commands into objective categories

    Uses GPT-4o-mini for fast, cheap classification (~$0.00002 per task)
    """

    # Category descriptions for classification
    CATEGORIES = {
        "research": "Information gathering, web search, fact-finding, exploring topics",
        "analysis": "Data analysis, pattern detection, interpretation, insights",
        "writing": "Content creation, documentation, emails, reports",
        "compliance": "Policy review, risk assessment, regulations, legal",
        "planning": "Strategy, coordination, task breakdown, multi-step workflows",
        "chat": "Conversational, Q&A, general help, simple questions"
    }

    def __init__(self):
        settings = get_settings()

        # Use GPT-4o-mini for cost-effective classification
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.0,  # Deterministic classification
            api_key=settings.openai_api_key
        )

    async def classify(self, command: str) -> TaskCategory:
        """
        Classify a user command into a category

        Args:
            command: User's command (e.g., "@bob research quantum computing")

        Returns:
            TaskCategory enum value

        Cost: ~$0.00002 per classification
        """
        logger.info(f"Classifying command: {command[:50]}...")

        try:
            prompt = self._build_classification_prompt(command)

            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            category_str = response.content.strip().lower()

            # Map to enum
            category = self._parse_category(category_str)

            logger.info(f"Classified as: {category.value}")
            return category

        except Exception as e:
            logger.error(f"Classification failed: {e}", exc_info=True)
            return TaskCategory.UNKNOWN

    def _build_classification_prompt(self, command: str) -> str:
        """Build prompt for category classification"""
        categories_list = "\n".join(
            f"- {cat}: {desc}"
            for cat, desc in self.CATEGORIES.items()
        )

        return f"""Classify this user command into ONE category.

Command: {command}

Categories:
{categories_list}

Respond with ONLY the category name (e.g., "research", "analysis", "writing").
If uncertain, choose the closest match or "chat" for simple questions."""

    def _parse_category(self, category_str: str) -> TaskCategory:
        """Parse LLM response to enum"""
        category_str = category_str.lower().strip()

        # Direct match
        for category in TaskCategory:
            if category.value == category_str:
                return category

        # Fuzzy match (in case LLM adds extra words)
        for category in TaskCategory:
            if category.value in category_str:
                return category

        logger.warning(f"Unknown category '{category_str}', defaulting to UNKNOWN")
        return TaskCategory.UNKNOWN

    def classify_sync(self, command: str) -> TaskCategory:
        """
        Synchronous classification (for non-async contexts)

        Falls back to keyword-based classification without LLM.
        Less accurate but free.
        """
        command_lower = command.lower()

        # Keyword-based classification (free fallback)
        if any(kw in command_lower for kw in ["research", "find", "search", "explore", "investigate"]):
            return TaskCategory.RESEARCH

        if any(kw in command_lower for kw in ["analyze", "analysis", "data", "insights", "patterns"]):
            return TaskCategory.ANALYSIS

        if any(kw in command_lower for kw in ["write", "create", "draft", "compose", "document"]):
            return TaskCategory.WRITING

        if any(kw in command_lower for kw in ["compliance", "policy", "risk", "legal", "regulations"]):
            return TaskCategory.COMPLIANCE

        if any(kw in command_lower for kw in ["plan", "coordinate", "organize", "orchestrate", "delegate"]):
            return TaskCategory.PLANNING

        if any(kw in command_lower for kw in ["what", "how", "why", "when", "help", "?"]):
            return TaskCategory.CHAT

        return TaskCategory.UNKNOWN


# Convenience function

async def classify_command(command: str) -> TaskCategory:
    """
    Classify a user command

    Usage:
        category = await classify_command("@bob research quantum computing")
        # category = TaskCategory.RESEARCH
    """
    classifier = CategoryClassifier()
    return await classifier.classify(command)
