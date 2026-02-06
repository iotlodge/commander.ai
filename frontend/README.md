# Commander.ai Frontend

Next.js 14 frontend with Mission Control interface for real-time AI agent orchestration.

## Features

- 🎨 **Mission Control UI**: Three-panel command center (Agents, Conversation, Quick Actions)
- 🔌 **Real-time Updates**: WebSocket connection for live agent metrics and task updates
- 📊 **Agent Metrics**: Live token counts, LLM calls, tool usage, and current processing node
- ⚡ **Quick Actions**: One-click command delegation panel
- 📈 **Execution Flow**: Detailed metrics timeline with step-by-step visibility
- 🔍 **Graph Visualization**: Inline agent workflow diagrams with zoom controls
- 🎭 **shadcn/ui Components**: Professional, accessible UI components
- 🌙 **Dark Theme**: Custom color palette optimized for command center aesthetics

## Tech Stack

- **Next.js 14** - App Router with React Server Components
- **TypeScript** - Type safety throughout
- **Tailwind CSS** - Utility-first styling
- **Zustand** - Lightweight state management
- **shadcn/ui** - Accessible component library
- **Lucide Icons** - Modern icon system

## Getting Started

### Prerequisites

- Node.js 18+ installed
- Backend server running on http://localhost:8000

### Development

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to view Mission Control.

## Architecture

### Three-Panel Layout

1. **Left Panel: Agent Team** (`agent-team-panel.tsx`)
   - Live agent metrics (tokens, LLM calls, tools, current node)
   - System activity dashboard (Active | Queued | Done)
   - Click agent to auto-fill @mention

2. **Center Panel: Conversation Stream** (`conversation-stream.tsx`)
   - Chronological command/response flow
   - Expandable metrics & execution flow
   - Inline agent graph visualization
   - Command input bar with autocomplete

3. **Right Panel: Quick Actions** (`quick-actions-panel.tsx`)
   - Agent-specific one-click commands
   - Auto-fills command input on selection

### Key Components

```
components/
├── mission-control/
│   ├── mission-control-layout.tsx   # Main layout & orchestration
│   ├── agent-team-panel.tsx         # Left panel - agent roster
│   ├── conversation-stream.tsx      # Center - conversation flow
│   ├── conversation-message.tsx     # Individual message rendering
│   ├── command-input-bar.tsx        # Command input with @mentions
│   ├── quick-actions-panel.tsx      # Right panel - quick actions
│   ├── inline-agent-graph.tsx       # Graph with zoom controls
│   ├── inline-execution-flow.tsx    # Metrics timeline
│   ├── system-message.tsx           # System notifications
│   ├── chat-mode-context.tsx        # Chat mode state
│   └── keyboard-shortcuts-help.tsx  # Shortcuts modal
├── command/
│   └── agent-mention-autocomplete.tsx  # @mention suggestions
└── ui/
    └── ...shadcn components
```

### State Management

**Zustand Store** (`/lib/store.ts`):
- Task management (Map-based for O(1) lookups)
- WebSocket connection state
- Real-time updates without re-renders

**Chat Mode Context**:
- Toggle between command mode (@mentions) and chat mode (direct LLM)
- Managed via React Context

### WebSocket Integration

**Hook**: `/lib/hooks/use-websocket.ts`
- Auto-reconnect with exponential backoff
- Handles task updates, status changes, metrics
- Real-time agent metrics updates

**Events**:
- `task_status_updated` - Task lifecycle changes
- `task_result_ready` - Completion with results
- `agent_metrics_update` - Live token/LLM/tool counts

## Configuration

**MVP User ID**: `00000000-0000-0000-0000-000000000001`

**Backend Endpoints**:
- API: `http://localhost:8000`
- WebSocket: `ws://localhost:8000/ws/{user_id}`

## Development Notes

### Performance

- **No Animations**: Removed all animations to prevent render jitter
- **React.memo**: Memoized ConversationMessage and SystemMessage
- **Map Data Structure**: O(1) task lookups instead of array iteration
- **Instant Scroll**: Auto-scroll uses "instant" behavior for stability

### Color System

```css
--background: #1a1f2e      /* Main background */
--panel: #141824           /* Left panel */
--surface: #1e2433         /* Cards, headers */
--border: #2a3444          /* Borders */
--accent: #4a9eff          /* Primary blue */
```

### Keyboard Shortcuts

- `⌘K` - Focus command input
- `Esc` - Clear agent filter / Exit chat mode
- `⌘⇧G` - Scroll to bottom

## Build

```bash
# Production build
npm run build

# Start production server
npm start
```

## Testing

```bash
# Lint check
npm run lint
```

## Project Structure

```
frontend/
├── app/                   # Next.js App Router
│   ├── page.tsx          # Main entry (Mission Control)
│   ├── layout.tsx        # Root layout
│   └── globals.css       # Global styles
├── components/           # React components
│   ├── mission-control/  # Main UI components
│   ├── command/          # Command input utilities
│   └── ui/               # shadcn/ui components
├── lib/                  # Utilities
│   ├── store.ts          # Zustand state
│   ├── types.ts          # TypeScript types
│   └── hooks/            # Custom React hooks
└── public/               # Static assets
    └── favicon.ico
```

## Environment

No environment variables needed for frontend. Backend URL is hardcoded to `http://localhost:8000` for development.

---

**Version**: 2.0 - Mission Control
**Last Updated**: February 5, 2026
