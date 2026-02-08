#!/usr/bin/env bash

################################################################################
# commander.ai - Clean Shutdown Script
################################################################################
# This script handles the graceful shutdown of the commander.ai application:
# - Frontend (Next.js) shutdown
# - Backend API (FastAPI/uvicorn) shutdown
# - Docker services (PostgreSQL, Redis, Qdrant) shutdown
# - PID file cleanup
# - Log archiving (optional)
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

################################################################################
# Shutdown Banner
################################################################################

print_header "commander.ai - Clean Shutdown"
echo ""
print_info "Gracefully shutting down all services..."
echo ""

################################################################################
# 1. Frontend Shutdown
################################################################################

print_header "Step 1: Stopping Frontend (Next.js)"

FRONTEND_STOPPED=false

# Check PID file
if [ -f "$FRONTEND_PID_FILE" ]; then
    FRONTEND_PID=$(cat "$FRONTEND_PID_FILE")
    if ps -p "$FRONTEND_PID" > /dev/null 2>&1; then
        print_info "Stopping frontend process (PID: $FRONTEND_PID)..."
        kill "$FRONTEND_PID" 2>/dev/null || true
        sleep 2

        # Force kill if still running
        if ps -p "$FRONTEND_PID" > /dev/null 2>&1; then
            print_warning "Process still running, force killing..."
            kill -9 "$FRONTEND_PID" 2>/dev/null || true
            sleep 1
        fi

        print_success "Frontend process stopped"
        FRONTEND_STOPPED=true
    else
        print_warning "Frontend PID file exists but process not running"
    fi
    rm -f "$FRONTEND_PID_FILE"
else
    print_info "No frontend PID file found"
fi

# Check for any remaining processes on port 3000
if lsof -ti:3000 > /dev/null 2>&1; then
    print_info "Killing remaining process on port 3000..."
    lsof -ti:3000 | xargs kill -9 2>/dev/null || true
    sleep 1
    print_success "Port 3000 cleared"
    FRONTEND_STOPPED=true
fi

if [ "$FRONTEND_STOPPED" = false ]; then
    print_info "Frontend was not running"
fi

################################################################################
# 2. Backend Shutdown
################################################################################

print_header "Step 2: Stopping Backend API (FastAPI)"

BACKEND_STOPPED=false

# Check PID file
if [ -f "$BACKEND_PID_FILE" ]; then
    BACKEND_PID=$(cat "$BACKEND_PID_FILE")
    if ps -p "$BACKEND_PID" > /dev/null 2>&1; then
        print_info "Stopping backend process (PID: $BACKEND_PID)..."
        kill "$BACKEND_PID" 2>/dev/null || true
        sleep 2

        # Force kill if still running
        if ps -p "$BACKEND_PID" > /dev/null 2>&1; then
            print_warning "Process still running, force killing..."
            kill -9 "$BACKEND_PID" 2>/dev/null || true
            sleep 1
        fi

        print_success "Backend process stopped"
        BACKEND_STOPPED=true
    else
        print_warning "Backend PID file exists but process not running"
    fi
    rm -f "$BACKEND_PID_FILE"
else
    print_info "No backend PID file found"
fi

# Check for any remaining uvicorn processes on port 8000
if lsof -ti:8000 > /dev/null 2>&1; then
    print_info "Killing remaining process on port 8000..."
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true
    sleep 1
    print_success "Port 8000 cleared"
    BACKEND_STOPPED=true
fi

if [ "$BACKEND_STOPPED" = false ]; then
    print_info "Backend was not running"
fi

################################################################################
# 3. Docker Services Shutdown
################################################################################

print_header "Step 3: Stopping Docker Services"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_warning "Docker is not running (already stopped)"
else
    # Check if docker-compose.yml exists
    if [ ! -f "docker-compose.yml" ]; then
        print_warning "docker-compose.yml not found, skipping Docker shutdown"
    else
        # Show current status
        print_info "Current Docker services:"
        docker-compose ps 2>/dev/null || true
        echo ""

        # Stop and remove containers
        print_info "Stopping Docker Compose services..."
        docker-compose down

        print_success "Docker services stopped"

        # Optional: Show remaining containers (if any)
        REMAINING=$(docker-compose ps -q 2>/dev/null | wc -l | tr -d ' ')
        if [ "$REMAINING" -gt 0 ]; then
            print_warning "Some containers still running:"
            docker-compose ps
        fi
    fi
fi

################################################################################
# 4. Cleanup & Verification
################################################################################

print_header "Step 4: Cleanup & Verification"

# Remove PID files
if [ -f "$BACKEND_PID_FILE" ] || [ -f "$FRONTEND_PID_FILE" ]; then
    print_info "Removing PID files..."
    rm -f "$BACKEND_PID_FILE" "$FRONTEND_PID_FILE"
    print_success "PID files cleaned"
fi

# Verify ports are free
echo ""
print_info "Verifying ports are free..."
PORT_3000_FREE=true
PORT_8000_FREE=true

if lsof -ti:3000 > /dev/null 2>&1; then
    print_error "Port 3000 still in use!"
    PORT_3000_FREE=false
else
    print_success "Port 3000 is free"
fi

if lsof -ti:8000 > /dev/null 2>&1; then
    print_error "Port 8000 still in use!"
    PORT_8000_FREE=false
else
    print_success "Port 8000 is free"
fi

################################################################################
# 5. Optional: Archive Logs
################################################################################

if [ -f "$BACKEND_LOG" ] || [ -f "$FRONTEND_LOG" ]; then
    echo ""
    print_info "Log files are available at:"
    [ -f "$BACKEND_LOG" ] && echo "  - Backend:  $BACKEND_LOG"
    [ -f "$FRONTEND_LOG" ] && echo "  - Frontend: $FRONTEND_LOG"
    echo ""

    # Prompt to archive logs
    read -p "Archive logs to logs/archive/? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        ARCHIVE_DIR="$LOGS_DIR/archive"
        mkdir -p "$ARCHIVE_DIR"
        TIMESTAMP=$(date +%Y%m%d_%H%M%S)

        if [ -f "$BACKEND_LOG" ]; then
            cp "$BACKEND_LOG" "$ARCHIVE_DIR/backend_${TIMESTAMP}.log"
            print_success "Backend log archived"
        fi

        if [ -f "$FRONTEND_LOG" ]; then
            cp "$FRONTEND_LOG" "$ARCHIVE_DIR/frontend_${TIMESTAMP}.log"
            print_success "Frontend log archived"
        fi

        print_info "Logs archived to: $ARCHIVE_DIR"
    fi
fi

################################################################################
# 6. Shutdown Complete
################################################################################

echo ""
print_header "Shutdown Complete!"

echo ""
print_success "All services have been stopped:"
echo ""
echo -e "${GREEN}✓${NC} Frontend (Next.js)     - Port 3000 free"
echo -e "${GREEN}✓${NC} Backend API (FastAPI)  - Port 8000 free"
echo -e "${GREEN}✓${NC} Docker services        - Containers stopped"
echo -e "${GREEN}✓${NC} PID files              - Cleaned up"
echo ""

if [ "$PORT_3000_FREE" = true ] && [ "$PORT_8000_FREE" = true ]; then
    print_success "System is ready for restart! 🛑"
    echo ""
    print_info "To start again, run: ./start_or_restart.sh"
else
    print_error "Some ports are still in use!"
    echo ""
    print_info "Check processes manually:"
    echo "  - Port 3000: lsof -i :3000"
    echo "  - Port 8000: lsof -i :8000"
fi

echo ""
