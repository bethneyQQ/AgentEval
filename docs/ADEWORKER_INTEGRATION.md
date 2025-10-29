# ADEWorker Integration Guide

Complete guide for integrating AgentEval trace collection with ADEWorker.

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Step-by-Step Integration](#step-by-step-integration)
- [Configuration](#configuration)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)

## Overview

The AgentEval plugin system collects execution traces from ADEWorker with minimal code changes and less than 5% performance overhead.

### Key Features

- **Non-invasive**: Only requires adding decorators to existing methods
- **Low overhead**: Less than 5% performance impact
- **Automatic batching**: Traces uploaded asynchronously in batches
- **Data privacy**: Automatic redaction of sensitive information
- **Fallback cache**: Local storage when upload fails
- **Flexible configuration**: YAML or environment variables

### Architecture

```
ADEWorker Agent
    |
    +-- @instrument_agent (arun/astream_run)
    |
    +-- @instrument_node (workflow nodes)
            |
            v
    AgentEval Plugin System
            |
            +-- Collect traces
            +-- Batch events
            +-- Upload async
            |
            v
    AgentEval Server
```

## Quick Start

### 1. Install Dependencies

```bash
cd /home/shared/zqq/AgentEval
pip install -e .
pip install aiohttp pyyaml pydantic
```

### 2. Copy Integration Module

```bash
# Copy the integration module to ADEWorker
cp /home/shared/zqq/AgentEval/integration/adeworker_plugin.py \
   /home/shared/zqq/adeworker/backend/worker/agent/plugins/agenteval_plugin.py
```

### 3. Configure

Create configuration file:

```bash
# Create config directory if not exists
mkdir -p /home/shared/zqq/adeworker/config

# Copy example config
cp /home/shared/zqq/AgentEval/config/agenteval_plugin.yaml \
   /home/shared/zqq/adeworker/config/agenteval_plugin.yaml
```

Edit `/home/shared/zqq/adeworker/config/agenteval_plugin.yaml`:

```yaml
global:
  enabled: true
  log_level: INFO

trace_collector:
  enabled: true
  endpoint: "http://localhost:8000"
  api_key: "${AGENTEVAL_API_KEY}"

  batch:
    max_size: 100
    max_wait_seconds: 1.0

privacy:
  enabled: true
  sensitive_fields:
    - password
    - token
    - api_key
```

Set environment variables:

```bash
export AGENTEVAL_API_KEY="your_api_key_here"
export AGENTEVAL_PATH="/home/shared/zqq/AgentEval"
```

### 4. Initialize Plugin in Startup

Edit your ADEWorker startup file (e.g., `backend/worker/main.py` or wherever FastAPI app is created):

```python
from fastapi import FastAPI
from worker.agent.plugins.agenteval_plugin import init_agenteval, shutdown_agenteval

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    """Initialize AgentEval plugin on startup"""
    config_path = "/home/shared/zqq/adeworker/config/agenteval_plugin.yaml"
    init_agenteval(config_path=config_path)
    print("AgentEval plugin initialized")

@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown AgentEval plugin"""
    shutdown_agenteval()
    print("AgentEval plugin shutdown")
```

### 5. Instrument Your Agent

Edit `backend/worker/agent/dev_agent/agent.py`:

```python
# Add import at the top
from worker.agent.plugins.agenteval_plugin import instrument_agent, instrument_node

class BaseDevAgent(BaseAgent):

    # Add decorator to arun
    @instrument_agent(agent_type="DevAgent", agent_version="1.0.0")
    async def arun(self, user_input: UserInput) -> DevState:
        # Existing code unchanged
        state = DevState(input=user_input)
        state = await self.workflow.ainvoke(
            input=state,
            config={"configurable": {"thread_id": user_input.task_id}}
        )
        return state

    # Add decorator to astream_run
    @instrument_agent(agent_type="DevAgent", agent_version="1.0.0")
    async def astream_run(self, user_input: UserInput):
        # Existing code unchanged
        state = DevState(input=user_input)
        async for step_state in self.workflow.astream(
            input=state,
            config={"configurable": {"thread_id": user_input.task_id}},
            stream_mode="values"
        ):
            yield step_state

    # Add decorators to all node methods
    @instrument_node(node_name="prepare_context")
    def _node_prepare_context(self, state: DevState) -> DevState:
        # Existing code unchanged
        LOGGER.info("Received request and prepare context with state: %s", state)
        state.repo_metadata = RepoMetadata(repo_dir=state.input.repo_ws_path)
        state.output.message = "接收到任务，开始处理"
        state.output.status = "started"
        return state

    @instrument_node(node_name="understand_repo")
    def _node_understand_repo(self, state: DevState) -> DevState:
        # Existing code unchanged
        LOGGER.info("Start to understand the repo code...")
        # ... rest of the code
        return state

    @instrument_node(node_name="gen_requirement")
    def _node_gen_requirement(self, state: DevState) -> DevState:
        # Existing code unchanged
        return state

    @instrument_node(node_name="gen_solution")
    def _node_gen_solution(self, state: DevState) -> DevState:
        # Existing code unchanged
        return state

    @instrument_node(node_name="gen_code")
    def _node_gen_code(self, state: DevState) -> DevState:
        # Existing code unchanged
        return state

    @instrument_node(node_name="run_tests")
    def _node_run_tests(self, state: DevState) -> DevState:
        # Existing code unchanged
        return state

    # Add decorators to other nodes as well
    @instrument_node(node_name="wait_requirement_confirmation")
    def _node_wait_requirement_confirmation(self, state: DevState) -> DevState:
        # Existing code unchanged
        return state

    @instrument_node(node_name="wait_solution_review")
    def _node_wait_solution_review(self, state: DevState) -> DevState:
        # Existing code unchanged
        return state

    @instrument_node(node_name="wait_code_review")
    def _node_wait_code_review(self, state: DevState) -> DevState:
        # Existing code unchanged
        return state

    @instrument_node(node_name="close")
    def _node_close(self, state: DevState):
        # Existing code unchanged
        return state
```

## Step-by-Step Integration

### Step 1: Prepare Environment

```bash
# Set environment variables in your shell or .bashrc
export AGENTEVAL_API_KEY="your_api_key"
export AGENTEVAL_PATH="/home/shared/zqq/AgentEval"

# Or create a .env file in your ADEWorker root
cat > /home/shared/zqq/adeworker/.env << EOF
AGENTEVAL_API_KEY=your_api_key
AGENTEVAL_PATH=/home/shared/zqq/AgentEval
EOF
```

### Step 2: Copy Integration Files

```bash
# Create plugins directory
mkdir -p /home/shared/zqq/adeworker/backend/worker/agent/plugins

# Copy integration module
cp /home/shared/zqq/AgentEval/integration/adeworker_plugin.py \
   /home/shared/zqq/adeworker/backend/worker/agent/plugins/agenteval_plugin.py

# Create __init__.py
touch /home/shared/zqq/adeworker/backend/worker/agent/plugins/__init__.py

# Copy configuration
mkdir -p /home/shared/zqq/adeworker/config
cp /home/shared/zqq/AgentEval/config/agenteval_plugin.yaml \
   /home/shared/zqq/adeworker/config/agenteval_plugin.yaml
```

### Step 3: Update Startup Code

Find your FastAPI application startup (usually in `backend/worker/main.py` or similar):

```python
# Add these imports at the top
from worker.agent.plugins.agenteval_plugin import init_agenteval, shutdown_agenteval
import os

# In your startup event
@app.on_event("startup")
async def startup_event():
    # Your existing startup code...

    # Add AgentEval initialization
    config_path = os.path.join(
        os.path.dirname(__file__),
        "../config/agenteval_plugin.yaml"
    )
    init_agenteval(config_path=config_path)

    # Rest of your startup code...

# In your shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    # Your existing shutdown code...

    # Add AgentEval shutdown
    shutdown_agenteval()

    # Rest of your shutdown code...
```

### Step 4: Instrument Agent Classes

For **DevAgent** (`backend/worker/agent/dev_agent/agent.py`):

```python
from worker.agent.plugins.agenteval_plugin import instrument_agent, instrument_node

class BaseDevAgent(BaseAgent):

    @instrument_agent(agent_type="DevAgent", agent_version="1.0.0")
    async def arun(self, user_input: UserInput) -> DevState:
        # No changes to existing code
        pass

    @instrument_agent(agent_type="DevAgent", agent_version="1.0.0")
    async def astream_run(self, user_input: UserInput):
        # No changes to existing code
        pass

    @instrument_node(node_name="prepare_context")
    def _node_prepare_context(self, state: DevState) -> DevState:
        # No changes to existing code
        pass

    # Add @instrument_node to all other node methods...
```

For **PMAgent** (`backend/worker/agent/pm_agent/agent.py`):

```python
from worker.agent.plugins.agenteval_plugin import instrument_agent, instrument_node

class BasePMAgent(BaseAgent):

    @instrument_agent(agent_type="PMAgent", agent_version="1.0.0")
    async def arun(self, user_input: UserInput) -> PMState:
        # No changes to existing code
        pass

    @instrument_node(node_name="analyze_requirement")
    def _node_analyze_requirement(self, state: PMState) -> PMState:
        # No changes to existing code
        pass

    # Add @instrument_node to all other node methods...
```

### Step 5: Verify Installation

```bash
# Check if plugin module is accessible
cd /home/shared/zqq/adeworker
python -c "from worker.agent.plugins.agenteval_plugin import init_agenteval; print('OK')"

# Check if AgentEval package is accessible
python -c "import agenteval_plugin; print('OK')"

# Check configuration file
cat config/agenteval_plugin.yaml
```

## Configuration

### Configuration File Structure

```yaml
# config/agenteval_plugin.yaml

global:
  enabled: true              # Enable/disable plugin
  log_level: INFO            # DEBUG, INFO, WARNING, ERROR
  log_file: /var/log/agenteval/plugin.log  # Optional log file

trace_collector:
  enabled: true
  endpoint: "http://localhost:8000"     # AgentEval server URL
  api_key: "${AGENTEVAL_API_KEY}"       # API key (from env var)

  batch:
    max_size: 100                        # Events per batch
    max_wait_seconds: 1.0                # Max wait before flush
    max_queue_size: 10000                # Max queue size

  retry:
    max_attempts: 3                      # Retry attempts
    backoff_factor: 2.0                  # Exponential backoff
    max_backoff_seconds: 60              # Max backoff time

  sampling:
    rate: 1.0                            # 1.0 = 100% (collect all)
    rules:                               # Conditional sampling
      - condition: "error == true"
        rate: 1.0                        # Always collect errors
      - condition: "duration > 60"
        rate: 1.0                        # Always collect slow tasks

  local_cache:
    enabled: true                        # Cache failed uploads
    cache_dir: /tmp/agenteval_cache      # Cache directory
    max_size_mb: 1000                    # Max cache size
    ttl_hours: 24                        # Time to live

privacy:
  enabled: true
  sensitive_fields:                      # Fields to redact
    - password
    - token
    - api_key
    - secret
  redact_patterns:                       # Regex patterns
    - pattern: "sk-[a-zA-Z0-9]{32,}"
      replacement: "sk-***REDACTED***"
    - pattern: "ghp_[a-zA-Z0-9]{36}"
      replacement: "ghp_***REDACTED***"

performance:
  async_mode: true                       # Async hook execution
  max_concurrent_uploads: 5              # Parallel uploads
  use_compression: true                  # gzip compression
```

### Environment Variables

You can override configuration with environment variables:

```bash
# Enable/disable plugin
export AGENTEVAL_ENABLED="true"

# Server endpoint
export AGENTEVAL_ENDPOINT="http://localhost:8000"

# API key
export AGENTEVAL_API_KEY="your_api_key"

# Log level
export AGENTEVAL_LOG_LEVEL="INFO"

# Sampling rate
export AGENTEVAL_SAMPLING_RATE="1.0"

# AgentEval package path
export AGENTEVAL_PATH="/home/shared/zqq/AgentEval"
```

### Production Configuration

For production, consider:

```yaml
global:
  enabled: true
  log_level: WARNING

trace_collector:
  enabled: true
  endpoint: "http://production-server:8000"
  api_key: "${AGENTEVAL_API_KEY}"

  batch:
    max_size: 500              # Larger batches
    max_wait_seconds: 5.0      # Less frequent uploads

  sampling:
    rate: 0.1                  # Sample 10%
    rules:
      - condition: "error == true"
        rate: 1.0              # Always collect errors
      - condition: "duration > 120"
        rate: 1.0              # Collect very slow tasks

privacy:
  enabled: true                # Always enable in production
```

## Verification

### Check Plugin Initialization

After starting your ADEWorker application:

```bash
# Check logs
tail -f /var/log/agenteval/plugin.log

# Expected output:
# INFO - Initializing AgentEval Plugin System v1.0.0
# INFO - Enabled plugin: evaluation_plugin
# INFO - Registered plugin: AgentEval Evaluation Plugin v1.0.0
# INFO - AgentEval Plugin System initialized successfully
```

### Check Trace Collection

Run a test task and check for trace collection:

```bash
# Watch logs
tail -f /var/log/agenteval/plugin.log

# Expected output during task execution:
# DEBUG - Agent started: trace_id=abc-123, task_id=task_001
# DEBUG - Node started: prepare_context
# DEBUG - Node ended: prepare_context, duration=0.5s
# DEBUG - Node started: gen_code
# DEBUG - Node ended: gen_code, duration=2.3s
# DEBUG - Agent ended: trace_id=abc-123, duration=10.2s, status=ok
# DEBUG - Uploaded 8 traces successfully
```

### Check Local Cache (if upload fails)

```bash
# Check cache directory
ls -lh /tmp/agenteval_cache/

# Expected: failed_*.json.gz files if upload failed
```

### Verify Trace Data

If you have access to the AgentEval server:

```bash
# Query traces for a specific task
curl -X GET "http://localhost:8000/api/v1/traces?task_id=task_001" \
  -H "Authorization: Bearer $AGENTEVAL_API_KEY"
```

## Troubleshooting

### Plugin Not Initializing

**Symptom**: No log messages about plugin initialization

**Check**:
```bash
# 1. Verify AGENTEVAL_PATH
echo $AGENTEVAL_PATH
python -c "import sys; print($AGENTEVAL_PATH in sys.path)"

# 2. Verify package installation
cd $AGENTEVAL_PATH
pip list | grep agenteval-plugin

# 3. Check import
python -c "import agenteval_plugin; print('OK')"

# 4. Check configuration
python -c "from agenteval_plugin import get_config; print(get_config().get('global.enabled'))"
```

**Solution**:
```bash
# Reinstall package
cd /home/shared/zqq/AgentEval
pip install -e .

# Add to Python path in startup code
import sys
sys.path.insert(0, '/home/shared/zqq/AgentEval')
```

### No Traces Being Collected

**Symptom**: Plugin initialized but no trace events in logs

**Check**:
```bash
# 1. Verify plugin is enabled
python -c "from agenteval_plugin import get_config; print(get_config().to_dict())"

# 2. Check if decorators are being called
# Add debug logging to your agent methods temporarily
```

**Common causes**:
- Plugin disabled in configuration
- Decorators not added to methods
- Methods not being called
- Sampling rate set to 0

**Solution**:
```yaml
# In config/agenteval_plugin.yaml
global:
  enabled: true
  log_level: DEBUG  # Enable debug logging

trace_collector:
  enabled: true
  sampling:
    rate: 1.0  # Ensure 100% sampling
```

### Upload Failures

**Symptom**: "Upload failed" or "Failed to upload after N attempts" in logs

**Check**:
```bash
# 1. Test endpoint connectivity
curl -X POST http://localhost:8000/api/v1/traces \
  -H "Authorization: Bearer $AGENTEVAL_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"traces": []}'

# 2. Check local cache
ls -lh /tmp/agenteval_cache/

# 3. Check API key
echo $AGENTEVAL_API_KEY
```

**Solution**:
- Verify AgentEval server is running
- Check network connectivity
- Verify API key is correct
- Traces are cached locally, can be uploaded later

### High Memory Usage

**Symptom**: Memory consumption increases over time

**Check**:
```bash
# Check queue size
# Add to your monitoring
```

**Solution**:
```yaml
# Reduce queue size and batch more frequently
batch:
  max_size: 50
  max_wait_seconds: 0.5
  max_queue_size: 5000
```

### Performance Impact Too High

**Symptom**: Task execution time increases significantly

**Check**:
- Profile task execution with and without plugin
- Check log for slow operations

**Solution**:
```yaml
# Reduce sampling rate
sampling:
  rate: 0.1  # Collect only 10%

# Increase batch size to reduce network calls
batch:
  max_size: 500
  max_wait_seconds: 5.0

# Ensure async mode is enabled
performance:
  async_mode: true
```

### Decorator Import Errors

**Symptom**: "ImportError: cannot import name 'instrument_agent'"

**Solution**:
```python
# Verify import path
from worker.agent.plugins.agenteval_plugin import instrument_agent, instrument_node

# Or use absolute import
import sys
sys.path.insert(0, '/home/shared/zqq/adeworker')
from worker.agent.plugins.agenteval_plugin import instrument_agent, instrument_node
```

## Advanced Usage

### Conditional Instrumentation

Only instrument in certain environments:

```python
import os

# Only enable in development/staging
if os.getenv('ENVIRONMENT') in ['development', 'staging']:
    from worker.agent.plugins.agenteval_plugin import instrument_agent, instrument_node
else:
    # Dummy decorators that do nothing
    def instrument_agent(**kwargs):
        def decorator(func):
            return func
        return decorator

    def instrument_node(**kwargs):
        def decorator(func):
            return func
        return decorator
```

### Custom Sampling Rules

Implement smart sampling based on task characteristics:

```yaml
sampling:
  rate: 0.1  # Default 10%
  rules:
    # Always collect errors
    - condition: "error == true"
      rate: 1.0

    # Always collect slow tasks
    - condition: "duration > 60"
      rate: 1.0

    # High sampling for specific users (testing)
    - condition: "user_id == 'test_user'"
      rate: 1.0

    # No sampling for health checks
    - condition: "task_type == 'health_check'"
      rate: 0.0
```

### Manual Trace Upload

If you want to manually upload cached traces:

```bash
# Find cached traces
ls /tmp/agenteval_cache/failed_*.json.gz

# Manually upload using curl
for file in /tmp/agenteval_cache/failed_*.json.gz; do
    curl -X POST http://localhost:8000/api/v1/traces \
      -H "Authorization: Bearer $AGENTEVAL_API_KEY" \
      -H "Content-Type: application/json" \
      -H "Content-Encoding: gzip" \
      --data-binary @"$file"
done
```

## Summary

Integration checklist:

- [ ] Install dependencies: `pip install -e /home/shared/zqq/AgentEval`
- [ ] Copy integration module to ADEWorker plugins directory
- [ ] Copy configuration file
- [ ] Set environment variables (AGENTEVAL_API_KEY, AGENTEVAL_PATH)
- [ ] Add init_agenteval() to startup
- [ ] Add shutdown_agenteval() to shutdown
- [ ] Add @instrument_agent decorators to arun/astream_run
- [ ] Add @instrument_node decorators to all node methods
- [ ] Test and verify trace collection
- [ ] Monitor performance impact

Total integration time: Approximately 30 minutes

The plugin system will:
- Automatically collect execution traces
- Batch and upload asynchronously
- Cache locally if upload fails
- Redact sensitive information
- Maintain < 5% performance overhead

For questions or issues, refer to the complete documentation in `/home/shared/zqq/AgentEval/docs/`.
