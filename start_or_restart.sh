#!/usr/bin/env bash

################################################################################
# commander.ai - Comprehensive Start/Restart Script
################################################################################
# This script handles the complete startup of the commander.ai application:
# - Docker services (PostgreSQL, Redis, Qdrant)
# - Environment validation
# - Database migrations
# - Backend API (FastAPI/uvicorn)
# - Frontend (Next.js)
# - Browser auto-launch
################################################################################

set -e  # Exit on error

# Color codes for better UX
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Log directories
LOGS_DIR="$SCRIPT_DIR/logs"
BACKEND_LOG="$LOGS_DIR/backend.log"
FRONTEND_LOG="$LOGS_DIR/frontend.log"

# PID tracking
BACKEND_PID_FILE="$LOGS_DIR/backend.pid"
FRONTEND_PID_FILE="$LOGS_DIR/frontend.pid"

################################################################################
# Helper Functions
################################################################################

print_header() {
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}  $1${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Create logs directory if it doesn't exist
mkdir -p "$LOGS_DIR"

################################################################################
# 1. Docker Service Management
################################################################################

print_header "Step 1: Docker Services Check"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running!"
    echo ""
    echo "Please start Docker Desktop and try again."
    echo "  macOS: Open Docker Desktop application"
    echo "  Linux: sudo systemctl start docker"
    exit 1
fi
print_success "Docker daemon is running"

# Check if docker-compose.yml exists
if [ ! -f "docker-compose.yml" ]; then
    print_error "docker-compose.yml not found in $SCRIPT_DIR"
    exit 1
fi

# Start or restart Docker Compose services
print_info "Starting Docker Compose services (postgres, redis, qdrant)..."
docker-compose up -d

# Wait for services to be healthy
print_info "Waiting for services to be ready..."
sleep 5

# Check if containers are running
if docker-compose ps | grep -q "Up"; then
    print_success "Docker services are running"
    docker-compose ps
else
    print_error "Failed to start Docker services"
    docker-compose ps
    exit 1
fi

################################################################################
# 2. Environment Setup
################################################################################

print_header "Step 2: Environment Configuration"

ENV_FILE="backend/.env"
ENV_EXAMPLE="backend/.env.example"

if [ ! -f "$ENV_FILE" ]; then
    print_warning ".env file not found!"

    if [ -f "$ENV_EXAMPLE" ]; then
        print_info "Copying .env.example to .env..."
        cp "$ENV_EXAMPLE" "$ENV_FILE"
        print_warning "Please edit backend/.env and add your API keys:"
        echo "  - OPENAI_API_KEY"
        echo "  - ANTHROPIC_API_KEY (optional)"
        echo "  - TAVILY_API_KEY (optional)"
        echo ""
        read -p "Press Enter after configuring .env, or Ctrl+C to exit..."
    else
        print_error ".env.example not found. Cannot proceed."
        exit 1
    fi
fi
print_success "Environment file exists: $ENV_FILE"

# Basic validation - check for required vars
if ! grep -q "DATABASE_URL" "$ENV_FILE"; then
    print_warning "DATABASE_URL not found in .env"
fi

if ! grep -q "OPENAI_API_KEY" "$ENV_FILE"; then
    print_warning "OPENAI_API_KEY not found in .env (may be required for agents)"
fi

################################################################################
# 3. Database Setup
################################################################################

print_header "Step 3: Database Migrations"

# Check if alembic is available
if command -v alembic &> /dev/null; then
    print_info "Running database migrations..."
    if alembic upgrade head; then
        print_success "Database migrations applied successfully"
    else
        print_error "Failed to run migrations"
        echo "Try running manually: alembic upgrade head"
        exit 1
    fi
else
    print_warning "Alembic not found. Skipping migrations."
    print_info "Install with: pip install alembic"
fi

################################################################################
# 4. Backend Startup
################################################################################

print_header "Step 4: Backend API (FastAPI)"

# Kill existing backend process if running
if [ -f "$BACKEND_PID_FILE" ]; then
    OLD_PID=$(cat "$BACKEND_PID_FILE")
    if ps -p "$OLD_PID" > /dev/null 2>&1; then
        print_info "Stopping existing backend process (PID: $OLD_PID)..."
        kill "$OLD_PID" 2>/dev/null || true
        sleep 2
    fi
    rm -f "$BACKEND_PID_FILE"
fi

# Also check for any uvicorn processes on port 8000
if lsof -ti:8000 > /dev/null 2>&1; then
    print_info "Killing process on port 8000..."
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true
    sleep 1
fi

# Start backend
print_info "Starting backend server..."
> "$BACKEND_LOG"  # Clear previous log

# Check if uvicorn is available
if command -v uvicorn &> /dev/null; then
    nohup uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8000 > "$BACKEND_LOG" 2>&1 &
    BACKEND_PID=$!
    echo "$BACKEND_PID" > "$BACKEND_PID_FILE"

    # Wait for backend to start
    print_info "Waiting for backend to start (PID: $BACKEND_PID)..."
    sleep 3

    # Check if backend is responding
    if curl -s http://localhost:8000/health > /dev/null 2>&1 || \
       curl -s http://localhost:8000/ > /dev/null 2>&1; then
        print_success "Backend API is running on http://localhost:8000"
    else
        print_warning "Backend started but not responding yet (check logs)"
        print_info "Log: $BACKEND_LOG"
    fi
else
    print_error "uvicorn not found!"
    print_info "Install with: pip install uvicorn"
    exit 1
fi

################################################################################
# 5. Frontend Startup
################################################################################

print_header "Step 5: Frontend (Next.js)"

# Check if frontend directory exists
if [ ! -d "frontend" ]; then
    print_error "frontend/ directory not found"
    exit 1
fi

cd frontend

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    print_info "node_modules not found. Running npm install..."
    if command -v npm &> /dev/null; then
        npm install
    else
        print_error "npm not found! Please install Node.js."
        exit 1
    fi
fi
print_success "Frontend dependencies installed"

# Kill existing frontend process if running
cd "$SCRIPT_DIR"
if [ -f "$FRONTEND_PID_FILE" ]; then
    OLD_PID=$(cat "$FRONTEND_PID_FILE")
    if ps -p "$OLD_PID" > /dev/null 2>&1; then
        print_info "Stopping existing frontend process (PID: $OLD_PID)..."
        kill "$OLD_PID" 2>/dev/null || true
        sleep 2
    fi
    rm -f "$FRONTEND_PID_FILE"
fi

# Also check for any process on port 3000
if lsof -ti:3000 > /dev/null 2>&1; then
    print_info "Killing process on port 3000..."
    lsof -ti:3000 | xargs kill -9 2>/dev/null || true
    sleep 1
fi

# Start frontend
print_info "Starting frontend development server..."
> "$FRONTEND_LOG"  # Clear previous log

cd frontend
nohup npm run dev > "$FRONTEND_LOG" 2>&1 &
FRONTEND_PID=$!
echo "$FRONTEND_PID" > "$FRONTEND_PID_FILE"

cd "$SCRIPT_DIR"

# Wait for frontend to start
print_info "Waiting for frontend to start (PID: $FRONTEND_PID)..."
sleep 5

# Check if frontend is responding
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    print_success "Frontend is running on http://localhost:3000"
else
    print_warning "Frontend started but not responding yet (check logs)"
    print_info "Log: $FRONTEND_LOG"
fi

################################################################################
# 6. Status Report & Browser Launch
################################################################################

print_header "Startup Complete!"

echo ""
print_success "All services are running:"
echo ""
echo -e "${GREEN}Backend API:${NC}      http://localhost:8000"
echo -e "${GREEN}API Documentation:${NC} http://localhost:8000/docs"
echo -e "${GREEN}Frontend UI:${NC}      http://localhost:3000"
echo ""
echo -e "${BLUE}Docker Services:${NC}"
docker-compose ps | tail -n +2 | awk '{print "  - " $1 ": " $4}'
echo ""
echo -e "${BLUE}Process Information:${NC}"
echo "  - Backend PID:  $(cat $BACKEND_PID_FILE 2>/dev/null || echo 'N/A')"
echo "  - Frontend PID: $(cat $FRONTEND_PID_FILE 2>/dev/null || echo 'N/A')"
echo ""
echo -e "${BLUE}Logs:${NC}"
echo "  - Backend:  $BACKEND_LOG"
echo "  - Frontend: $FRONTEND_LOG"
echo ""
print_info "Monitor logs with: tail -f logs/*.log"
echo ""

# Auto-open browser
print_info "Opening browser to http://localhost:3000..."
sleep 2

# Cross-platform browser opening
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    open http://localhost:3000
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    if command -v xdg-open &> /dev/null; then
        xdg-open http://localhost:3000
    elif command -v wslview &> /dev/null; then
        # WSL
        wslview http://localhost:3000
    else
        print_warning "Could not auto-open browser. Please visit: http://localhost:3000"
    fi
else
    print_warning "Unknown OS. Please manually open: http://localhost:3000"
fi

echo ""
print_success "commander.ai is ready! 🚀"
echo ""
print_info "To stop services:"
echo "  - Press Ctrl+C (if running in foreground)"
echo "  - Or run: kill \$(cat logs/*.pid) && docker-compose down"
echo ""
