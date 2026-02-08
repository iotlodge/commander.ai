# Agent-Initiated Task Scheduling - Architecture Plan

**Status:** 📋 Planning Phase
**Priority:** Medium (after Alice stabilization)
**Estimated Effort:** 1-2 days implementation + testing

---

## Executive Summary

Enable **all agents** to schedule recurring tasks with user approval via **Graph Interrupts**. Agents will have access to a `TaskTool` with full CRUD operations to create, check, confirm, and manage scheduled tasks.

**Key Design Decision:** Graph Interrupt prevents runaway scheduling - agents MUST ask user permission before creating schedules.

---

## Current State vs Future State

| Aspect | Current (User-Initiated) | Future (Agent-Initiated) |
|--------|-------------------------|--------------------------|
| **Who Schedules** | User via Mission Control UI | Agents via LLM reasoning + approval |
| **Access Method** | REST API (`/api/scheduled-commands`) | LangChain Tool (`TaskTool`) |
| **Approval** | Implicit (user clicks button) | Explicit (Graph Interrupt) |
| **Agent Support** | N/A | ALL agents (leo, alice, bob, sue, rex, maya, kai, chat) |
| **CRUD Operations** | Full (UI) | Full (Tool: create, list, update, delete) |

---

## Architecture Overview

### **1. TaskTool (LangChain Tool)**

**Why Tool vs Graph Node:**
- ✅ Portable across ALL agents (no need to modify 8 graphs)
- ✅ Agents can call it from any node during reasoning
- ✅ Standardized interface (LangChain tools)
- ✅ Easier to add permissions/validation
- ❌ Only agent_g currently uses tools (BUT this is intentional - all agents should support tools)

**Tool Structure:**

```python
# backend/tools/task_scheduling_tool.py

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Literal

class TaskSchedulingInput(BaseModel):
    """Input schema for task scheduling tool"""
    operation: Literal["create", "list", "update", "delete"] = Field(
        description="CRUD operation to perform"
    )
    command_text: str | None = Field(
        default=None,
        description="Command to schedule (e.g., '@alice check deprecated models')"
    )
    schedule_type: Literal["cron", "interval"] | None = Field(
        default=None,
        description="Schedule type: cron expression or simple interval"
    )
    interval_value: int | None = Field(
        default=None,
        description="Interval value (e.g., 1 for daily, 7 for weekly)"
    )
    interval_unit: Literal["minutes", "hours", "days"] | None = Field(
        default=None,
        description="Interval unit for simple schedules"
    )
    cron_expression: str | None = Field(
        default=None,
        description="Cron expression for complex schedules (e.g., '0 9 * * 1-5')"
    )
    description: str | None = Field(
        default=None,
        description="Human-readable description of the scheduled task"
    )
    schedule_id: str | None = Field(
        default=None,
        description="Schedule ID for update/delete operations"
    )

class TaskSchedulingTool(BaseTool):
    """
    Tool for agents to manage scheduled tasks

    Operations:
    - create: Create a new scheduled task (requires user approval via interrupt)
    - list: List existing schedules for this agent
    - update: Modify an existing schedule
    - delete: Remove a schedule
    """
    name = "schedule_task"
    description = """
    Manage recurring scheduled tasks.

    Use this tool when:
    - User asks for automation ("check this daily", "run weekly reports")
    - You identify a valuable recurring task
    - Task has time-based value (health checks, monitoring, reports)

    IMPORTANT: Creating schedules requires user approval. The system will
    pause and ask the user to confirm before actually creating the schedule.
    """
    args_schema = TaskSchedulingInput

    def _run(self, **kwargs):
        """Synchronous version (not used)"""
        raise NotImplementedError("Use async version")

    async def _arun(
        self,
        operation: str,
        command_text: str | None = None,
        schedule_type: str | None = None,
        interval_value: int | None = None,
        interval_unit: str | None = None,
        cron_expression: str | None = None,
        description: str | None = None,
        schedule_id: str | None = None,
    ) -> str:
        """
        Execute scheduling operation

        Returns:
            - For 'list': JSON list of schedules
            - For 'create': Schedule ID or approval request
            - For 'update/delete': Confirmation message
        """
        from backend.repositories.scheduled_command_repository import ScheduledCommandRepository
        from backend.core.database import get_session_maker

        session_maker = get_session_maker()

        async with session_maker() as session:
            repo = ScheduledCommandRepository(session)

            if operation == "list":
                # List schedules for this agent
                # Get agent_id from context (injected by agent)
                schedules = await repo.get_user_scheduled_commands(
                    user_id=self.user_id,  # Injected
                    agent_id=self.agent_id,  # Injected
                )
                return json.dumps([{
                    "id": str(s.id),
                    "command": s.command_text,
                    "schedule": f"{s.schedule_type}: {s.cron_expression or f'Every {s.interval_value} {s.interval_unit}'}",
                    "enabled": s.enabled,
                    "next_run": str(s.next_run_at),
                } for s in schedules], indent=2)

            elif operation == "create":
                # IMPORTANT: This triggers a Graph Interrupt
                # The agent's execution will PAUSE and ask user for approval
                # If approved, the schedule is created
                # If denied, the agent receives "User denied schedule creation"

                # Return a special marker that triggers interrupt
                return "__INTERRUPT_SCHEDULE_CREATE__" + json.dumps({
                    "command_text": command_text,
                    "schedule_type": schedule_type,
                    "interval_value": interval_value,
                    "interval_unit": interval_unit,
                    "cron_expression": cron_expression,
                    "description": description,
                })

            elif operation == "update":
                # Update existing schedule
                # (validation, user ownership check, etc.)
                pass

            elif operation == "delete":
                # Delete schedule
                # (validation, user ownership check, etc.)
                pass
```

---

### **2. Graph Interrupt Implementation**

**What is a Graph Interrupt?**
- LangGraph feature that PAUSES execution and waits for user input
- Agent proposes an action → User approves/denies → Agent continues

**Implementation:**

```python
# backend/agents/base/agent_interface.py (BaseAgent class)

async def _execute_graph(self, command: str, context: AgentExecutionContext):
    """Execute graph with interrupt handling"""

    initial_state = {...}

    # Enable checkpointing for interrupts
    # (Graph must be compiled with checkpointer)
    config = {
        "configurable": {
            "thread_id": str(context.thread_id),
            "user_id": str(context.user_id),
        },
        "checkpointer": self.checkpointer,  # MemorySaver or PostgresCheckpointer
    }

    # Execute graph until interrupt or completion
    async for event in self.graph.astream(initial_state, config):
        # Check for interrupt marker in tool outputs
        if "__INTERRUPT_SCHEDULE_CREATE__" in str(event):
            # Extract schedule details
            schedule_data = json.loads(event.split("__INTERRUPT_SCHEDULE_CREATE__")[1])

            # Send approval request to user via WebSocket
            from backend.api.websocket import get_ws_manager
            ws_manager = get_ws_manager()

            await ws_manager.send_approval_request(
                user_id=context.user_id,
                task_id=context.task_id,
                approval_type="schedule_create",
                data=schedule_data,
                message=f"Agent @{self.nickname} wants to create a scheduled task:\n\n"
                        f"Command: {schedule_data['command_text']}\n"
                        f"Schedule: Every {schedule_data['interval_value']} {schedule_data['interval_unit']}\n"
                        f"Description: {schedule_data['description']}\n\n"
                        f"Approve?"
            )

            # PAUSE execution - wait for user response
            # User response will be sent via WebSocket and resume graph
            # (Implementation: wait for approval_response event)

            break  # Exit stream, wait for approval

    # After approval, resume graph with approval result
    # (LangGraph handles state restoration via checkpointer)
```

---

### **3. Frontend Integration**

**New UI Component: Approval Modal**

```tsx
// frontend/components/mission-control/approval-request-modal.tsx

interface ApprovalRequest {
  task_id: string;
  agent_nickname: string;
  approval_type: "schedule_create";
  data: {
    command_text: string;
    schedule_type: string;
    interval_value: number;
    interval_unit: string;
    description: string;
  };
  message: string;
}

export function ApprovalRequestModal({
  request,
  onApprove,
  onDeny,
}: {
  request: ApprovalRequest;
  onApprove: () => void;
  onDeny: () => void;
}) {
  return (
    <Dialog open={true}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5 text-yellow-400" />
            Approval Required - @{request.agent_nickname}
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          <div className="bg-[var(--mc-bg-tertiary)] p-4 rounded-lg">
            <div className="text-sm text-[var(--mc-text-secondary)]">
              {request.message}
            </div>
          </div>

          <div className="space-y-2">
            <div>
              <span className="font-semibold">Command:</span>{" "}
              <code className="text-xs bg-[var(--mc-bg-tertiary)] px-2 py-1 rounded">
                {request.data.command_text}
              </code>
            </div>
            <div>
              <span className="font-semibold">Schedule:</span> Every{" "}
              {request.data.interval_value} {request.data.interval_unit}
            </div>
            <div>
              <span className="font-semibold">Description:</span>{" "}
              {request.data.description}
            </div>
          </div>
        </div>

        <div className="flex gap-2 justify-end pt-4">
          <Button
            onClick={onDeny}
            variant="outline"
            className="border-red-500 text-red-400"
          >
            Deny
          </Button>
          <Button
            onClick={onApprove}
            className="bg-green-500 hover:bg-green-600"
          >
            Approve & Create Schedule
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
```

**WebSocket Event Handling:**

```tsx
// frontend/lib/hooks/use-websocket.ts

// Listen for approval requests
socket.on("approval_request", (request: ApprovalRequest) => {
  setApprovalRequest(request);  // Show modal
});

// Send approval response
const approveSchedule = (taskId: string) => {
  socket.emit("approval_response", {
    task_id: taskId,
    approved: true,
  });
  setApprovalRequest(null);  // Close modal
};
```

---

### **4. Agent Integration**

**ALL agents need to bind the TaskSchedulingTool:**

```python
# backend/agents/specialized/agent_d/graph.py (Alice)

from backend.tools.task_scheduling_tool import TaskSchedulingTool

class DocumentManagerAgent(BaseAgent):
    def create_graph(self) -> StateGraph:
        # Bind tool to LLM nodes
        task_tool = TaskSchedulingTool(
            user_id=self.user_id,   # Injected during execute()
            agent_id=self.agent_id,
        )

        # For agents using LLM nodes (like llm_reasoning_node):
        # llm = create_llm(config).bind_tools(tools=[task_tool])

        # OR: Add dedicated tool node
        graph.add_node("use_tool", create_tool_node([task_tool]))
```

**Repeat for ALL 8 agents** (leo, alice, bob, sue, rex, maya, kai, chat)

---

## Implementation Phases

### **Phase 1: Core Infrastructure** (Day 1, Morning)

- [ ] Create `TaskSchedulingTool` class (`backend/tools/task_scheduling_tool.py`)
- [ ] Implement CRUD operations (list, create, update, delete)
- [ ] Add interrupt detection logic to `BaseAgent._execute_graph()`
- [ ] Set up checkpointer (MemorySaver for MVP, PostgresCheckpointer later)
- [ ] Unit tests for TaskSchedulingTool

**Deliverables:**
- Working tool that can list schedules
- Interrupt marker detection working
- Tests passing

---

### **Phase 2: Graph Interrupt & Approval Flow** (Day 1, Afternoon)

- [ ] Implement WebSocket approval request event
- [ ] Create `ApprovalRequestModal.tsx` component
- [ ] Add approval response handler (approve/deny)
- [ ] Test interrupt → pause → approval → resume flow
- [ ] Handle denial case (agent receives "denied" response)

**Deliverables:**
- Graph pauses on schedule creation
- Modal appears with approval request
- Approve creates schedule, Deny cancels

---

### **Phase 3: Agent Integration** (Day 2, Morning)

- [ ] Bind `TaskSchedulingTool` to ALL 8 agents
- [ ] Update agent prompts to mention scheduling capability
- [ ] Add scheduling examples to prompts
- [ ] Test each agent can trigger tool

**Agents to Update:**
1. agent_parent (leo) - Orchestrator
2. agent_a (bob) - Research
3. agent_b (sue) - Compliance
4. agent_c (rex) - Data Analytics
5. agent_d (alice) - Documents
6. agent_e (maya) - Reflection
7. agent_f (kai) - Reflexion
8. agent_g (chat) - General Chat

**Deliverables:**
- All agents can call `schedule_task` tool
- Prompts explain when to schedule tasks

---

### **Phase 4: Testing & Polish** (Day 2, Afternoon)

- [ ] End-to-end test: Agent proposes schedule → User approves → Schedule created
- [ ] Test denial flow: Agent proposes → User denies → Agent acknowledges
- [ ] Test edge cases (duplicate schedules, max limit, invalid cron)
- [ ] Update CLAUDE.md with scheduling documentation
- [ ] Add scheduling example to README.md

**Deliverables:**
- Production-ready feature
- Documentation complete
- All tests passing

---

## Critical Files

| File | Purpose | Lines | Complexity |
|------|---------|-------|------------|
| `backend/tools/task_scheduling_tool.py` | Tool implementation | ~200 | Medium |
| `backend/agents/base/agent_interface.py` | Interrupt handling | +80 | High |
| `backend/api/websocket.py` | Approval events | +40 | Medium |
| `frontend/components/mission-control/approval-request-modal.tsx` | UI | ~120 | Low |
| `frontend/lib/hooks/use-websocket.ts` | Event handling | +30 | Low |
| `backend/agents/specialized/agent_*/graph.py` (x8) | Bind tool | +5 each | Low |

**Total Effort:** ~600 lines of code

---

## Security & Guardrails

### **1. Rate Limiting**
- Existing: Max 50 schedules per user (enforced in `ScheduledCommandRepository`)
- New: Check schedule count BEFORE showing approval modal
- Agent should list existing schedules first to avoid duplicates

### **2. Authorization**
- Tool receives `user_id` and `agent_id` from execution context
- All schedules are user-scoped (agents can't schedule for other users)
- Only user who created schedule can update/delete

### **3. Duplicate Prevention**
```python
# In TaskSchedulingTool._arun() before creating:

existing = await repo.get_user_scheduled_commands(
    user_id=self.user_id,
    agent_id=self.agent_id,
)

for schedule in existing:
    if schedule.command_text == command_text:
        return f"⚠️ Schedule already exists: {schedule.description}"
```

### **4. Prompt Injection Defense**
- Approval modal shows RAW command text (no markdown rendering)
- User can inspect full command before approving
- Agents can't create schedules without user seeing details

---

## Testing Strategy

### **Unit Tests**

```python
# tests/tools/test_task_scheduling_tool.py

async def test_list_schedules():
    """Test listing existing schedules"""
    tool = TaskSchedulingTool(user_id=test_user, agent_id="agent_d")
    result = await tool._arun(operation="list")
    assert isinstance(json.loads(result), list)

async def test_create_triggers_interrupt():
    """Test create operation returns interrupt marker"""
    tool = TaskSchedulingTool(user_id=test_user, agent_id="agent_d")
    result = await tool._arun(
        operation="create",
        command_text="@alice test",
        schedule_type="interval",
        interval_value=1,
        interval_unit="days",
    )
    assert "__INTERRUPT_SCHEDULE_CREATE__" in result
```

### **Integration Tests**

```python
# tests/integration/test_agent_scheduling.py

async def test_alice_proposes_schedule():
    """Test Alice can propose a schedule and user approves"""
    # Send command: "@alice please check deprecated models daily"
    # Assert: Approval request sent to WebSocket
    # Simulate: User clicks "Approve"
    # Assert: Schedule created in database
    # Assert: APScheduler has the job
```

---

## Example User Flows

### **Flow 1: Agent Proposes Schedule (Approved)**

```
User: "@alice can you check for deprecated models every day?"

Alice (thinking): User wants daily checks. I'll propose a scheduled task.

Alice (calls tool): schedule_task(
  operation="create",
  command_text="@alice check for deprecated LLM models",
  schedule_type="interval",
  interval_value=1,
  interval_unit="days",
  description="Daily LLM model deprecation check"
)

[GRAPH PAUSES - Interrupt triggered]

Mission Control: [Approval Modal appears]
"Agent @alice wants to create a scheduled task:
Command: @alice check for deprecated LLM models
Schedule: Every 1 days
Approve?"

User: [Clicks "Approve"]

[Graph resumes]

Alice: "✅ I've scheduled a daily check for deprecated models.
       The first check will run tomorrow at 9:00 AM UTC."

Mission Control: [Clock icon on Alice's card now shows "1 active schedule"]
```

---

### **Flow 2: Agent Proposes Schedule (Denied)**

```
User: "@bob research our competitors"

Bob (thinking): This could benefit from weekly monitoring. Let me propose it.

Bob (calls tool): schedule_task(
  operation="create",
  command_text="@bob research competitor activity",
  schedule_type="interval",
  interval_value=7,
  interval_unit="days",
  description="Weekly competitor research"
)

[GRAPH PAUSES]

Mission Control: [Approval Modal appears]

User: [Clicks "Deny"]

[Graph resumes with denial]

Bob: "Understood, I won't schedule that. I've completed the research
      for now. You can always ask me to run this again manually."
```

---

## Open Questions

1. **Checkpointer Choice:**
   - Start with `MemorySaver` (in-memory) for MVP?
   - Migrate to `PostgresCheckpointer` later for persistence?
   - Impact: MemorySaver doesn't survive backend restarts

2. **Approval Timeout:**
   - How long should graph wait for user approval?
   - Default: 5 minutes? 1 hour?
   - What happens if user never responds? (Auto-deny?)

3. **Bulk Approval:**
   - If agent wants to create 3 schedules, show 3 modals?
   - Or batch into single approval with checklist?

4. **Scheduling Conflicts:**
   - Agent wants to schedule "@alice check X" daily
   - User already has "@alice check Y" daily
   - Should agent check for timing conflicts?

---

## Success Metrics

- [ ] All 8 agents can call `schedule_task` tool
- [ ] Graph interrupt triggers and pauses execution
- [ ] Approval modal appears with correct schedule details
- [ ] Approve → schedule created in DB + APScheduler
- [ ] Deny → agent continues without creating schedule
- [ ] No agent can create schedule without user approval
- [ ] Existing schedule limit (50/user) still enforced
- [ ] Scheduled tasks execute at correct times
- [ ] Mission Control shows active schedule count on agent cards

---

## Future Enhancements

### **Post-MVP v1.1**
- [ ] Bulk approval (approve multiple schedules at once)
- [ ] Schedule templates (save common patterns)
- [ ] Natural language parsing ("every Monday at 9am" → cron)
- [ ] Schedule preview (show next 5 execution times before approving)

### **Post-MVP v1.2**
- [ ] Schedule dependencies ("Run A, then B 30 minutes later")
- [ ] Conditional schedules ("Only if previous run failed")
- [ ] Smart scheduling (agent analyzes optimal time based on past executions)

---

**Last Updated:** February 7, 2026
**Next Steps:** Fix Alice backend errors → Implement Phase 1 → Test interrupt flow
