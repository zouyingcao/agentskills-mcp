# flake8: noqa: E402
# pylint: disable=wrong-import-position

"""Public package interface for the AgentSkills MCP library.

This module exposes the high-level objects that users are expected to import
from :mod:`agentskills_mcp`. It also sets the :envvar:`FLOW_APP_NAME` environment
variable so that the underlying FlowLLM framework can correctly associate
configuration and logging with this application.
"""

import os

# Hint FlowLLM about the logical application name. This is used by the
# framework to locate configuration files and to tag logs/telemetry.
os.environ["FLOW_APP_NAME"] = "AgentSkillsMCP"

from . import core
from . import config

from .main import AgentSkillsMcpApp

__all__ = [
    "core",
    "config",
    "AgentSkillsMcpApp",
]

# Library version. Keep in sync with the project metadata.
__version__ = "0.1.1"
