# AgentEval Plugin - Quick Start Guide

Get started with the AgentEval plugin system in 5 minutes.

## 1. Install

```bash
cd /home/shared/zqq/AgentEval
pip install -e .
pip install aiohttp pyyaml pydantic
```

## 2. Configure

Create `config/agenteval_plugin.yaml`:

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
```

Set environment variable:

```bash
export AGENTEVAL_API_KEY="your_api_key_here"
```

## 3. Initialize

In your application startup:

```python
from agenteval_plugin import init_plugin_system, shutdown_plugin_system

# On startup
def startup():
    init_plugin_system(config_path="config/agenteval_plugin.yaml")

# On shutdown
def shutdown():
    shutdown_plugin_system()
```

## 4. Instrument Your Agent

### Agent Methods

```python
from agenteval_plugin import instrument_agent

class MyAgent:
    @instrument_agent(agent_type="MyAgent", agent_version="1.0.0")
    async def arun(self, user_input):
        # Your existing code - no changes needed
        result = await self.workflow.ainvoke(...)
        return result
```

### Node Methods

```python
from agenteval_plugin import instrument_node

class MyAgent:
    @instrument_node(node_name="process_data")
    def _node_process_data(self, state):
        # Your existing code - no changes needed
        return state
```

## 5. Run and Verify

```bash
# Run your application
python your_app.py

# Check logs
tail -f /var/log/agenteval/plugin.log
```

You should see:
```
INFO - Initializing AgentEval Plugin System v1.0.0
INFO - Registered plugin: AgentEval Evaluation Plugin v1.0.0
DEBUG - Agent started: trace_id=...
DEBUG - Node started: process_data
DEBUG - Uploaded 10 traces successfully
```

## 6. Test with Example

```bash
# Run the example
python examples/adeworker_integration_example.py
```

Expected output:
```
✅ Plugin system initialized with 1 active plugins
✅ Agent created and instrumented
🚀 Starting agent execution for task: task_001
✅ Agent execution completed
✅ Found 1 cached trace batches
```

## Configuration Options

### Sampling

Sample 10% of traces:

```yaml
sampling:
  rate: 0.1
```

Always collect errors:

```yaml
sampling:
  rate: 0.1
  rules:
    - condition: "error == true"
      rate: 1.0
```

### Batch Size

Larger batches for efficiency:

```yaml
batch:
  max_size: 500
  max_wait_seconds: 5.0
```

### Privacy

Add sensitive patterns:

```yaml
privacy:
  sensitive_fields:
    - password
    - api_key
  redact_patterns:
    - pattern: "my-secret-.*"
      replacement: "***REDACTED***"
```

## Troubleshooting

### Plugin not collecting traces?

```bash
# Check if enabled
python -c "from agenteval_plugin import get_config; print(get_config().get('global.enabled'))"

# Check logs
tail -f /var/log/agenteval/plugin.log
```

### Upload failing?

Traces are automatically cached locally:

```bash
ls -lh /tmp/agenteval_cache/
```

### Performance issues?

Reduce sampling rate:

```yaml
sampling:
  rate: 0.1  # Collect only 10%
```

## Next Steps

- Read full [Integration Guide](ADEWORKER_INTEGRATION_GUIDE.md)
- Review [Configuration Options](../config/agenteval_plugin.yaml)
- Run [Unit Tests](../tests/unit/)

## Help

For issues or questions:
- Check the [Integration Guide](ADEWORKER_INTEGRATION_GUIDE.md)
- Review [Milestone 2 README](MILESTONE2_README.md)
- Open an issue on GitHub

---

That's it! You're now collecting agent execution traces with < 5% overhead. 🚀
