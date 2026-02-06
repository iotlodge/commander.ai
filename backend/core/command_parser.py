"""
Command Parser - Parses user commands to extract agent mentions and routing info
Supports @mentions and natural greetings
"""

import re
import logging
from dataclasses import dataclass
from typing import List

from backend.agents.base.agent_registry import AgentRegistry

logger = logging.getLogger(__name__)


@dataclass
class ParsedCommand:
    """Result of command parsing"""

    raw_command: str
    mentioned_agents: List[str]  # List of agent IDs
    greeting_target: str | None  # Agent ID if greeting detected
    clean_command: str  # Command with @mentions removed
    is_direct_mention: bool  # True if command starts with @mention
    requires_parent: bool  # True if multiple agents or complex task


class CommandParser:
    """
    Parses commands to extract agent mentions and routing information
    """

    # Greeting patterns: "hello bob", "hi sue", "hey rex"
    GREETING_PATTERNS = [
        r"^(hello|hi|hey|greetings)\s+(\w+)",
        r"^(\w+),?\s+(hello|hi|hey|greetings)",
    ]

    # @mention pattern: "@bob", "@sue"
    MENTION_PATTERN = r"@(\w+)"

    @classmethod
    def parse(cls, command: str) -> ParsedCommand:
        """
        Parse a command to extract agent mentions and routing info
        """
        command = command.strip()
        mentioned_agents: List[str] = []
        greeting_target: str | None = None

        # Check for greetings
        for pattern in cls.GREETING_PATTERNS:
            match = re.search(pattern, command.lower())
            if match:
                # Extract nickname from greeting
                for group in match.groups():
                    if group not in ["hello", "hi", "hey", "greetings"]:
                        agent = AgentRegistry.get_by_nickname(group)
                        if agent:
                            greeting_target = agent.agent_id
                            mentioned_agents.append(agent.agent_id)
                        break
                break

        # Extract @mentions
        mentions = re.findall(cls.MENTION_PATTERN, command)
        for nickname in mentions:
            agent = AgentRegistry.get_by_nickname(nickname)
            if agent and agent.agent_id not in mentioned_agents:
                mentioned_agents.append(agent.agent_id)
            elif not agent:
                # Trust but verify: Agent mentioned but not found in registry
                logger.warning(
                    f"Agent nickname '@{nickname}' mentioned in command but not found in registry. "
                    f"Registered nicknames: {AgentRegistry.get_all_nicknames()}"
                )

        # Clean command (remove @mentions)
        clean_command = re.sub(cls.MENTION_PATTERN, "", command).strip()
        clean_command = re.sub(r"\s+", " ", clean_command)  # Normalize spaces

        # Determine if direct mention (command starts with @mention)
        is_direct_mention = bool(re.match(r"^@\w+", command))

        # Determine if parent agent needed
        # Parent needed if: multiple agents mentioned OR no specific agent
        requires_parent = len(mentioned_agents) > 1 or (
            len(mentioned_agents) == 0 and not greeting_target
        )

        return ParsedCommand(
            raw_command=command,
            mentioned_agents=mentioned_agents,
            greeting_target=greeting_target,
            clean_command=clean_command,
            is_direct_mention=is_direct_mention,
            requires_parent=requires_parent,
        )

    @classmethod
    def get_target_agent_id(cls, parsed: ParsedCommand) -> str:
        """
        Determine which agent should handle this command
        Returns agent_id
        """
        # Priority 1: Greeting target
        if parsed.greeting_target:
            return parsed.greeting_target

        # Priority 2: Single direct mention
        if len(parsed.mentioned_agents) == 1:
            return parsed.mentioned_agents[0]

        # Priority 3: Multiple mentions or no mention -> parent agent
        return "parent"

    @classmethod
    def extract_consultation_pattern(cls, command: str) -> tuple[str | None, str | None]:
        """
        Detect patterns like "ask bob about X" or "consult sue on Y"
        Returns (target_agent_id, consultation_query)
        """
        patterns = [
            r"(?:ask|consult)\s+@?(\w+)\s+(?:about|on|regarding)\s+(.+)",
            r"@?(\w+),?\s+(?:what|how|can you)\s+(.+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, command.lower())
            if match:
                nickname = match.group(1)
                query = match.group(2).strip()
                agent = AgentRegistry.get_by_nickname(nickname)
                if agent:
                    return (agent.agent_id, query)

        return (None, None)
