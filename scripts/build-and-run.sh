#!/bin/bash
# =============================================================================
# Obsidian - Build and Run Script
# =============================================================================
# Usage: ./scripts/build-and-run.sh [options]
#
# Options:
#   --with-n8n    Include n8n workflow automation
#   --dev         Run in development mode with hot reload
#   --build-only  Build without running
#   --slim        Build slim version (smaller, no pre-downloaded models)
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Parse arguments
WITH_N8N=false
DEV_MODE=false
BUILD_ONLY=false
SLIM_BUILD=false

for arg in "$@"; do
    case $arg in
        --with-n8n)
            WITH_N8N=true
            shift
            ;;
        --dev)
            DEV_MODE=true
            shift
            ;;
        --build-only)
            BUILD_ONLY=true
            shift
            ;;
        --slim)
            SLIM_BUILD=true
            shift
            ;;
    esac
done

echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                                                               ║"
echo "║     ██████  ██████  ███████ ██ ██████  ██  █████  ███    ██   ║"
echo "║    ██    ██ ██   ██ ██      ██ ██   ██ ██ ██   ██ ████   ██   ║"
echo "║    ██    ██ ██████  ███████ ██ ██   ██ ██ ███████ ██ ██  ██   ║"
echo "║    ██    ██ ██   ██      ██ ██ ██   ██ ██ ██   ██ ██  ██ ██   ║"
echo "║     ██████  ██████  ███████ ██ ██████  ██ ██   ██ ██   ████   ║"
echo "║                                                               ║"
echo "║                   AI Chat Interface                           ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    echo "Please install Docker from https://docs.docker.com/get-docker/"
    exit 1
fi

# Check Docker Compose is available
if ! docker compose version &> /dev/null; then
    echo -e "${RED}Error: Docker Compose is not available${NC}"
    echo "Please install Docker Compose from https://docs.docker.com/compose/install/"
    exit 1
fi

# Determine which compose file to use
if [ "$DEV_MODE" = true ]; then
    COMPOSE_FILE="docker-compose.dev.yaml"
    echo -e "${YELLOW}Mode: Development (hot reload enabled)${NC}"
elif [ "$WITH_N8N" = true ]; then
    COMPOSE_FILE="docker-compose.obsidian.yaml"
    echo -e "${YELLOW}Mode: Production with n8n${NC}"
else
    COMPOSE_FILE="docker-compose.yaml"
    echo -e "${YELLOW}Mode: Production (simple stack)${NC}"
fi

# Build arguments
BUILD_ARGS=""
if [ "$SLIM_BUILD" = true ]; then
    BUILD_ARGS="--build-arg USE_SLIM=true"
    echo -e "${YELLOW}Build: Slim (no pre-downloaded models)${NC}"
fi

echo ""
echo -e "${GREEN}Building Obsidian...${NC}"
echo ""

# Build
docker compose -f "$COMPOSE_FILE" build $BUILD_ARGS

if [ "$BUILD_ONLY" = true ]; then
    echo ""
    echo -e "${GREEN}✓ Build complete!${NC}"
    exit 0
fi

echo ""
echo -e "${GREEN}Starting services...${NC}"
echo ""

# Run
docker compose -f "$COMPOSE_FILE" up -d

echo ""
echo -e "${GREEN}✓ Obsidian is running!${NC}"
echo ""
echo -e "Access the application:"
if [ "$DEV_MODE" = true ]; then
    echo -e "  ${BLUE}Frontend:${NC} http://localhost:3000"
    echo -e "  ${BLUE}Backend:${NC}  http://localhost:8080"
else
    echo -e "  ${BLUE}Obsidian:${NC} http://localhost:3000"
fi

if [ "$WITH_N8N" = true ]; then
    echo -e "  ${BLUE}n8n:${NC}      http://localhost:5678"
fi

echo -e "  ${BLUE}Ollama:${NC}   http://localhost:11434"
echo ""
echo -e "Commands:"
echo -e "  View logs:    ${YELLOW}docker compose -f $COMPOSE_FILE logs -f${NC}"
echo -e "  Stop:         ${YELLOW}docker compose -f $COMPOSE_FILE down${NC}"
echo ""

