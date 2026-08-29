"""Make each Space importable the way Hugging Face imports it.

A Space is deployed from its own directory as that repository's root, so its
modules are top-level there (`import predictor`, not `import apps.space.predictor`).
Putting those directories on `sys.path` keeps the tests honest about the layout
the deployed apps actually run under.

Both Spaces are on the path at once, which is safe because their module names
are distinct — `figures`/`predictor`/`recaman` in the next-move Space,
`hole_figures`/`holes`/`sequence` in the Claude.ai holes Space. Only `app.py`
is shared, and no test imports it by module name; CI imports each Space's app
in its own job with a single directory on the path.
"""

from __future__ import annotations

import sys
from pathlib import Path


APPS = Path(__file__).resolve().parents[1] / "apps"
SPACE_DIRS = (APPS / "space", APPS / "claude_ai_holes")

for directory in SPACE_DIRS:
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))
