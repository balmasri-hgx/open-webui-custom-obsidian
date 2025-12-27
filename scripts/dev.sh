#!/bin/bash
# ===========================================
# Obsidian Development Mode
# Hot reload for ALL files - no rebuilding!
# ===========================================

echo "🔮 Starting Obsidian Development Environment..."
echo ""

# Colors
PURPLE='\033[0;35m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if ollama container is running
if ! docker ps | grep -q ollama; then
    echo -e "${YELLOW}Starting Ollama container...${NC}"
    docker compose up -d ollama
    sleep 2
fi

echo -e "${GREEN}✓ Ollama is running${NC}"

# Check if backend is needed
if ! curl -s http://localhost:8080/health > /dev/null 2>&1; then
    echo -e "${YELLOW}Starting backend...${NC}"
    echo "  Run in a separate terminal:"
    echo -e "  ${PURPLE}cd backend && ./start.sh${NC}"
    echo ""
    echo "  Or use the production backend:"
    echo -e "  ${PURPLE}docker compose up -d open-webui${NC}"
    echo ""
fi

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}Installing dependencies...${NC}"
    npm install --legacy-peer-deps
fi

echo ""
echo -e "${PURPLE}═══════════════════════════════════════════${NC}"
echo -e "${PURPLE}  Starting Vite Dev Server (Hot Reload)    ${NC}"
echo -e "${PURPLE}═══════════════════════════════════════════${NC}"
echo ""
echo "  Edit ANY file and see changes instantly:"
echo "  • src/**/*.svelte  - Components"
echo "  • src/**/*.ts      - TypeScript"
echo "  • static/**/*      - Static assets"
echo "  • src/app.html     - HTML template"
echo ""
echo -e "  Open: ${GREEN}http://localhost:5173${NC}"
echo ""

# Start Vite dev server
npm run dev

