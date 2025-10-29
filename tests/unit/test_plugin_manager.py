"""
Unit tests for Plugin Manager
"""

import pytest
import asyncio
from agenteval_plugin.core import (
    PluginManager, BasePlugin, PluginMetadata, PluginConfig, AgentContext
)


class MockPlugin(BasePlugin):
    """Mock plugin for testing"""

    def __init__(self, plugin_id: str = "mock_plugin"):
        super().__init__(PluginConfig(enabled=True, priority=100))
        self.plugin_id = plugin_id
        self.call_count = 0
        self.agent_start_calls = []
        self.agent_end_calls = []

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            id=self.plugin_id,
            name="Mock Plugin",
            version="1.0.0",
            description="Test plugin",
            author="Test"
        )

    async def on_agent_start(self, context: AgentContext) -> None:
        self.call_count += 1
        self.agent_start_calls.append(context)

    async def on_agent_end(self, context: AgentContext, result, error=None) -> None:
        self.call_count += 1
        self.agent_end_calls.append((context, result, error))


@pytest.fixture
def plugin_manager():
    """Create fresh plugin manager for each test"""
    return PluginManager()


@pytest.fixture
def mock_plugin():
    """Create mock plugin"""
    return MockPlugin()


@pytest.fixture
def agent_context():
    """Create mock agent context"""
    return AgentContext(
        agent_id="test_agent",
        agent_type="TestAgent",
        agent_version="1.0.0",
        session_id="session_1",
        user_id="user_1",
        task_id="task_1",
        workspace_path="/tmp/test",
        start_time=1234567890.0
    )


class TestPluginManager:
    """Test plugin manager functionality"""

    def test_plugin_registration(self, plugin_manager, mock_plugin):
        """Test plugin can be registered"""
        plugin_manager.register_plugin(mock_plugin)

        assert len(plugin_manager.get_active_plugins()) == 1
        assert plugin_manager.get_plugin("mock_plugin") == mock_plugin

    def test_plugin_enable_disable(self, plugin_manager, mock_plugin):
        """Test plugin can be enabled and disabled"""
        plugin_manager.register_plugin(mock_plugin)
        assert len(plugin_manager.get_active_plugins()) == 1

        plugin_manager.disable_plugin("mock_plugin")
        assert len(plugin_manager.get_active_plugins()) == 0

        plugin_manager.enable_plugin("mock_plugin")
        assert len(plugin_manager.get_active_plugins()) == 1

    def test_plugin_unregistration(self, plugin_manager, mock_plugin):
        """Test plugin can be unregistered"""
        plugin_manager.register_plugin(mock_plugin)
        assert plugin_manager.get_plugin("mock_plugin") is not None

        plugin_manager.unregister_plugin("mock_plugin")
        assert plugin_manager.get_plugin("mock_plugin") is None

    @pytest.mark.asyncio
    async def test_hook_triggering(self, plugin_manager, mock_plugin, agent_context):
        """Test hooks are triggered correctly"""
        plugin_manager.register_plugin(mock_plugin)

        await plugin_manager.trigger_agent_start(agent_context)
        assert mock_plugin.call_count == 1
        assert len(mock_plugin.agent_start_calls) == 1
        assert mock_plugin.agent_start_calls[0].task_id == "task_1"

    @pytest.mark.asyncio
    async def test_multiple_plugins(self, plugin_manager, agent_context):
        """Test multiple plugins can coexist"""
        plugin1 = MockPlugin("plugin1")
        plugin2 = MockPlugin("plugin2")

        plugin_manager.register_plugin(plugin1)
        plugin_manager.register_plugin(plugin2)

        await plugin_manager.trigger_agent_start(agent_context)

        assert plugin1.call_count == 1
        assert plugin2.call_count == 1

    @pytest.mark.asyncio
    async def test_plugin_priority(self, plugin_manager, agent_context):
        """Test plugins are executed in priority order"""
        plugin1 = MockPlugin("plugin1")
        plugin1.config.priority = 200  # Lower priority

        plugin2 = MockPlugin("plugin2")
        plugin2.config.priority = 50  # Higher priority

        plugin_manager.register_plugin(plugin1)
        plugin_manager.register_plugin(plugin2)

        # Check order
        handlers = plugin_manager._hook_handlers['on_agent_start']
        assert handlers[0] == plugin2  # Higher priority first
        assert handlers[1] == plugin1

    @pytest.mark.asyncio
    async def test_sampling_rate(self, plugin_manager, agent_context):
        """Test sampling rate works"""
        plugin = MockPlugin()
        plugin.config.sampling_rate = 0.0  # Never process

        plugin_manager.register_plugin(plugin)
        await plugin_manager.trigger_agent_start(agent_context)

        assert plugin.call_count == 0  # Should not be called

    @pytest.mark.asyncio
    async def test_error_handling(self, plugin_manager, agent_context):
        """Test plugin errors don't crash the system"""

        class FaultyPlugin(MockPlugin):
            async def on_agent_start(self, context):
                raise ValueError("Test error")

        faulty = FaultyPlugin("faulty")
        normal = MockPlugin("normal")

        plugin_manager.register_plugin(faulty)
        plugin_manager.register_plugin(normal)

        # Should not raise exception
        await plugin_manager.trigger_agent_start(agent_context)

        # Normal plugin should still be called
        assert normal.call_count == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
