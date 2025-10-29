#!/bin/bash

# ADEWorker AgentEval Plugin Installation Script
# This script installs the AgentEval plugin into ADEWorker

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Paths
AGENTEVAL_PATH="${AGENTEVAL_PATH:-/home/shared/zqq/AgentEval}"
ADEWORKER_PATH="${ADEWORKER_PATH:-/home/shared/zqq/adeworker}"

echo "========================================"
echo "AgentEval Plugin Installation"
echo "========================================"
echo ""

# Check paths
echo "Checking paths..."
if [ ! -d "$AGENTEVAL_PATH" ]; then
    echo -e "${RED}Error: AgentEval directory not found at $AGENTEVAL_PATH${NC}"
    exit 1
fi

if [ ! -d "$ADEWORKER_PATH" ]; then
    echo -e "${RED}Error: ADEWorker directory not found at $ADEWORKER_PATH${NC}"
    exit 1
fi

echo -e "${GREEN}Paths verified${NC}"
echo ""

# Step 1: Install AgentEval package
echo "Step 1: Installing AgentEval package..."
cd "$AGENTEVAL_PATH"
pip install -e . > /dev/null 2>&1
pip install aiohttp pyyaml pydantic > /dev/null 2>&1
echo -e "${GREEN}Package installed${NC}"
echo ""

# Step 2: Create plugins directory
echo "Step 2: Creating plugins directory..."
mkdir -p "$ADEWORKER_PATH/backend/worker/agent/plugins"
touch "$ADEWORKER_PATH/backend/worker/agent/plugins/__init__.py"
echo -e "${GREEN}Plugins directory created${NC}"
echo ""

# Step 3: Copy integration module
echo "Step 3: Copying integration module..."
cp "$AGENTEVAL_PATH/integration/adeworker_plugin.py" \
   "$ADEWORKER_PATH/backend/worker/agent/plugins/agenteval_plugin.py"
echo -e "${GREEN}Integration module copied${NC}"
echo ""

# Step 4: Copy configuration
echo "Step 4: Setting up configuration..."
mkdir -p "$ADEWORKER_PATH/config"
if [ -f "$ADEWORKER_PATH/config/agenteval_plugin.yaml" ]; then
    echo -e "${YELLOW}Config file already exists, backing up...${NC}"
    cp "$ADEWORKER_PATH/config/agenteval_plugin.yaml" \
       "$ADEWORKER_PATH/config/agenteval_plugin.yaml.backup"
fi
cp "$AGENTEVAL_PATH/config/agenteval_plugin.yaml" \
   "$ADEWORKER_PATH/config/agenteval_plugin.yaml"
echo -e "${GREEN}Configuration copied${NC}"
echo ""

# Step 5: Set environment variables
echo "Step 5: Setting up environment variables..."
ENV_FILE="$ADEWORKER_PATH/.env"

if [ ! -f "$ENV_FILE" ]; then
    echo "# AgentEval Configuration" > "$ENV_FILE"
    echo "AGENTEVAL_PATH=$AGENTEVAL_PATH" >> "$ENV_FILE"
    echo "AGENTEVAL_API_KEY=your_api_key_here" >> "$ENV_FILE"
    echo "AGENTEVAL_ENABLED=true" >> "$ENV_FILE"
    echo -e "${GREEN}.env file created${NC}"
else
    if ! grep -q "AGENTEVAL_PATH" "$ENV_FILE"; then
        echo "" >> "$ENV_FILE"
        echo "# AgentEval Configuration" >> "$ENV_FILE"
        echo "AGENTEVAL_PATH=$AGENTEVAL_PATH" >> "$ENV_FILE"
        echo "AGENTEVAL_API_KEY=your_api_key_here" >> "$ENV_FILE"
        echo "AGENTEVAL_ENABLED=true" >> "$ENV_FILE"
        echo -e "${GREEN}Environment variables added to .env${NC}"
    else
        echo -e "${YELLOW}Environment variables already exist in .env${NC}"
    fi
fi
echo ""

# Step 6: Verify installation
echo "Step 6: Verifying installation..."
cd "$ADEWORKER_PATH"
if python -c "from worker.agent.plugins.agenteval_plugin import init_agenteval" 2>/dev/null; then
    echo -e "${GREEN}Verification successful${NC}"
else
    echo -e "${RED}Verification failed - check Python path${NC}"
    exit 1
fi
echo ""

# Success message
echo "========================================"
echo -e "${GREEN}Installation Complete!${NC}"
echo "========================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Edit configuration file:"
echo "   vi $ADEWORKER_PATH/config/agenteval_plugin.yaml"
echo ""
echo "2. Set your API key:"
echo "   export AGENTEVAL_API_KEY='your_api_key'"
echo "   # Or edit $ADEWORKER_PATH/.env"
echo ""
echo "3. Add to your startup code:"
echo "   from worker.agent.plugins.agenteval_plugin import init_agenteval"
echo "   init_agenteval(config_path='config/agenteval_plugin.yaml')"
echo ""
echo "4. Add decorators to your agent:"
echo "   from worker.agent.plugins.agenteval_plugin import instrument_agent, instrument_node"
echo "   "
echo "   @instrument_agent(agent_type='DevAgent', agent_version='1.0.0')"
echo "   async def arun(self, user_input):"
echo "       ..."
echo ""
echo "5. Restart ADEWorker and verify:"
echo "   tail -f /var/log/agenteval/plugin.log"
echo ""
echo "For detailed instructions, see:"
echo "$AGENTEVAL_PATH/docs/ADEWORKER_INTEGRATION.md"
echo ""
