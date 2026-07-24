"""Shared test setup.

The bot's data-access layer imports heavy third-party clients (openai / pinecone
/ pymongo) at module load, which aren't needed to test the learning integration.
They're stubbed with lightweight mocks so the router module imports without those
packages installed.
"""

from __future__ import annotations

import os
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock

# --- make the bot package importable -------------------------------------
_BOT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BOT_ROOT))


def _stub(name: str) -> None:
    """Register a MagicMock module so `import <name>` succeeds in tests."""
    if name not in sys.modules:
        mod = types.ModuleType(name)
        mod.__getattr__ = lambda attr: MagicMock()  # type: ignore[attr-defined]
        sys.modules[name] = mod


# Heavy clients the learning integration does not exercise.
for _mod in ("openai", "pinecone", "pdfplumber"):
    _stub(_mod)

# pymongo / bson need a couple of concrete symbols the modules reference.
if "pymongo" not in sys.modules:
    pymongo = types.ModuleType("pymongo")
    pymongo.MongoClient = MagicMock()  # type: ignore[attr-defined]
    sys.modules["pymongo"] = pymongo
if "bson" not in sys.modules:
    bson = types.ModuleType("bson")
    bson.ObjectId = MagicMock()  # type: ignore[attr-defined]
    sys.modules["bson"] = bson

# A base URL so the integration reports as enabled by default in tests; the
# actual HTTP calls are always monkeypatched, never made for real.
os.environ.setdefault("LEARNINGS_BASE_URL", "http://learnings.test")
