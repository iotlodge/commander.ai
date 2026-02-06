# Commander.ai - Claude Code Reference

This document provides context about Commander.ai's architecture, patterns, and Mission Control UI for Claude Code.

---

## Project Overview

**Commander.ai** is a multi-agent AI orchestration system with a real-time Mission Control interface. Users delegate tasks to specialized AI agents and watch them execute with complete visibility.

**Core Philosophy**: Maximum visibility, maximum control. Show users exactly what's happening as AI agents work.

---

## Mission Control UI Architecture

### Three-Panel Layout

The UI is organized into three distinct panels (left → center → right):

```
┌──────────────┬────────────────────────┬───────────────┐
│ Agent Team   │   Conversation Stream  │ Quick Actions │
│   Panel      │                        │    Panel      │
│  (264px)     │    (flexible width)    │   (288px)     │
└──────────────┴────────────────────────┴───────────────┘
```

**Design Principle**: No Kanban boards, no project management UI. This is Mission Control for AI orchestration, not task management.

### Component Structure

```
frontend/components/
├── mission-control/
│   ├── mission-control-layout.tsx         # Root layout with 3 panels
│   ├── agent-team-panel.tsx              # Left: Agent roster + metrics
│   ├── conversation-stream.tsx           # Center: Command/response flow
│   ├── command-input-bar.tsx             # Bottom of center: Input
│   ├── quick-actions-panel.tsx           # Right: One-click commands
│   ├── conversation-message.tsx          # Individual agent responses
│   ├── system-message.tsx                # In-progress indicators
│   ├── inline-execution-flow.tsx         # Metrics timeline display
│   ├── inline-agent-graph.tsx            # Workflow visualization
│   ├── keyboard-shortcuts-help.tsx       # Shortcuts modal
│   ├── chat-mode-context.tsx             # Chat mode state
│   └── index.ts                          # Barrel export
├── command/
│   └── agent-mention-autocomplete.tsx    # @mention suggestions
├── providers/
│   └── ...context providers
└── ui/
    └── ...shadcn/ui components (button, card, dialog, etc.)
```

**Note**: Recent cleanup removed unused components (chat-modal, graph viewers, old input components) and empty directories. Only Mission Control and actively used components remain.

---

## Key UI Patterns

### 1. Real-Time Agent Metrics

**Location**: `agent-team-panel.tsx`

Agent tiles show **live metrics** that update as tasks execute:

```typescript
// Metrics extracted from task.metadata.execution_metrics
{
  tokens: number,           // Green - "1,234 tok"
  llmCalls: number,         // Purple - "3 LLM"
  toolCalls: number,        // Yellow - "2 tools"
  currentNode: string,      // Blue - "→ reasoning"
}
```

**Key Function**: `getAgentActivity(nickname: string)` aggregates metrics from all active tasks for an agent.

**Visual Indicators**:
- Green pulsing dot: Agent has active tasks
- Badge counts: "1 active", "2 queued"
- Live metrics: Update on every WebSocket event

### 2. Conversation Stream

**Location**: `conversation-stream.tsx`

Displays chronological conversation items built from task state:

```typescript
type ConversationItem = {
  id: string,
  type: "user_command" | "agent_response" | "system_event",
  timestamp: Date,
  content: any
}
```

**Critical Pattern**: NO ANIMATIONS (removed to prevent shaking/re-render loops)
- Items render instantly, no slide-ins or fades
- Memoized components prevent unnecessary re-renders
- Auto-scroll uses `behavior: "instant"` not "smooth"

**State Management**:
- Builds from `useTaskStore().tasks` (Zustand)
- Updates on WebSocket events via `handleWebSocketEvent`
- Creates user_command, agent_response, system_event items

### 3. Metrics & Flow Display

**Location**: `inline-execution-flow.tsx`

Shows comprehensive execution metrics when expanded:

```typescript
// Data structure from backend
executionMetrics: {
  llm_calls: number,
  tool_calls: number,
  agent_calls: number,
  tokens: {
    prompt: number,
    completion: number,
    total: number
  }
}

executionSummary: {
  total_steps: number,
  total_duration_ms: number,
  step_counts: Record<string, number>
}

executionTrace: Array<{
  type: "node" | "tool" | "llm",
  name: string,
  timestamp: string,
  duration_ms?: number,
  metadata?: Record<string, any>
}>
```

**Visual Design**:
- Top: Metrics summary grid (tokens, calls, duration)
- Bottom: Timeline with color-coded steps (blue/yellow/purple)
- Collapsed by default, expands on click
- Positioned below agent response content

### 4. Quick Actions Panel

**Location**: `quick-actions-panel.tsx`

One-click command shortcuts organized by agent:

```typescript
interface QuickAction {
  label: string,        // "List all documents"
  command: string,      // "@alice list all documents in the system"
  icon?: ReactNode
}
```

**Interaction Flow**:
1. User clicks Quick Action button
2. `onCommandSelect(command)` called
3. Parent calls `commandInputRef.current?.setCommand(command)`
4. Command auto-fills input, cursor positioned at end
5. User edits if needed, hits Enter

**Collapsible Sections**: Only one agent expanded at a time (accordion pattern)

### 5. Agent Graph Visualization

**Location**: `inline-agent-graph.tsx`

Shows agent workflow as Mermaid diagram with zoom controls:

```typescript
// Features
- Starts at 70% zoom for better fit
- Zoom in/out buttons (± 10%)
- Reset button shows current zoom "%"
- Scrollable container (max-height: 500px)
- Transform-based scaling with smooth transitions
```

**Critical**: Fetches from `/api/graphs?user_id=MVP_USER_ID`, filters by `agent_nickname`

---

## State Management

### Zustand Store (`lib/store.ts`)

```typescript
interface TaskStore {
  tasks: Map<string, AgentTask>,
  addTask: (task) => void,
  updateTask: (taskId, updates) => void,
  removeTask: (taskId) => void,
  clearAllTasks: () => void,
  clearCompletedTasks: () => void,
  handleWebSocketEvent: (event) => void,
  getTasksByStatus: (status) => AgentTask[]
}
```

**Key Patterns**:
- Tasks stored in `Map<string, AgentTask>` for O(1) lookup
- Updates create new Map (immutability)
- WebSocket events update store → components re-render
- `clearCompletedTasks()` removes COMPLETED and FAILED tasks

### WebSocket Integration (`hooks/use-websocket.ts`)

```typescript
// Event types handled
- task_created
- task_status_changed
- task_completed
- task_metadata_updated
- task_progress
- consultation_started/completed
- task_deleted
```

**Flow**:
1. WebSocket receives event
2. `handleWebSocketEvent(event)` in store
3. Store updates task Map
4. Components using `useTaskStore()` re-render
5. UI updates instantly

---

## Component Communication Patterns

### Parent → Child (Refs)

```typescript
// CommandInputBar exposes methods via ref
interface CommandInputBarRef {
  focus: () => void,
  insertMention: (nickname: string) => void,
  setCommand: (command: string) => void
}

// Usage in parent
const commandInputRef = useRef<CommandInputBarRef>(null);
commandInputRef.current?.setCommand("@alice search...");
```

### Context API

```typescript
// Chat mode state shared across components
const ChatModeProvider: {
  isChatMode: boolean,
  enterChatMode: () => void,
  exitChatMode: () => void,
  chatThreadId: string | null
}
```

### Memoization

```typescript
// Prevent unnecessary re-renders
export const ConversationMessage = memo(
  ConversationMessageComponent,
  (prevProps, nextProps) => {
    return (
      prevProps.task.id === nextProps.task.id &&
      prevProps.task.status === nextProps.task.status &&
      prevProps.task.result === nextProps.task.result &&
      // ... check all relevant fields
    )
  }
)
```

**Critical**: Used on `ConversationMessage` and `SystemMessage` to prevent render loops

---

## Styling Patterns

### Color System

```typescript
// Agent colors (consistent across UI)
const AGENT_COLORS = {
  chat: "#4a9eff",   // Blue
  bob: "#10b981",    // Green
  sue: "#f59e0b",    // Amber
  rex: "#8b5cf6",    // Purple
  alice: "#ec4899",  // Pink
  maya: "#06b6d4",   // Cyan
  kai: "#f97316"     // Orange
}

// Metric colors
- Tokens: green-400 (#4ade80)
- LLM calls: purple-400 (#c084fc)
- Tool calls: yellow-400 (#facc15)
- Duration: blue-400 (#60a5fa)
- Agent calls: cyan-400 (#22d3ee)
```

### Dark Theme

Base colors:
- Background: `#1a1f2e`
- Panel background: `#141824`
- Card background: `#1e2433`
- Border: `#2a3444`
- Text: `white`, `gray-300`, `gray-400`, `gray-500`

**Tailwind Classes**:
- Backgrounds: `bg-[#1a1f2e]`, `bg-[#141824]`, `bg-[#1e2433]`
- Borders: `border-[#2a3444]`
- Text: `text-white`, `text-gray-300`, etc.

---

## Performance Patterns

### Why NO Animations?

Early versions had smooth slide-in/fade-in animations. This caused:
- Violent shaking on scroll
- Re-render loops
- Animations triggering on every state update

**Solution**: Removed all CSS animations from conversation items. Items render instantly.

**Trade-off**: Less visual polish, but 100% stability and performance.

### Preventing Re-Render Loops

1. **Memoize components** that render frequently
2. **Disable smooth scroll** (use `behavior: "instant"`)
3. **Remove comparison logic** that blocked legitimate updates
4. **Use refs for tracking** (e.g., `hasAnimatedRef`, `previousItemCountRef`)

---

## Data Flow

```
User Action (Quick Action click or @mention)
    ↓
CommandInputBar.handleSubmit()
    ↓
POST /api/commands?user_id=MVP_USER_ID
    ↓
Backend creates task
    ↓
WebSocket broadcasts "task_created"
    ↓
useWebSocket.events updates
    ↓
handleWebSocketEvent(event)
    ↓
useTaskStore updates tasks Map
    ↓
Components re-render (ConversationStream, AgentTeamPanel)
    ↓
UI shows: user command, agent working indicator
    ↓
WebSocket broadcasts "task_metadata_updated" (during execution)
    ↓
Agent tiles update with live metrics
    ↓
WebSocket broadcasts "task_completed"
    ↓
UI shows: agent response with results, metrics, execution flow
```

---

## Adding Features

### Adding a New Quick Action

```typescript
// quick-actions-panel.tsx
{
  agentNickname: "alice",
  agentName: "Alice",
  color: "#ec4899",
  icon: <FileText className="h-4 w-4" />,
  actions: [
    {
      label: "New action",
      command: "@alice do something new"
    },
    // ... existing actions
  ]
}
```

### Adding a New Metric

```typescript
// 1. Backend: Add to ExecutionMetrics.to_dict()
// 2. Frontend: Update ExecutionMetrics interface
interface ExecutionMetrics {
  // ... existing fields
  new_metric: number
}

// 3. Display in inline-execution-flow.tsx
{executionMetrics.new_metric !== undefined && (
  <div className="space-y-1">
    <div className="text-xs text-gray-500">New Metric</div>
    <div className="text-lg font-bold text-cyan-400">
      {executionMetrics.new_metric}
    </div>
  </div>
)}
```

---

## Testing Patterns

### Manual Testing Checklist

When testing Mission Control UI changes:

1. **Agent Tiles**
   - [ ] Submit command, watch tiles update live
   - [ ] Token counts increment
   - [ ] LLM calls count up
   - [ ] Current node shows
   - [ ] Green dot appears on active agents

2. **Conversation Stream**
   - [ ] User commands appear instantly
   - [ ] Agent responses show after completion
   - [ ] No screen shaking on scroll
   - [ ] Results display immediately (not on second load)

3. **Metrics & Flow**
   - [ ] Button appears after "Done" badge
   - [ ] Shows tokens, LLM calls, tool calls, duration
   - [ ] Execution flow timeline renders
   - [ ] Collapsible works

4. **Quick Actions**
   - [ ] Click action → fills command input
   - [ ] Cursor positioned at end
   - [ ] Can edit before submitting

5. **System Activity**
   - [ ] Active/Queued/Done counts correct
   - [ ] Clear Completed button appears when Done > 0
   - [ ] Confirmation dialog shows
   - [ ] Completed tasks removed after confirm

---

## Common Gotchas

### 1. WebSocket Connection

**Problem**: Commands submit but nothing appears.

**Check**:
- Is "🟢 Live" badge showing in agent panel?
- Is backend running?
- Check browser console for WebSocket errors
- Verify MVP_USER_ID is set correctly

### 2. Metrics Not Showing

**Problem**: Execution flow button doesn't appear.

**Check**:
- Does `task.metadata.execution_trace` exist?
- Is backend saving metrics to task metadata?
- Check data structure matches frontend interface
- Console log `task.metadata` to inspect

### 3. Re-Render Loops

**Problem**: UI constantly updates or shakes.

**Solution**:
- Use `React.memo` on frequently rendered components
- Remove animations from items that update often
- Check for unnecessary state updates in useEffect
- Use refs for tracking instead of state when possible

---

## MVP User Development Bypass

All frontend API calls include `?user_id=00000000-0000-0000-0000-000000000001` for development:

```typescript
const MVP_USER_ID = "00000000-0000-0000-0000-000000000001";

fetch(`http://localhost:8000/api/commands?user_id=${MVP_USER_ID}`, {
  method: "POST",
  // ...
});
```

**Production**: Replace with JWT token in Authorization header.

---

## Future Enhancements (Ideas)

- **Agent collaboration view**: Show when agents consult each other
- **Token cost calculator**: Real-time cost tracking
- **Custom Quick Actions**: User-defined command shortcuts
- **Agent performance dashboard**: Historical metrics
- **Multi-user**: Isolate tasks by authenticated user
- **Keyboard shortcuts**: More power-user features
- **Agent response streaming**: Show responses as they generate

---

## File Locations Reference

**Mission Control Components**:
- Layout: `frontend/components/mission-control/mission-control-layout.tsx`
- Agents: `frontend/components/mission-control/agent-team-panel.tsx`
- Conversation: `frontend/components/mission-control/conversation-stream.tsx`
- Input: `frontend/components/mission-control/command-input-bar.tsx`
- Quick Actions: `frontend/components/mission-control/quick-actions-panel.tsx`
- Autocomplete: `frontend/components/command/agent-mention-autocomplete.tsx`

**State & Hooks**:
- Store: `frontend/lib/store.ts`
- WebSocket: `frontend/lib/hooks/use-websocket.ts`
- Command Submit: `frontend/lib/hooks/use-command-submit.ts`
- Agents: `frontend/lib/hooks/use-agents.ts`

**Frontend Structure**:
- App Entry: `frontend/app/page.tsx` (renders MissionControlLayout)
- Favicon: `frontend/app/favicon.ico`
- Public: `frontend/public/` (empty - all images removed, favicon moved to /app/)

**Backend**:
- Agents: `backend/agents/specialized/agent_*/`
- API: `backend/api/main.py`
- WebSocket: `backend/api/websocket.py`
- Metrics: `backend/core/token_tracker.py`
- Execution Tracking: `backend/core/execution_tracker.py`

---

## Recent Changes (February 2026)

### February 5, 2026 - Evening Session

**Critical Fixes**:
- ✅ Fixed Leo (parent agent) missing execution metrics tracking
  - Was using manual config instead of `_build_graph_config()`
  - Now all 8 agents consistently use execution tracker callbacks
  - Leo now shows tokens, LLM calls, tool calls, duration like other agents
- ✅ Fixed Leo missing from frontend UI
  - Was missing from hardcoded AGENTS array in agent-team-panel.tsx
  - Added to Quick Actions panel with orchestration commands
  - Color: #fbbf24 (amber/gold), Icon: Network

**New Features**:
- ✅ Agent Status Indicator in header
  - Shows "X/Y agents" with live vs configured count
  - Blue badge when all agents active
  - Orange badge + alert icon when agents offline/mismatched
  - Fetches live data from `/api/agents`
- ✅ Inline autocomplete for @mentions
  - Replaced Popover-based component with simple inline dropdown
  - Maintains filtering, selection, and styling
  - Fixed build issues after cleanup

**Cleanup**:
- ✅ Removed 6 unused component files (~1,000 lines)
  - chat-modal.tsx, old command inputs, graph viewers
- ✅ Deleted 3MB of unused images from `/public/`
- ✅ Removed standalone `/graphs` page (not linked from Mission Control)
- ✅ Simplified component directory structure
- ✅ Updated frontend README to reflect current architecture

**Frontend Now**:
- Single-purpose: Mission Control interface only
- No Kanban board, no project management UI
- Clean component structure focused on AI orchestration
- All 8 agents visible and functional
- Real-time agent status monitoring

**Key Learnings**:
- Always use `_build_graph_config()` for agents to get execution tracking
- Frontend needs to sync with backend agent list (or fetch dynamically)
- Hardcoded UI lists can cause agents to "disappear" from interface
- Agent status visibility is important for system health monitoring

### February 6, 2026 - Light/Dark Mode Implementation

**Theme System**:
- ✅ Full light/dark mode toggle with system preference detection
  - Created `ThemeProvider` context (light, dark, system modes)
  - Added `ThemeToggle` button in Mission Control header
  - Persists theme to localStorage
  - Detects OS `prefers-color-scheme`
- ✅ CSS Variables architecture for scalable theming
  - Mission Control colors: `--mc-bg-primary/secondary/tertiary`, `--mc-border`, `--mc-hover`
  - Text colors: `--mc-text-primary/secondary/tertiary` (adapt per theme)
  - Agent brand colors: `--agent-leo/bob/sue/rex/alice/maya/kai/chat`
  - Metric colors: `--metric-tokens/llm/tools/duration/agent-calls`
- ✅ Comprehensive contrast improvements
  - Light mode: Dark text on bright backgrounds, visible borders
  - Dark mode: Enhanced border visibility, brighter accents
  - All 13 components refactored to use CSS variables
  - MarkdownRenderer fully theme-aware (headers, code, tables, links)
- ✅ Mermaid diagrams adapt to theme
  - Detects current theme via `useTheme()`
  - Re-renders graph when theme changes

**Files Added**:
- `frontend/components/providers/theme-provider.tsx` - Theme context and management
- `frontend/components/mission-control/theme-toggle.tsx` - UI toggle button

**Files Modified**:
- `frontend/app/globals.css` - CSS variables for both themes
- `frontend/app/layout.tsx` - ThemeProvider wrapper
- 10 Mission Control components - All colors now use CSS variables
- `frontend/components/ui/markdown-renderer.tsx` - Theme-aware markdown rendering

**Design Decisions**:
- Light mode optimized for readability (WCAG AA contrast standards)
- Dark mode maintains existing aesthetics with minor improvements
- Agent colors remain vibrant and consistent across themes
- CSS variables enable future themes without component changes
- System preference as default provides automatic adaptation

**Key Patterns**:
- Use `var(--mc-text-primary)` instead of `text-white` for adaptive text
- Use `var(--mc-bg-primary/secondary/tertiary)` for backgrounds
- Use `var(--mc-border)` instead of hardcoded hex values
- Use `var(--agent-{name})` for consistent agent branding
- MarkdownRenderer uses theme-aware colors for all elements

---

**Last Updated**: February 6, 2026 - Light/Dark Mode + Enhanced Contrast
