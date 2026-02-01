# Commander.ai Frontend

Next.js 14 frontend with real-time task management Kanban board.

## Features

- 🎨 **Modern UI**: Built with Next.js 14, TypeScript, and Tailwind CSS
- 🔌 **Real-time Updates**: WebSocket connection for live task updates
- 📊 **Kanban Board**: 5-column layout (Queued, In Progress, Tool Call, Completed, Failed)
- 📈 **Progress Tracking**: Live progress bars showing agent execution status
- 🤝 **Consultation Indicators**: Visual indicators when agents consult each other
- 🎭 **shadcn/ui Components**: Professional, accessible UI components

## Getting Started

### Development

\`\`\`bash
# Install dependencies
npm install

# Start development server
npm run dev
\`\`\`

Open [http://localhost:3000](http://localhost:3000) to view the Kanban board.

### Prerequisites

- Node.js 18+ installed
- Backend server running on http://localhost:8000

## Configuration

MVP User ID: \`00000000-0000-0000-0000-000000000001\`

Backend endpoints:
- API: \`http://localhost:8000\`
- WebSocket: \`ws://localhost:8000/ws/{user_id}\`
