"""
Execution Tracking for Agent Workflows

Tracks the sequential flow of nodes, tools, and LLM calls during agent execution.
Provides observability into the agent decision-making process.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID
from langchain_core.callbacks.base import BaseCallbackHandler

logger = logging.getLogger(__name__)


class ExecutionStep:
    """Represents a single step in the execution trace"""

    def __init__(
        self,
        step_type: str,  # "node", "tool", "llm", "agent"
        name: str,
        timestamp: str,
        duration_ms: Optional[float] = None,
        inputs: Optional[Dict[str, Any]] = None,
        outputs: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.step_type = step_type
        self.name = name
        self.timestamp = timestamp
        self.duration_ms = duration_ms
        self.inputs = inputs
        self.outputs = outputs
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "type": self.step_type,
            "name": self.name,
            "timestamp": self.timestamp,
            "duration_ms": self.duration_ms,
            "inputs": self._sanitize(self.inputs),
            "outputs": self._sanitize(self.outputs),
            "metadata": self.metadata,
        }

    @staticmethod
    def _sanitize(data: Any, max_length: int = 500) -> Any:
        """Sanitize data for storage (truncate long strings, convert UUIDs)"""
        if data is None:
            return None

        # Convert UUIDs to strings
        if isinstance(data, UUID):
            return str(data)

        if isinstance(data, str):
            return data[:max_length] + "..." if len(data) > max_length else data

        if isinstance(data, dict):
            return {k: ExecutionStep._sanitize(v, max_length) for k, v in data.items()}

        if isinstance(data, list):
            return [ExecutionStep._sanitize(item, max_length) for item in data[:10]]  # Limit to 10 items

        # For other types (int, float, bool, etc.), return as-is
        # Skip non-serializable objects like callbacks
        try:
            import json
            json.dumps(data)  # Test if serializable
            return data
        except (TypeError, ValueError):
            return str(data)  # Convert non-serializable to string


class ExecutionTracker(BaseCallbackHandler):
    """
    Tracks execution flow of LangGraph agents

    Captures:
    - Node executions (graph nodes)
    - Tool calls (web search, document processing, etc.)
    - LLM invocations (GPT-4o-mini, embeddings)
    - Nested agent calls (when parent delegates to children)

    Usage:
        tracker = ExecutionTracker()
        result = await graph.ainvoke(state, config={"callbacks": [tracker]})
        trace = tracker.get_trace()
    """

    def __init__(self):
        self.flow: List[ExecutionStep] = []
        self._start_times: Dict[str, float] = {}
        self._step_counter = 0

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        return datetime.now().isoformat()

    def _get_duration(self, key: str) -> Optional[float]:
        """Calculate duration since start time"""
        if key in self._start_times:
            start_time = self._start_times.pop(key)
            return (datetime.now().timestamp() - start_time) * 1000  # Convert to ms
        return None

    def _get_step_key(self) -> str:
        """Generate unique key for tracking step timing"""
        self._step_counter += 1
        return f"step_{self._step_counter}"

    # === Chain/Node Callbacks ===

    def on_chain_start(
        self,
        serialized: Dict[str, Any],
        inputs: Dict[str, Any],
        **kwargs: Any
    ) -> None:
        """Called when a chain/node starts"""
        name = kwargs.get("name") or serialized.get("name", "unknown_node")

        # Skip internal LangGraph nodes
        if name.startswith("__") or "pregel" in name.lower():
            return

        key = self._get_step_key()
        self._start_times[key] = datetime.now().timestamp()

        step = ExecutionStep(
            step_type="node",
            name=name,
            timestamp=self._get_timestamp(),
            inputs=inputs,
        )
        self.flow.append(step)
        logger.debug(f"Node started: {name}")

    def on_chain_end(
        self,
        outputs: Dict[str, Any],
        **kwargs: Any
    ) -> None:
        """Called when a chain/node ends"""
        # Update the last step with outputs and duration
        if self.flow:
            last_step = self.flow[-1]
            if last_step.step_type == "node":
                last_step.outputs = outputs
                # Try to get duration if we have a matching start time
                if self._start_times:
                    # Pop the most recent start time
                    key = max(self._start_times.keys(), default=None)
                    if key:
                        last_step.duration_ms = self._get_duration(key)

    # === Tool Callbacks ===

    def on_tool_start(
        self,
        serialized: Dict[str, Any],
        input_str: str,
        **kwargs: Any
    ) -> None:
        """Called when a tool starts execution"""
        name = serialized.get("name", "unknown_tool")

        key = self._get_step_key()
        self._start_times[key] = datetime.now().timestamp()

        step = ExecutionStep(
            step_type="tool",
            name=name,
            timestamp=self._get_timestamp(),
            inputs={"input": input_str},
        )
        self.flow.append(step)
        logger.debug(f"Tool started: {name}")

    def on_tool_end(
        self,
        output: str,
        **kwargs: Any
    ) -> None:
        """Called when a tool ends execution"""
        if self.flow and self.flow[-1].step_type == "tool":
            last_step = self.flow[-1]
            last_step.outputs = {"output": output}

            # Get duration
            if self._start_times:
                key = max(self._start_times.keys(), default=None)
                if key:
                    last_step.duration_ms = self._get_duration(key)

    def on_tool_error(
        self,
        error: BaseException,
        **kwargs: Any
    ) -> None:
        """Called when a tool encounters an error"""
        if self.flow and self.flow[-1].step_type == "tool":
            last_step = self.flow[-1]
            last_step.metadata["error"] = str(error)
            last_step.metadata["status"] = "failed"

    # === LLM Callbacks ===

    def on_llm_start(
        self,
        serialized: Dict[str, Any],
        prompts: List[str],
        **kwargs: Any
    ) -> None:
        """Called when an LLM starts generation"""
        model_name = kwargs.get("invocation_params", {}).get("model_name", "unknown_model")

        key = self._get_step_key()
        self._start_times[key] = datetime.now().timestamp()

        step = ExecutionStep(
            step_type="llm",
            name=model_name,
            timestamp=self._get_timestamp(),
            inputs={"prompt_count": len(prompts)},
            metadata={"model": model_name}
        )
        self.flow.append(step)
        logger.debug(f"LLM started: {model_name}")

    def on_llm_end(
        self,
        response: Any,
        **kwargs: Any
    ) -> None:
        """Called when an LLM finishes generation"""
        if self.flow and self.flow[-1].step_type == "llm":
            last_step = self.flow[-1]

            # Extract token usage if available
            if hasattr(response, "llm_output") and response.llm_output:
                token_usage = response.llm_output.get("token_usage", {})
                last_step.metadata["tokens"] = token_usage

            # Get duration
            if self._start_times:
                key = max(self._start_times.keys(), default=None)
                if key:
                    last_step.duration_ms = self._get_duration(key)

    def on_llm_error(
        self,
        error: BaseException,
        **kwargs: Any
    ) -> None:
        """Called when an LLM encounters an error"""
        if self.flow and self.flow[-1].step_type == "llm":
            last_step = self.flow[-1]
            last_step.metadata["error"] = str(error)
            last_step.metadata["status"] = "failed"

    # === Retrieval Methods ===

    def get_trace(self) -> List[Dict[str, Any]]:
        """Get the execution trace as a list of dictionaries"""
        return [step.to_dict() for step in self.flow]

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the execution"""
        total_duration = sum(
            step.duration_ms for step in self.flow
            if step.duration_ms is not None
        )

        step_counts = {}
        for step in self.flow:
            step_counts[step.step_type] = step_counts.get(step.step_type, 0) + 1

        return {
            "total_steps": len(self.flow),
            "total_duration_ms": total_duration,
            "step_counts": step_counts,
            "nodes": [s.name for s in self.flow if s.step_type == "node"],
            "tools": [s.name for s in self.flow if s.step_type == "tool"],
            "llms": [s.name for s in self.flow if s.step_type == "llm"],
        }

    def clear(self):
        """Clear the execution trace"""
        self.flow = []
        self._start_times = {}
        self._step_counter = 0
