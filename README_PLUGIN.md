# AgentEval Plugin System

Low-overhead trace collection plugin for ADEWorker agent execution monitoring.

## Overview

The AgentEval plugin system collects execution traces from ADEWorker agents with less than 5% performance overhead. It uses decorators for non-invasive integration and provides async batch uploading with local fallback caching.

## Features

- **Non-invasive**: Only requires adding decorators to methods
- **Low overhead**: < 5% performance impact
- **Async batch upload**: Events uploaded in batches asynchronously
- **Data privacy**: Automatic redaction of sensitive information
- **Fallback cache**: Local storage when upload fails
- **Flexible config**: YAML or environment variables

## Quick Start

### 1. Install

```bash
cd /home/shared/zqq/AgentEval
pip install -e .
pip install aiohttp pyyaml pydantic
```

### 2. Integrate with ADEWorker

```bash
# Automated installation
bash integration/install_to_adeworker.sh

# Or manual installation - see docs/ADEWORKER_INTEGRATION.md
```

### 3. Configure

```bash
# Set API key
export AGENTEVAL_API_KEY="your_api_key"

# Edit configuration if needed
vi /home/shared/zqq/adeworker/config/agenteval_plugin.yaml
```

### 4. Use in Code

```python
# In startup (backend/worker/main.py)
from worker.agent.plugins.agenteval_plugin import init_agenteval, shutdown_agenteval

@app.on_event("startup")
async def startup():
    init_agenteval(config_path="config/agenteval_plugin.yaml")

@app.on_event("shutdown")
async def shutdown():
    shutdown_agenteval()

# In agent (backend/worker/agent/dev_agent/agent.py)
from worker.agent.plugins.agenteval_plugin import instrument_agent, instrument_node

class BaseDevAgent(BaseAgent):
    @instrument_agent(agent_type="DevAgent", agent_version="1.0.0")
    async def arun(self, user_input):
        # Your code unchanged
        ...

    @instrument_node(node_name="gen_code")
    def _node_gen_code(self, state):
        # Your code unchanged
        ...
```

## Documentation

- **Quick Reference**: [docs/QUICK_REFERENCE.md](docs/QUICK_REFERENCE.md) - One-page guide
- **Integration Guide**: [docs/ADEWORKER_INTEGRATION.md](docs/ADEWORKER_INTEGRATION.md) - Complete guide
- **Update Summary**: [docs/INTEGRATION_UPDATE_SUMMARY.md](docs/INTEGRATION_UPDATE_SUMMARY.md) - What's new
- **Milestone 2**: [docs/MILESTONE2_README.md](docs/MILESTONE2_README.md) - Feature overview

## Directory Structure

```
AgentEval/
├── agenteval_plugin/          # Plugin package
│   ├── core/                  # Plugin system
│   ├── trace/                 # Trace collection
│   ├── session/               # Session mapping
│   ├── plugins/               # Plugin implementations
│   ├── privacy/               # Data redaction
│   └── utils/                 # Utilities
│
├── integration/               # ADEWorker integration
│   ├── adeworker_plugin.py           # Integration module (copy this)
│   ├── adeworker_agent_instrumented.py  # Reference implementation
│   ├── install_to_adeworker.sh       # Installation script
│   └── README.md                     # Integration guide
│
├── docs/                      # Documentation
│   ├── QUICK_REFERENCE.md            # One-page reference
│   ├── ADEWORKER_INTEGRATION.md      # Complete guide
│   └── INTEGRATION_UPDATE_SUMMARY.md # Update summary
│
├── examples/                  # Examples
│   ├── simple_integration_example.py  # Minimal example
│   └── adeworker_integration_example.py  # Full example
│
├── config/                    # Configuration
│   └── agenteval_plugin.yaml         # Configuration template
│
└── tests/                     # Tests
    ├── unit/                  # Unit tests
    └── integration/           # Integration tests
```

## Configuration

### Minimal Configuration

```yaml
global:
  enabled: true

trace_collector:
  enabled: true
  endpoint: "http://localhost:8000"
  api_key: "${AGENTEVAL_API_KEY}"
```

### Environment Variables

```bash
export AGENTEVAL_API_KEY="your_api_key"
export AGENTEVAL_PATH="/home/shared/zqq/AgentEval"
export AGENTEVAL_ENABLED="true"
```

See [config/agenteval_plugin.yaml](config/agenteval_plugin.yaml) for all options.

## Examples

### Basic Usage

```python
from agenteval_plugin import init_plugin_system, instrument_agent, instrument_node

# Initialize
init_plugin_system(config_path="config/agenteval_plugin.yaml")

# Instrument agent
class MyAgent:
    @instrument_agent(agent_type="MyAgent", agent_version="1.0.0")
    async def arun(self, user_input):
        return await self.process(user_input)

    @instrument_node(node_name="process")
    def process(self, state):
        return state
```

See [examples/simple_integration_example.py](examples/simple_integration_example.py) for a complete working example.

## Testing

```bash
# Unit tests
pytest tests/unit/ -v

# Run simple example
python examples/simple_integration_example.py
```

## Troubleshooting

### Plugin not found

```bash
export AGENTEVAL_PATH="/home/shared/zqq/AgentEval"
python -c "import agenteval_plugin; print('OK')"
```

### No traces collected

```yaml
# Enable debug logging
global:
  log_level: DEBUG

sampling:
  rate: 1.0
```

### Upload failures

Check cached traces:
```bash
ls /tmp/agenteval_cache/
```

See [docs/ADEWORKER_INTEGRATION.md](docs/ADEWORKER_INTEGRATION.md) for more troubleshooting.

## Performance

Verified metrics:
- Overhead: < 5%
- Memory: ~20MB additional
- Batch size: ~600 bytes compressed per batch
- Network: Async, batched, compressed

## Architecture

```
Agent Methods
    |
    +-- @instrument_agent (arun/astream_run)
    +-- @instrument_node (workflow nodes)
            |
            v
    Plugin Manager
            |
            +-- EvaluationPlugin
            |       |
            |       +-- Collect traces
            |       +-- Create events
            |
            v
    TraceCollector
            |
            +-- Batch events (100 or 1s)
            +-- Compress (gzip)
            +-- Upload async
            |
            v
    AgentEval Server
            |
    Local Cache (if upload fails)
```

## Key Components

1. **Plugin System** - Lifecycle management, hook execution
2. **Trace Collector** - Async batching, retry, caching
3. **Session Mapper** - Session-to-trace mapping
4. **Evaluation Plugin** - Core trace collection
5. **Data Redactor** - Sensitive data filtering
6. **Configuration** - YAML + environment variables

## Integration Steps

1. Copy integration module: `integration/adeworker_plugin.py`
2. Add init to startup: `init_agenteval(config_path=...)`
3. Add decorators to agent: `@instrument_agent`, `@instrument_node`
4. Configure: Edit `config/agenteval_plugin.yaml`
5. Set API key: `export AGENTEVAL_API_KEY=...`

Total time: ~30 minutes

## Requirements

- Python >= 3.8
- pydantic >= 2.0.0
- pyyaml >= 6.0
- aiohttp >= 3.8.0

## License

MIT License

## Support

- Quick Reference: [docs/QUICK_REFERENCE.md](docs/QUICK_REFERENCE.md)
- Integration Guide: [docs/ADEWORKER_INTEGRATION.md](docs/ADEWORKER_INTEGRATION.md)
- Examples: [examples/](examples/)
- Configuration: [config/agenteval_plugin.yaml](config/agenteval_plugin.yaml)

## Version

Current version: 1.0.0

Milestone 2 Complete - Production Ready
