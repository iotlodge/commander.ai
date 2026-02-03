# Commander.ai – Project Plan

## Objective

Build a modular AI orchestration platform with both UI and CLI interfaces that connect to a shared backend powered by LangGraph workflows.  

Primary focus for this phase is improving and extending backend graph workflows, particularly around task decomposition, reasoning, and multi-agent interoperability.

---

## High-Level Architecture

### Interfaces

- **User Interfaces**
  - Web UI (React) – already implemented and functional  
  - CLI – planned for v1.0  

Both interfaces must be able to:
- Attach to a running backend session  
- Reattach to previous sessions  
- Submit commands  
- Retrieve results  

### Backend Overview

The backend consists of:

- LangGraph (LangChain-based) workflows
- Multiple AI agents communicating via graph nodes
- Persistent memory and storage

Current infrastructure stack (already operational):

| Component | Purpose |
|--------|--------|
| Redis | Short-Term Memory (STM) |
| PostgreSQL | Long-Term Memory (LTM) |
| Qdrant | Vector storage |
| Docker | Containerized deployment |
| Migrations | Fully working |

All services are dockerized with startup scripts and confirmed operational.

---

## Current State

### What Is Already Working

- UI is fully functional and communicating with backend graphs  
- Backend infrastructure is in place and stable  
- Database migrations working  
- Memory and vector stores integrated  
- Graph execution pipeline functional  

---

## Current Workflow Behavior

### Entry Node

- System currently uses a `decompose_task_node` as the entry point
- This node does **not** use an LLM
- Performs basic pattern matching to route requests

This works adequately for:
- Routing to specialized agents  
- Simple command execution  

---

## New Requirement – Research Workflow

### Problem to Solve

The existing pattern-matching entry node is insufficient for complex research tasks.

For research-oriented commands, we need a smarter, LLM-driven reasoning pipeline.

---

## Proposed Enhancements

### 1. Introduce a Reasoning Agent

When a request involves research, the system should:

- Route the request to a **new reasoning agent**
- Example agent: `@bob`
- Use OpenAI models such as:

```python
ChatOpenAI(model="gpt-4o-mini", temperature=0)
```

### 2. Prompt Refinement Flow

The reasoning agent will:

- Analyze the original user prompt  
- Redraft it into specialized prompts  
- Generate one or more targeted instructions  
- Dispatch them to Reflection / Reflexion agents  

---

## Multi-Agent Execution Model

### Parallel Processing

- The reasoning agent determines investigation areas  
- Each area is assigned to one or more agents  
- Agents execute in parallel  
- All results are collected  

### Aggregation

- Results are combined using simple aggregation initially  
- Aggregated output must be downloadable from the UI  

---

## Required Development Focus

Primary engineering focus areas:

1. Backend graph adjustments  
2. New node types  
3. LLM-based routing  
4. Custom prompt generation  
5. Multi-agent parallel execution  
6. Result aggregation pipeline  
7. Build simple Reflexion Agent (use OpenAI LLM)
   8. Youre choice on name
8. Build simple Reflection Agent (use OpenAI LLM)
   9. Your choice on name

API keys will be sourced from `.env`.

---

## Command Interface Requirements

### Hard Requirement

Users must be able to issue natural language commands from:

- Web UI command field  
- CLI async loop

Example command format:

```
@Agents research "Designing a Quantum Accelerator" investigate ['area one', 'area two', 'area three']
```

---

## Execution Flow Requirement

When such a command is submitted:

1. Command received by parent orchestrator agent (`@Leo`)
2. Leo routes request to the new reasoning agent
3. Reasoning agent:
   - Interprets intent  
   - Decomposes into subtasks  
   - Creates prompts  
4. Parallel agents execute assigned tasks  
5. Results are aggregated  
6. Output returned to UI or CLI  

---

## Next Steps

### Immediate Tasks

- Review current backend codebase  
- Implement LLM router node  
- Create reasoning agent  
- Add Reflection / Reflexion agents  
- Integrate parallel execution  
- Build aggregation logic  

---

## Version Goal

- Deliver fully functional multi-agent research workflow  
- Support both UI and CLI interactions  
- Stable backend architecture  
- Ready for v1.0 release  

---

## Summary

This phase is not about infrastructure. That is already working.

The focus is:

- Graph workflow design  
- Agent orchestration  
- Intelligent routing  
- Reasoning capabilities  
- Multi-agent interoperability  

The goal is to evolve Commander.ai from a rule-based task router into a reasoning-driven AI orchestration platform.
