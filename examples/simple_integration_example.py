"""
Simple Integration Example

Demonstrates basic AgentEval plugin usage without ADEWorker dependencies.
"""

import asyncio
import sys
import time
from pathlib import Path

# Add AgentEval to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agenteval_plugin import init_plugin_system, shutdown_plugin_system
from agenteval_plugin import instrument_agent, instrument_node


# ===== Mock Classes =====

class UserInput:
    """Mock user input"""
    def __init__(self, task_id, task_desc, repo_ws_path, session_id="", user_id=""):
        self.task_id = task_id
        self.task_desc = task_desc
        self.repo_ws_path = repo_ws_path
        self.session_id = session_id
        self.user_id = user_id


class State:
    """Mock state"""
    def __init__(self, input):
        self.input = input
        self.data = {}

    def model_dump(self):
        return {"input": self.input.__dict__, "data": self.data}


# ===== Instrumented Agent =====

class SimpleAgent:
    """Simple instrumented agent"""

    @instrument_agent(agent_type="SimpleAgent", agent_version="1.0.0")
    async def arun(self, user_input: UserInput):
        """Main execution method"""
        print(f"[Agent] Starting task: {user_input.task_id}")

        state = State(input=user_input)

        # Execute workflow steps
        state = self.step1(state)
        state = self.step2(state)
        state = self.step3(state)

        print(f"[Agent] Task completed: {user_input.task_id}")
        return state

    @instrument_node(node_name="step1")
    def step1(self, state):
        """First step"""
        print("[Node] Executing step1...")
        time.sleep(0.1)
        state.data["step1"] = "completed"
        return state

    @instrument_node(node_name="step2")
    def step2(self, state):
        """Second step"""
        print("[Node] Executing step2...")
        time.sleep(0.2)
        state.data["step2"] = "completed"
        return state

    @instrument_node(node_name="step3")
    def step3(self, state):
        """Third step"""
        print("[Node] Executing step3...")
        time.sleep(0.1)
        state.data["step3"] = "completed"
        return state


# ===== Main =====

async def main():
    print("=" * 60)
    print("AgentEval Simple Integration Example")
    print("=" * 60)
    print()

    # Initialize plugin
    print("[Setup] Initializing plugin system...")
    config = {
        'global': {'enabled': True, 'log_level': 'INFO'},
        'trace_collector': {
            'enabled': True,
            'endpoint': 'http://localhost:8000',
            'api_key': 'demo_key',
            'batch': {'max_size': 10, 'max_wait_seconds': 2.0},
            'retry': {'max_attempts': 1},
            'local_cache': {'enabled': True, 'cache_dir': '/tmp/agenteval_example'},
            'privacy': {'enabled': True},
            'performance': {'use_compression': False}
        }
    }

    init_plugin_system(config_dict=config)
    print("[Setup] Plugin initialized")
    print()

    # Create agent
    agent = SimpleAgent()

    # Run tasks
    print("[Test] Running tasks...")
    print()

    tasks = [
        UserInput(
            task_id="task_001",
            task_desc="Process data batch 1",
            repo_ws_path="/tmp/repo1",
            session_id="session_001",
            user_id="user_001"
        ),
        UserInput(
            task_id="task_002",
            task_desc="Process data batch 2",
            repo_ws_path="/tmp/repo2",
            session_id="session_002",
            user_id="user_001"
        ),
    ]

    for user_input in tasks:
        result = await agent.arun(user_input)
        print()

    # Wait for batch upload
    print("[Test] Waiting for trace upload...")
    await asyncio.sleep(3)
    print()

    # Shutdown
    print("[Cleanup] Shutting down...")
    shutdown_plugin_system()
    print()

    # Check results
    print("[Results] Checking cached traces...")
    cache_dir = Path("/tmp/agenteval_example")
    if cache_dir.exists():
        trace_files = list(cache_dir.glob("*.json*"))
        print(f"Found {len(trace_files)} cached trace batches")
        for f in trace_files:
            print(f"  - {f.name} ({f.stat().st_size} bytes)")
    else:
        print("No cached traces (upload may have succeeded)")
    print()

    print("=" * 60)
    print("Example completed")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
