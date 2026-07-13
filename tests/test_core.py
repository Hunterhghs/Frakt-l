"""Basic tests for Fraktál."""
import os
import sys
from pathlib import Path

# Ensure src is importable
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_import():
    """Package imports without error."""
    import fraktal
    assert fraktal.__version__ == "0.1.0"


def test_config_defaults():
    """Config loads with sensible defaults."""
    from fraktal.config import FraktalConfig
    cfg = FraktalConfig.load(workspace="/tmp")
    assert cfg.provider == "deepseek"
    assert cfg.model == "deepseek-chat"
    assert cfg.max_iterations > 0
    assert cfg.memory_backend in ("sqlite", "json")


def test_model_catalog():
    """Built-in models are defined."""
    from fraktal.config import BUILTIN_MODELS, get_model_info
    assert "deepseek-chat" in BUILTIN_MODELS
    assert "deepseek-reasoner" in BUILTIN_MODELS
    info = get_model_info("deepseek-chat")
    assert info.name == "DeepSeek V3"
    assert info.context_window == 128000


def test_tool_registry():
    """Tool registry works."""
    from fraktal.tools.base import ToolRegistry
    from fraktal.tools.filesystem import ReadFileTool
    from fraktal.config import FraktalConfig

    cfg = FraktalConfig(workspace="/tmp")
    registry = ToolRegistry()
    registry.register(ReadFileTool(cfg))
    assert registry.get("read_file") is not None
    assert len(registry.list_tools()) == 1


def test_agent_definitions():
    """Agent definitions load correctly."""
    from fraktal.agents import load_agent, load_persona, load_role, list_agents, list_personas, list_roles

    agents = list_agents()
    assert "general-purpose" in agents
    assert "plan" in agents

    agent = load_agent("general-purpose")
    assert agent.name == "general-purpose"
    assert len(agent.body) > 0

    personas = list_personas()
    assert "implementer" in personas
    assert "reviewer" in personas

    persona = load_persona("implementer")
    assert persona.name == "implementer"
    assert len(persona.instructions) > 0

    roles = list_roles()
    assert "implementer" in roles

    role = load_role("implementer")
    assert role.name == "implementer"


def test_playbooks():
    """Playbooks load correctly."""
    from fraktal.playbooks import load_playbook, list_playbooks
    playbooks = list_playbooks()
    assert "dashboard" in playbooks
    assert "report" in playbooks
    assert "website" in playbooks

    content = load_playbook("dashboard")
    assert "KPI" in content


def test_prompts():
    """Prompts load correctly."""
    from fraktal.prompts import load_prompt, AGENT_ROLES
    assert "orchestrator" in AGENT_ROLES
    prompt = load_prompt("orchestrator")
    assert "Orchestrator" in prompt


def test_memory():
    """Memory store works."""
    from fraktal.memory import create_memory
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        mem = create_memory("json", Path(tmp) / "memory.json")
        entry_id = mem.remember("Test fact", category="note", tags=["test"])
        assert entry_id > 0

        entry = mem.recall(entry_id)
        assert entry is not None
        assert entry.content == "Test fact"

        results = mem.search("Test")
        assert len(results) >= 1

        recent = mem.recent(limit=5)
        assert len(recent) >= 1
