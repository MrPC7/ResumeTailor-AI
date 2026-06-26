"""Test configuration — patches heavy dependencies for isolated unit testing."""
from __future__ import annotations

import importlib
import sys
from unittest.mock import MagicMock


def _is_importable(name: str) -> bool:
    """Check if a module is genuinely available (not just stubbed)."""
    try:
        importlib.import_module(name)
        return True
    except ImportError:
        return False


# Stub out heavy third-party modules that aren't needed during unit tests.
# Only stub if the real package isn't installed — this lets integration tests
# that need FastAPI/Starlette work alongside pure-unit tests.
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
    if mod_name not in sys.modules and not _is_importable(mod_name):
        stub = MagicMock()
        if mod_name == "slowapi":
            stub.Limiter = MagicMock()
        if mod_name == "slowapi.util":
            stub.get_remote_address = MagicMock()
        sys.modules[mod_name] = stub
