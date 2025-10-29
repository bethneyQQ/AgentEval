# AgentEval Plugin - Quick Reference

## Installation

```bash
# 1. Install package
cd /home/shared/zqq/AgentEval
pip install -e .

# 2. Run installation script
bash integration/install_to_adeworker.sh

# 3. Set API key
export AGENTEVAL_API_KEY="your_api_key"
```

## Basic Usage

### Initialize Plugin

```python
from worker.agent.plugins.agenteval_plugin import init_agenteval, shutdown_agenteval

# Startup
init_agenteval(config_path="config/agenteval_plugin.yaml")

# Shutdown
shutdown_agenteval()
```

### Instrument Agent

```python
from worker.agent.plugins.agenteval_plugin import instrument_agent, instrument_node

class MyAgent:
    @instrument_agent(agent_type="DevAgent", agent_version="1.0.0")
    async def arun(self, user_input):
        # Your code here
        return result

    @instrument_node(node_name="process_data")
    def _node_process_data(self, state):
        # Your code here
        return state
```

## Configuration

### Minimal Config (config/agenteval_plugin.yaml)

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

## Common Tasks

### Enable/Disable Plugin

```yaml
# In config file
global:
  enabled: false  # Disable
```

### Adjust Sampling

```yaml
# Sample 10% of requests
sampling:
  rate: 0.1
```

### Always Collect Errors

```yaml
sampling:
  rate: 0.1
  rules:
    - condition: "error == true"
      rate: 1.0
```

### Check Logs

```bash
tail -f /var/log/agenteval/plugin.log
```

### Check Local Cache

```bash
ls -lh /tmp/agenteval_cache/
```

## Troubleshooting

### Plugin Not Starting

```bash
# Check installation
python -c "from worker.agent.plugins.agenteval_plugin import init_agenteval; print('OK')"

# Check path
echo $AGENTEVAL_PATH
```

### No Traces Collected

```yaml
# Enable debug logging
global:
  log_level: DEBUG

# Check sampling rate
sampling:
  rate: 1.0
```

### Upload Failing

```bash
# Test endpoint
curl -X POST http://localhost:8000/api/v1/traces \
  -H "Authorization: Bearer $AGENTEVAL_API_KEY" \
  -d '{"traces": []}'

# Check cache (traces are saved locally)
ls /tmp/agenteval_cache/
```

## File Locations

```
ADEWorker/
├── backend/worker/agent/plugins/
│   └── agenteval_plugin.py         # Integration module
├── config/
│   └── agenteval_plugin.yaml       # Configuration
└── .env                            # Environment variables

AgentEval/
├── agenteval_plugin/               # Plugin package
├── config/
│   └── agenteval_plugin.yaml       # Example config
├── docs/
│   └── ADEWORKER_INTEGRATION.md    # Full guide
└── integration/
    ├── adeworker_plugin.py         # Integration module
    └── install_to_adeworker.sh     # Install script
```

## Code Templates

### FastAPI Startup

```python
from fastapi import FastAPI
from worker.agent.plugins.agenteval_plugin import init_agenteval, shutdown_agenteval

app = FastAPI()

@app.on_event("startup")
async def startup():
    init_agenteval(config_path="config/agenteval_plugin.yaml")

@app.on_event("shutdown")
async def shutdown():
    shutdown_agenteval()
```

### Agent with All Nodes

```python
from worker.agent.plugins.agenteval_plugin import instrument_agent, instrument_node

class BaseDevAgent(BaseAgent):

    @instrument_agent(agent_type="DevAgent", agent_version="1.0.0")
    async def arun(self, user_input: UserInput) -> DevState:
        # Existing code
        pass

    @instrument_node(node_name="prepare_context")
    def _node_prepare_context(self, state: DevState) -> DevState:
        # Existing code
        pass

    @instrument_node(node_name="understand_repo")
    def _node_understand_repo(self, state: DevState) -> DevState:
        # Existing code
        pass

    @instrument_node(node_name="gen_requirement")
    def _node_gen_requirement(self, state: DevState) -> DevState:
        # Existing code
        pass

    @instrument_node(node_name="gen_solution")
    def _node_gen_solution(self, state: DevState) -> DevState:
        # Existing code
        pass

    @instrument_node(node_name="gen_code")
    def _node_gen_code(self, state: DevState) -> DevState:
        # Existing code
        pass

    @instrument_node(node_name="run_tests")
    def _node_run_tests(self, state: DevState) -> DevState:
        # Existing code
        pass
```

## Performance Tuning

### Low Traffic (< 10 req/min)

```yaml
batch:
  max_size: 50
  max_wait_seconds: 0.5
```

### High Traffic (> 100 req/min)

```yaml
batch:
  max_size: 500
  max_wait_seconds: 5.0

sampling:
  rate: 0.1  # 10% sampling
```

### Production

```yaml
global:
  log_level: WARNING

sampling:
  rate: 0.1
  rules:
    - condition: "error == true"
      rate: 1.0

privacy:
  enabled: true
```

## Support

- Full Documentation: `/home/shared/zqq/AgentEval/docs/ADEWORKER_INTEGRATION.md`
- Example Code: `/home/shared/zqq/AgentEval/examples/`
- Configuration: `/home/shared/zqq/AgentEval/config/agenteval_plugin.yaml`
