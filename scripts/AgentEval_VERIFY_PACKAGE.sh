#!/bin/bash

# Package Verification Script
# Verifies the AgentEval package contents

echo "=================================="
echo "AgentEval Package Verification"
echo "=================================="
echo ""

PACKAGE="/home/shared/zqq/AgentEval_milestone2_20251029_051458.tar.gz"

if [ ! -f "$PACKAGE" ]; then
    echo "ERROR: Package not found: $PACKAGE"
    exit 1
fi

echo "Package found: $(basename $PACKAGE)"
echo "Package size: $(du -h $PACKAGE | cut -f1)"
echo ""

echo "Checking key components..."
echo ""

# Check core components
echo "1. Core Plugin System:"
tar -tzf "$PACKAGE" | grep -c "agenteval_plugin/.*\.py$" | xargs echo "   Python files:"

echo ""
echo "2. Integration Files:"
tar -tzf "$PACKAGE" | grep "integration/" | wc -l | xargs echo "   Files:"

echo ""
echo "3. Documentation:"
tar -tzf "$PACKAGE" | grep "docs/.*\.md$" | wc -l | xargs echo "   Markdown files:"

echo ""
echo "4. Examples:"
tar -tzf "$PACKAGE" | grep "examples/.*\.py$" | wc -l | xargs echo "   Example files:"

echo ""
echo "5. Tests:"
tar -tzf "$PACKAGE" | grep "tests/unit/.*\.py$" | wc -l | xargs echo "   Test files:"

echo ""
echo "6. Configuration:"
tar -tzf "$PACKAGE" | grep "config/.*\.yaml$" | wc -l | xargs echo "   Config files:"

echo ""
echo "Key Files Check:"
echo ""

# Check specific important files
IMPORTANT_FILES=(
    "./agenteval_plugin/__init__.py"
    "./integration/adeworker_plugin.py"
    "./integration/install_to_adeworker.sh"
    "./docs/ADEWORKER_INTEGRATION.md"
    "./docs/QUICK_REFERENCE.md"
    "./examples/simple_integration_example.py"
    "./tests/unit/test_plugin_manager.py"
    "./config/agenteval_plugin.yaml"
    "./setup.py"
    "./README_PLUGIN.md"
)

for file in "${IMPORTANT_FILES[@]}"; do
    if tar -tzf "$PACKAGE" | grep -q "^$file$"; then
        echo "  [OK] $file"
    else
        echo "  [MISSING] $file"
    fi
done

echo ""
echo "=================================="
echo "Verification Complete"
echo "=================================="

