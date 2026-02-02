# Contributing to commander.ai

Thank you for your interest in contributing to commander.ai! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Coding Standards](#coding-standards)
- [Commit Message Guidelines](#commit-message-guidelines)
- [Pull Request Process](#pull-request-process)
- [Testing](#testing)
- [Questions or Need Help?](#questions-or-need-help)

## Code of Conduct

We are committed to providing a welcoming and inclusive environment. Please be respectful and constructive in all interactions.

**Expected Behavior:**
- Be respectful and considerate
- Welcome newcomers and help them get started
- Focus on what's best for the project and community
- Show empathy towards other community members

**Unacceptable Behavior:**
- Harassment, trolling, or discriminatory language
- Personal attacks or inflammatory comments
- Publishing others' private information
- Other conduct that would be inappropriate in a professional setting

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/commander.ai.git
   cd commander.ai
   ```
3. **Add upstream remote**:
   ```bash
   git remote add upstream https://github.com/iotlodge/commander.ai.git
   ```

## Development Setup

### Prerequisites

- Python 3.12+
- Node.js 18+
- Docker Desktop (for PostgreSQL, Redis, Qdrant)
- Git

### Quick Start

Use the automated startup script:

```bash
./start_or_restart.sh
```

This will:
- Start Docker services (PostgreSQL, Redis, Qdrant)
- Set up environment variables (creates `.env` from example)
- Run database migrations
- Start backend (port 8000) and frontend (port 3000)
- Open browser to http://localhost:3000

### Manual Setup

If you prefer manual setup:

1. **Start infrastructure**:
   ```bash
   docker-compose up -d
   ```

2. **Set up environment**:
   ```bash
   cp backend/.env.example backend/.env
   # Edit backend/.env and add your API keys
   ```

3. **Install Python dependencies**:
   ```bash
   uv sync
   # or: pip install -r requirements.txt
   ```

4. **Run database migrations**:
   ```bash
   alembic upgrade head
   ```

5. **Start backend**:
   ```bash
   uvicorn backend.api.main:app --reload
   ```

6. **Install frontend dependencies**:
   ```bash
   cd frontend
   npm install
   ```

7. **Start frontend**:
   ```bash
   npm run dev
   ```

## How to Contribute

### Reporting Bugs

Before creating a bug report:
- Check existing issues to avoid duplicates
- Try the latest version to see if the issue persists

When creating a bug report, include:
- Clear, descriptive title
- Steps to reproduce the issue
- Expected vs. actual behavior
- Screenshots or error messages (if applicable)
- Environment details (OS, Python version, Node version)

### Suggesting Enhancements

Enhancement suggestions are welcome! Please include:
- Clear description of the proposed feature
- Use cases and benefits
- Any implementation ideas (optional)
- Mockups or examples (if UI-related)

### Contributing Code

1. **Check existing issues** - Look for issues labeled `good first issue` or `help wanted`
2. **Discuss first** - For major changes, open an issue to discuss your approach
3. **Create a branch** - Use a descriptive branch name:
   ```bash
   git checkout -b feature/add-agent-memory
   git checkout -b fix/websocket-reconnection
   git checkout -b docs/update-api-guide
   ```
4. **Make your changes** - Follow the coding standards below
5. **Test your changes** - Ensure tests pass and add new tests if needed
6. **Commit your changes** - Follow commit message guidelines
7. **Push to your fork**:
   ```bash
   git push origin feature/add-agent-memory
   ```
8. **Open a Pull Request** - Use the PR template and link related issues

## Coding Standards

### Python (Backend)

**Style Guide:**
- Follow [PEP 8](https://pep8.org/)
- Use [Black](https://black.readthedocs.io/) for formatting (line length: 100)
- Use [Ruff](https://docs.astral.sh/ruff/) for linting

**Type Hints:**
- Use type hints for all function signatures
- Use Pydantic models for data validation

**Example:**
```python
from typing import Optional
from uuid import UUID

async def get_task(task_id: UUID, user_id: Optional[UUID] = None) -> AgentTask:
    """Retrieve a task by ID.

    Args:
        task_id: The unique task identifier
        user_id: Optional user ID for access control

    Returns:
        The requested AgentTask

    Raises:
        TaskNotFoundError: If task doesn't exist
    """
    # Implementation
```

**Run checks:**
```bash
# Format code
black backend/

# Lint code
ruff check backend/

# Type check
mypy backend/ --strict
```

### TypeScript/React (Frontend)

**Style Guide:**
- Use TypeScript for all files
- Follow React best practices
- Use functional components and hooks
- Prefer named exports over default exports

**Component Structure:**
```typescript
// components/example-component.tsx
import { FC } from 'react'

interface ExampleComponentProps {
  title: string
  count: number
  onUpdate?: (value: number) => void
}

export const ExampleComponent: FC<ExampleComponentProps> = ({
  title,
  count,
  onUpdate
}) => {
  // Implementation
}
```

**Run checks:**
```bash
cd frontend

# Type check
npm run type-check

# Lint
npm run lint

# Format
npm run format
```

### Database Migrations

When modifying database schema:

1. Create a migration:
   ```bash
   alembic revision --autogenerate -m "Add agent_memory table"
   ```

2. Review the generated migration file carefully
3. Test both upgrade and downgrade:
   ```bash
   alembic upgrade head
   alembic downgrade -1
   alembic upgrade head
   ```

## Commit Message Guidelines

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

**Format:**
```
<type>: <description>

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, no logic change)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks, dependency updates

**Examples:**
```
feat: Add agent memory persistence with Redis

fix: Resolve WebSocket reconnection issue on network drop

docs: Update README with deployment instructions

refactor: Extract command parser into separate module
```

**Good practices:**
- Use imperative mood ("Add feature" not "Added feature")
- Keep subject line under 72 characters
- Separate subject from body with blank line
- Explain *what* and *why* in the body, not *how*

## Pull Request Process

1. **Update documentation** - If you changed APIs or added features
2. **Add tests** - Ensure your code is tested
3. **Update CHANGELOG** - Add your changes to the unreleased section (if exists)
4. **Ensure CI passes** - All tests and checks must pass
5. **Request review** - Tag relevant maintainers
6. **Address feedback** - Respond to review comments
7. **Squash commits** - Clean up your commit history if requested
8. **Wait for merge** - Maintainers will merge when ready

**PR Title Format:**
```
feat: Add real-time agent status indicators
fix: Resolve task deletion race condition
docs: Add agent architecture diagram
```

**PR Description Template:**
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing completed

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex logic
- [ ] Documentation updated
- [ ] No new warnings generated
- [ ] Tests pass locally

## Screenshots (if applicable)
Add screenshots for UI changes

## Related Issues
Closes #123
```

## Testing

### Backend Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_agents.py

# Run with coverage
pytest --cov=backend --cov-report=html
```

### Frontend Tests

```bash
cd frontend

# Run all tests
npm test

# Run in watch mode
npm test -- --watch

# Run with coverage
npm test -- --coverage
```

### Integration Tests

```bash
# Ensure services are running
./start_or_restart.sh

# Run integration tests
pytest tests/integration/
```

## Project Structure

```
commander.ai/
├── backend/              # Python FastAPI backend
│   ├── agents/          # Agent implementations
│   ├── api/             # REST API and WebSocket
│   ├── core/            # Business logic
│   ├── models/          # Pydantic models
│   └── repositories/    # Database access layer
├── frontend/            # Next.js frontend
│   ├── app/            # Next.js App Router
│   ├── components/     # React components
│   ├── hooks/          # Custom React hooks
│   └── lib/            # Utilities and state
├── migrations/         # Database migrations
└── tests/             # Test files
```

## Questions or Need Help?

- **General questions**: Open a [Discussion](https://github.com/iotlodge/commander.ai/discussions)
- **Bug reports**: Open an [Issue](https://github.com/iotlodge/commander.ai/issues)
- **Security issues**: Email [security contact] instead of opening a public issue

## Recognition

Contributors will be recognized in:
- The project README
- Release notes for significant contributions
- The GitHub contributors page

Thank you for contributing to commander.ai! 🚀
