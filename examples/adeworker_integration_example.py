"""
ADEWorker Integration Example

This example demonstrates how to integrate AgentEval plugin with ADEWorker.
"""

import asyncio
import sys
from pathlib import Path

# Add AgentEval to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agenteval_plugin import (
    init_plugin_system,
    shutdown_plugin_system,
    instrument_agent,
    instrument_node,
)


# ===== Mock ADEWorker Classes (for demonstration) =====

class UserInput:
    """Mock UserInput"""
    def __init__(self, task_id, task_desc, repo_ws_path, session_id="", user_id=""):
        self.task_id = task_id
        self.task_desc = task_desc
        self.repo_ws_path = repo_ws_path
        self.session_id = session_id
        self.user_id = user_id


class DevState:
    """Mock DevState"""
    def __init__(self, input):
        self.input = input
        self.output = {"status": "pending", "message": ""}

    def model_dump(self):
        return {
            "input": self.input.__dict__,
            "output": self.output
        }


# ===== Instrumented Agent (Example) =====

class InstrumentedDevAgent:
    """Example instrumented agent"""

    def __init__(self):
        self.workflow_steps = [
            "prepare_context",
            "understand_repo",
            "gen_requirement",
            "gen_solution",
            "gen_code",
            "run_tests"
        ]

    @instrument_agent(agent_type="DevAgent", agent_version="1.0.0")
    async def arun(self, user_input: UserInput) -> DevState:
        """Main agent execution (instrumented)"""
        print(f"🚀 Starting agent execution for task: {user_input.task_id}")

        state = DevState(input=user_input)

        # Execute workflow
        for step in self.workflow_steps:
            state = await self._execute_step(step, state)

        state.output["status"] = "completed"
        state.output["message"] = "Task completed successfully"

        print(f"✅ Agent execution completed for task: {user_input.task_id}")
        return state

    async def _execute_step(self, step_name: str, state: DevState) -> DevState:
        """Execute a single workflow step"""
        method = getattr(self, f"_node_{step_name}", None)
        if method:
            return method(state)
        return state

    @instrument_node(node_name="prepare_context")
    def _node_prepare_context(self, state: DevState) -> DevState:
        """Prepare context node"""
        print("  📝 Preparing context...")
        import time
        time.sleep(0.1)  # Simulate work
        state.output["message"] = "Context prepared"
        return state

    @instrument_node(node_name="understand_repo")
    def _node_understand_repo(self, state: DevState) -> DevState:
        """Understand repository node"""
        print("  🔍 Understanding repository...")
        import time
        time.sleep(0.1)  # Simulate work
        state.output["message"] = "Repository analyzed"
        return state

    @instrument_node(node_name="gen_requirement")
    def _node_gen_requirement(self, state: DevState) -> DevState:
        """Generate requirement node"""
        print("  📋 Generating requirement...")
        import time
        time.sleep(0.1)  # Simulate work
        state.output["message"] = "Requirement generated"
        return state

    @instrument_node(node_name="gen_solution")
    def _node_gen_solution(self, state: DevState) -> DevState:
        """Generate solution node"""
        print("  💡 Generating solution...")
        import time
        time.sleep(0.1)  # Simulate work
        state.output["message"] = "Solution designed"
        return state

    @instrument_node(node_name="gen_code")
    def _node_gen_code(self, state: DevState) -> DevState:
        """Generate code node"""
        print("  💻 Generating code...")
        import time
        time.sleep(0.1)  # Simulate work
        state.output["message"] = "Code generated"
        return state

    @instrument_node(node_name="run_tests")
    def _node_run_tests(self, state: DevState) -> DevState:
        """Run tests node"""
        print("  🧪 Running tests...")
        import time
        time.sleep(0.1)  # Simulate work
        state.output["message"] = "Tests passed"
        return state


# ===== Main Demo =====

async def main():
    """Main demo function"""

    print("=" * 60)
    print("AgentEval Plugin - ADEWorker Integration Demo")
    print("=" * 60)
    print()

    # Step 1: Initialize plugin system
    print("📦 Step 1: Initializing AgentEval plugin system...")
    config_path = Path(__file__).parent.parent / "config" / "agenteval_plugin.yaml"

    # Use minimal config for demo (no actual server)
    demo_config = {
        'global': {'enabled': True, 'log_level': 'INFO'},
        'trace_collector': {
            'enabled': True,
            'endpoint': 'http://localhost:8000',
            'api_key': 'demo_key',
            'batch': {
                'max_size': 10,
                'max_wait_seconds': 2.0,
                'max_queue_size': 100
            },
            'retry': {'max_attempts': 1},
            'local_cache': {
                'enabled': True,
                'cache_dir': '/tmp/agenteval_demo_cache'
            },
            'privacy': {'enabled': True, 'sensitive_fields': ['password']},
            'performance': {'use_compression': False}
        }
    }

    plugin_manager = init_plugin_system(config_dict=demo_config)
    print(f"✅ Plugin system initialized with {len(plugin_manager.get_active_plugins())} active plugins")
    print()

    # Step 2: Create instrumented agent
    print("🤖 Step 2: Creating instrumented agent...")
    agent = InstrumentedDevAgent()
    print("✅ Agent created and instrumented")
    print()

    # Step 3: Run agent tasks
    print("🎯 Step 3: Running agent tasks...")
    print()

    tasks = [
        UserInput(
            task_id="task_001",
            task_desc="Implement user authentication",
            repo_ws_path="/tmp/repo1",
            session_id="session_001",
            user_id="user_001"
        ),
        UserInput(
            task_id="task_002",
            task_desc="Add logging functionality",
            repo_ws_path="/tmp/repo2",
            session_id="session_002",
            user_id="user_001"
        ),
    ]

    for user_input in tasks:
        print(f"Task: {user_input.task_id} - {user_input.task_desc}")
        result = await agent.arun(user_input)
        print(f"Result: {result.output['message']}")
        print()

    # Step 4: Wait for batch upload
    print("⏳ Step 4: Waiting for trace batch upload...")
    await asyncio.sleep(3)  # Wait for batch to flush
    print()

    # Step 5: Shutdown
    print("🛑 Step 5: Shutting down plugin system...")
    shutdown_plugin_system()
    print("✅ Plugin system shutdown complete")
    print()

    # Step 6: Check collected traces
    print("📊 Step 6: Checking collected traces...")
    cache_dir = Path("/tmp/agenteval_demo_cache")
    if cache_dir.exists():
        trace_files = list(cache_dir.glob("*.json*"))
        print(f"✅ Found {len(trace_files)} cached trace batches")
        for f in trace_files:
            print(f"  - {f.name} ({f.stat().st_size} bytes)")
    else:
        print("⚠️  No cached traces found (this is normal if upload succeeded)")
    print()

    print("=" * 60)
    print("Demo completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
