"""Hugging Face Space-card constraints that fail before deployment."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CARDS = (
    ROOT / "apps" / "space" / "README.md",
    ROOT / "apps" / "claude_ai_holes" / "README.md",
    ROOT / "apps" / "comparison" / "README.md",
)
ALLOWED_COLOURS = {"red", "yellow", "green", "blue", "indigo", "purple", "pink", "gray"}


def _frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    _, block, _ = text.split("---", 2)
    return {
        key.strip(): value.strip().strip('"')
        for line in block.splitlines()
        if ":" in line
        for key, value in [line.split(":", 1)]
    }


def test_space_cards_obey_hugging_face_metadata_limits() -> None:
    for card in CARDS:
        metadata = _frontmatter(card)
        assert metadata["colorFrom"] in ALLOWED_COLOURS
        assert metadata["colorTo"] in ALLOWED_COLOURS
        assert len(metadata["short_description"]) <= 60
        assert metadata["sdk"] == "gradio"
        assert metadata["app_file"] == "app.py"
