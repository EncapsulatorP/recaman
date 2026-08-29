"""Make the Space importable the way Hugging Face imports it.

The Space is deployed from `apps/space/` as its own repository root, so its
modules are top-level there (`import predictor`, not `import apps.space.predictor`).
Putting that directory on `sys.path` keeps the tests honest about the layout
the deployed app actually runs under.
"""

from __future__ import annotations

import sys
from pathlib import Path


SPACE_DIR = Path(__file__).resolve().parents[1] / "apps" / "space"

if str(SPACE_DIR) not in sys.path:
    sys.path.insert(0, str(SPACE_DIR))
