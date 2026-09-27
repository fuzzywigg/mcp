"""Shared paths and import helpers for offline bakery tests."""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock

LAUNCHMYBAKERY_ROOT = Path(__file__).resolve().parents[1]
ADK_AGENT_DIR = LAUNCHMYBAKERY_ROOT / "adk_agent"
APP_DIR = ADK_AGENT_DIR / "mcp_bakery_app"
DATA_DIR = LAUNCHMYBAKERY_ROOT / "data"
SETUP_DIR = LAUNCHMYBAKERY_ROOT / "setup"
CLEANUP_DIR = LAUNCHMYBAKERY_ROOT / "cleanup"


def load_tools_module():
    """Load tools.py with ADK MCP imports stubbed (no network, no credentials)."""
    # Keep stubs for the process lifetime so unittest reloads stay offline.
    for name in (
        "google.adk",
        "google.adk.tools",
        "google.adk.tools.mcp_tool",
        "google.adk.tools.mcp_tool.mcp_toolset",
        "google.adk.tools.mcp_tool.mcp_session_manager",
    ):
        sys.modules.setdefault(name, MagicMock())

    mcp_toolset_mod = sys.modules["google.adk.tools.mcp_tool.mcp_toolset"]
    mcp_session_mod = sys.modules["google.adk.tools.mcp_tool.mcp_session_manager"]
    if not callable(getattr(mcp_toolset_mod, "MCPToolset", None)):
        mcp_toolset_mod.MCPToolset = MagicMock(name="MCPToolset")
    if not callable(
        getattr(mcp_session_mod, "StreamableHTTPConnectionParams", None)
    ):
        mcp_session_mod.StreamableHTTPConnectionParams = MagicMock(
            name="StreamableHTTPConnectionParams"
        )

    if "mcp_bakery_app" not in sys.modules:
        pkg = types.ModuleType("mcp_bakery_app")
        pkg.__path__ = [str(APP_DIR)]
        sys.modules["mcp_bakery_app"] = pkg

    module_name = "mcp_bakery_app.tools"
    existing = sys.modules.get(module_name)
    if existing is not None and getattr(existing, "MAPS_MCP_URL", None):
        return existing

    spec = importlib.util.spec_from_file_location(
        module_name, APP_DIR / "tools.py"
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load tools.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")
