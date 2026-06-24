"""Test configuration — patches heavy dependencies for isolated unit testing."""
from __future__ import annotations

import sys
from types import ModuleType
from unittest.mock import MagicMock

# Stub out heavy third-party modules that aren't needed during unit tests.
# This prevents import-time failures when the full dependency tree isn't installed.
_STUBS = [
    "slowapi",
    "slowapi.util",
    "starlette",
    "starlette.config",
    "google",
    "google.generativeai",
    "google.api_core",
    "google.api_core.exceptions",
    "groq",
]

for mod_name in _STUBS:
    if mod_name not in sys.modules:
        stub = MagicMock()
        # slowapi needs Limiter class and get_remote_address function
        if mod_name == "slowapi":
            stub.Limiter = MagicMock()
        if mod_name == "slowapi.util":
            stub.get_remote_address = MagicMock()
        sys.modules[mod_name] = stub
