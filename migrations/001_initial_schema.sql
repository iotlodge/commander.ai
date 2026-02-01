-- Initial database schema for commander.ai
-- Requires pgvector extension

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Agents table
CREATE TABLE IF NOT EXISTS agents (
    id VARCHAR(50) PRIMARY KEY,  -- e.g., 'agent_a', 'agent_b'
    nickname VARCHAR(50) UNIQUE NOT NULL,  -- e.g., 'bob', 'sue'
    specialization TEXT NOT NULL,
    description TEXT,
    avatar_url TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Conversation history table
CREATE TABLE IF NOT EXISTS conversation_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    agent_id VARCHAR(50) NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    thread_id UUID NOT NULL,  -- Groups related conversations
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Agent memories (long-term learnings)
CREATE TABLE IF NOT EXISTS agent_memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id VARCHAR(50) NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,  -- NULL for shared memories
    memory_type VARCHAR(50) NOT NULL CHECK (memory_type IN ('episodic', 'semantic', 'procedural')),
    content TEXT NOT NULL,
    embedding vector(1536),  -- OpenAI ada-002 embeddings
    importance_score FLOAT DEFAULT 0.5 CHECK (importance_score >= 0 AND importance_score <= 1),
    access_count INTEGER DEFAULT 0,
    last_accessed_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Agent consultations (agent-to-agent interactions)
CREATE TABLE IF NOT EXISTS agent_consultations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    requesting_agent_id VARCHAR(50) NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    target_agent_id VARCHAR(50) NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    thread_id UUID NOT NULL,
    consultation_query TEXT NOT NULL,
    consultation_response TEXT,
    consultation_context JSONB DEFAULT '{}',
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'failed')),
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_ms INTEGER
);

-- Agent state snapshots (LangGraph checkpoints)
CREATE TABLE IF NOT EXISTS agent_state_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id VARCHAR(50) NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    thread_id UUID NOT NULL,
    checkpoint_id VARCHAR(255) NOT NULL UNIQUE,
    state_data JSONB NOT NULL,
    node_name VARCHAR(100),  -- Current graph node
    parent_checkpoint_id VARCHAR(255),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Agent tasks (for Kanban tracking)
CREATE TABLE IF NOT EXISTS agent_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    agent_id VARCHAR(50) NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    thread_id UUID NOT NULL,
    command_text TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'queued' CHECK (status IN ('queued', 'in_progress', 'tool_call', 'completed', 'failed')),
    progress_percentage INTEGER DEFAULT 0 CHECK (progress_percentage >= 0 AND progress_percentage <= 100),
    current_node VARCHAR(100),
    consultation_target_id VARCHAR(50) REFERENCES agents(id),  -- Non-null when in tool_call status
    result TEXT,
    error_message TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Insert default agents
INSERT INTO agents (id, nickname, specialization, description) VALUES
    ('parent', 'leo', 'Orchestrator', 'Coordinates complex multi-step tasks and delegates to specialist agents'),
    ('agent_a', 'bob', 'Research Specialist', 'Conducts research, synthesis, and information gathering'),
    ('agent_b', 'sue', 'Compliance Specialist', 'Reviews for regulatory compliance and policy adherence'),
    ('agent_c', 'rex', 'Data Analyst', 'Performs data analysis, visualization, and statistical insights')
ON CONFLICT (id) DO NOTHING;

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for users table
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create indexes for conversation_history
CREATE INDEX IF NOT EXISTS idx_thread_id ON conversation_history(thread_id);
CREATE INDEX IF NOT EXISTS idx_user_agent ON conversation_history(user_id, agent_id);
CREATE INDEX IF NOT EXISTS idx_created_at ON conversation_history(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_conversation_thread_created ON conversation_history(thread_id, created_at DESC);

-- Create indexes for agent_memories
CREATE INDEX IF NOT EXISTS idx_agent_memories ON agent_memories(agent_id, user_id);
CREATE INDEX IF NOT EXISTS idx_memory_type ON agent_memories(memory_type);
CREATE INDEX IF NOT EXISTS idx_importance ON agent_memories(importance_score DESC);
CREATE INDEX IF NOT EXISTS idx_memories_agent_user ON agent_memories(agent_id, user_id) WHERE user_id IS NOT NULL;

-- Create index for vector similarity search
CREATE INDEX IF NOT EXISTS idx_agent_memories_embedding ON agent_memories
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- Create indexes for agent_consultations
CREATE INDEX IF NOT EXISTS idx_consultations_thread ON agent_consultations(thread_id);
CREATE INDEX IF NOT EXISTS idx_requesting_agent ON agent_consultations(requesting_agent_id);
CREATE INDEX IF NOT EXISTS idx_target_agent ON agent_consultations(target_agent_id);
CREATE INDEX IF NOT EXISTS idx_status ON agent_consultations(status);
CREATE INDEX IF NOT EXISTS idx_consultations_requesting_target ON agent_consultations(requesting_agent_id, target_agent_id);

-- Create indexes for agent_state_snapshots
CREATE INDEX IF NOT EXISTS idx_checkpoint ON agent_state_snapshots(checkpoint_id);
CREATE INDEX IF NOT EXISTS idx_thread_snapshots ON agent_state_snapshots(thread_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_agent_checkpoints ON agent_state_snapshots(agent_id, user_id);

-- Create indexes for agent_tasks
CREATE INDEX IF NOT EXISTS idx_user_tasks ON agent_tasks(user_id, status);
CREATE INDEX IF NOT EXISTS idx_agent_tasks ON agent_tasks(agent_id, status);
CREATE INDEX IF NOT EXISTS idx_thread_tasks ON agent_tasks(thread_id);
CREATE INDEX IF NOT EXISTS idx_status_created ON agent_tasks(status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_tasks_user_status_created ON agent_tasks(user_id, status, created_at DESC);
