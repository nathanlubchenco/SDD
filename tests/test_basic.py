"""
Basic tests for SDD system components.
"""

import pytest
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_project_structure():
    """Test that key project files exist."""
    project_root = Path(__file__).parent.parent
    
    # Check core directories exist
    assert (project_root / "src" / "core").exists()
    assert (project_root / "src" / "mcp_servers").exists()
    assert (project_root / "src" / "orchestrator").exists()
    assert (project_root / "examples").exists()
    
    # Check key files exist
    assert (project_root / "requirements.txt").exists()
    assert (project_root / "README.md").exists()
    assert (project_root / "CLAUDE.md").exists()


def test_imports():
    """Test that core modules can be imported."""
    try:
        from src.mcp_servers.base_mcp_server import BaseMCPServer
        from src.orchestrator.iterative_orchestrator import IterativeOrchestrator
        assert True
    except ImportError as e:
        pytest.fail(f"Failed to import core modules: {e}")


def test_demo_script_exists():
    """Test that demo script exists and is readable."""
    demo_path = Path(__file__).parent.parent / "examples" / "iterative_development_demo.py"
    assert demo_path.exists(), "Demo script should exist"
    assert demo_path.is_file(), "Demo script should be a file"


@pytest.mark.asyncio
async def test_iterative_orchestrator_init():
    """Test that IterativeOrchestrator can be initialized."""
    from src.orchestrator.iterative_orchestrator import IterativeOrchestrator
    
    # Create orchestrator without initializing servers (to avoid requiring OpenAI API key)
    orchestrator = IterativeOrchestrator("test_workspace", max_iterations=1)
    
    # Check basic attributes
    assert orchestrator.workspace_path.name == "test_workspace"
    assert orchestrator.max_iterations == 1
    assert orchestrator.iteration_history == []


def test_mcp_servers_exist():
    """Test that all MCP server files exist."""
    mcp_dir = Path(__file__).parent.parent / "src" / "mcp_servers"
    
    expected_servers = [
        "base_mcp_server.py",
        "implementation_server.py",
        "testing_mcp_server.py", 
        "analysis_mcp_server.py",
        "specification_mcp_server.py",
        "docker_mcp_server.py"
    ]
    
    for server_file in expected_servers:
        server_path = mcp_dir / server_file
        assert server_path.exists(), f"MCP server {server_file} should exist"