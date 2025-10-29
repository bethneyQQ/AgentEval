# AgentEval Integration for ADEWorker

This directory contains integration files for connecting ADEWorker with AgentEval trace collection.

## Files

### adeworker_plugin.py
Integration module that provides decorators and initialization functions for ADEWorker.

**Key Features:**
- Self-contained module (no external dependencies except AgentEval)
- Graceful degradation if AgentEval not available
- Easy to copy into any ADEWorker project

**Usage:**
```python
from worker.agent.plugins.agenteval_plugin import init_agenteval, instrument_agent, instrument_node
```

### adeworker_agent_instrumented.py
Example showing how to instrument the actual ADEWorker DevAgent class.

**Purpose:**
- Reference implementation
- Shows exact decorator placement
- Documents what changes are needed

### install_to_adeworker.sh
Automated installation script.

**What it does:**
1. Installs AgentEval package
2. Creates plugins directory
3. Copies integration module
4. Copies configuration file
5. Sets up environment variables
6. Verifies installation

**Usage:**
```bash
bash install_to_adeworker.sh
```

## Quick Start

### Option 1: Automated Installation (Recommended)

```bash
cd /home/shared/zqq/AgentEval/integration
bash install_to_adeworker.sh
```

Then follow the printed instructions to:
1. Edit configuration
2. Add initialization to startup
3. Add decorators to agent

### Option 2: Manual Installation

```bash
# 1. Install AgentEval
cd /home/shared/zqq/AgentEval
pip install -e .

# 2. Copy integration module
cp integration/adeworker_plugin.py \
   /home/shared/zqq/adeworker/backend/worker/agent/plugins/agenteval_plugin.py

# 3. Copy configuration
mkdir -p /home/shared/zqq/adeworker/config
cp config/agenteval_plugin.yaml \
   /home/shared/zqq/adeworker/config/agenteval_plugin.yaml

# 4. Set environment variables
export AGENTEVAL_API_KEY="your_api_key"
export AGENTEVAL_PATH="/home/shared/zqq/AgentEval"
```

## Integration Steps

### Step 1: Initialize in Startup

Edit your FastAPI startup (e.g., `backend/worker/main.py`):

```python
from worker.agent.plugins.agenteval_plugin import init_agenteval, shutdown_agenteval

@app.on_event("startup")
async def startup():
    init_agenteval(config_path="config/agenteval_plugin.yaml")

@app.on_event("shutdown")
async def shutdown():
    shutdown_agenteval()
```

### Step 2: Instrument Agent

Edit your agent class (e.g., `backend/worker/agent/dev_agent/agent.py`):

```python
from worker.agent.plugins.agenteval_plugin import instrument_agent, instrument_node

class BaseDevAgent(BaseAgent):

    @instrument_agent(agent_type="DevAgent", agent_version="1.0.0")
    async def arun(self, user_input: UserInput) -> DevState:
        # Existing code unchanged
        ...

    @instrument_node(node_name="prepare_context")
    def _node_prepare_context(self, state: DevState) -> DevState:
        # Existing code unchanged
        ...

    # Add @instrument_node to all other node methods
```

### Step 3: Configure

Edit `config/agenteval_plugin.yaml`:

```yaml
global:
  enabled: true

trace_collector:
  enabled: true
  endpoint: "http://localhost:8000"
  api_key: "${AGENTEVAL_API_KEY}"

  batch:
    max_size: 100
    max_wait_seconds: 1.0

privacy:
  enabled: true
```

### Step 4: Verify

```bash
# Start ADEWorker and check logs
tail -f /var/log/agenteval/plugin.log

# Expected output:
# INFO - Initializing AgentEval Plugin System v1.0.0
# INFO - Registered plugin: AgentEval Evaluation Plugin
# DEBUG - Agent started: trace_id=...
```

## Configuration

### Required Environment Variables

```bash
export AGENTEVAL_API_KEY="your_api_key"
export AGENTEVAL_PATH="/home/shared/zqq/AgentEval"
```

### Optional Environment Variables

```bash
export AGENTEVAL_ENABLED="true"           # Enable/disable plugin
export AGENTEVAL_ENDPOINT="http://..."    # Server endpoint
export AGENTEVAL_LOG_LEVEL="INFO"         # Log level
export AGENTEVAL_SAMPLING_RATE="1.0"      # Sampling rate
```

### Configuration File

See `../config/agenteval_plugin.yaml` for full configuration options.

Key sections:
- `global`: Enable/disable, logging
- `trace_collector`: Endpoint, batching, retry
- `privacy`: Data redaction
- `performance`: Async, compression

## Troubleshooting

### Plugin not found

```bash
# Check installation
python -c "from worker.agent.plugins.agenteval_plugin import init_agenteval; print('OK')"

# Check path
echo $AGENTEVAL_PATH
ls $AGENTEVAL_PATH/agenteval_plugin
```

**Solution:**
```bash
export AGENTEVAL_PATH="/home/shared/zqq/AgentEval"
# Or add to startup code:
import sys
sys.path.insert(0, '/home/shared/zqq/AgentEval')
```

### No traces collected

```yaml
# Enable debug logging in config
global:
  log_level: DEBUG

# Check sampling rate
sampling:
  rate: 1.0
```

### Upload failures

Traces are automatically cached locally:
```bash
ls /tmp/agenteval_cache/
```

Check endpoint connectivity:
```bash
curl -X POST http://localhost:8000/api/v1/traces \
  -H "Authorization: Bearer $AGENTEVAL_API_KEY" \
  -d '{}'
```

## Examples

### Minimal Configuration

```yaml
global:
  enabled: true

trace_collector:
  endpoint: "http://localhost:8000"
  api_key: "${AGENTEVAL_API_KEY}"
```

### Production Configuration

```yaml
global:
  enabled: true
  log_level: WARNING

trace_collector:
  enabled: true
  endpoint: "http://production:8000"
  api_key: "${AGENTEVAL_API_KEY}"

  batch:
    max_size: 500
    max_wait_seconds: 5.0

  sampling:
    rate: 0.1  # 10% sampling
    rules:
      - condition: "error == true"
        rate: 1.0  # Always collect errors

privacy:
  enabled: true
```

### Development Configuration

```yaml
global:
  enabled: true
  log_level: DEBUG

trace_collector:
  enabled: true
  endpoint: "http://localhost:8000"
  api_key: "dev_key"

  batch:
    max_size: 10
    max_wait_seconds: 1.0

  sampling:
    rate: 1.0  # 100% sampling
```

## Documentation

- **Quick Reference**: `../docs/QUICK_REFERENCE.md` - One-page reference
- **Full Integration Guide**: `../docs/ADEWORKER_INTEGRATION.md` - Complete guide
- **Milestone 2 Summary**: `../docs/MILESTONE2_README.md` - Feature overview
- **Example Code**: See `adeworker_agent_instrumented.py`

## Support

For questions or issues:

1. Check the documentation in `../docs/`
2. Review example code in `../examples/`
3. Check configuration in `../config/`
4. Review logs at `/var/log/agenteval/plugin.log`

## Summary

The integration requires:
1. Copy one file: `adeworker_plugin.py`
2. Add two lines to startup: `init_agenteval()` and `shutdown_agenteval()`
3. Add decorators to agent methods: `@instrument_agent` and `@instrument_node`

Total integration time: ~30 minutes
Performance impact: < 5%
Code changes: Minimal (decorators only)
