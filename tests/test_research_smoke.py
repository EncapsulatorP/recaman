from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType


ROOT = Path(__file__).resolve().parents[1]


def load_script(name: str, relative_path: str) -> ModuleType:
    path = ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_recaman_prefix_matches_reference_values() -> None:
    wheel = load_script("recaman_wheel_validator_test", "scripts/recaman_wheel_validator.py")
    values, bits, _ = wheel.recaman(20)
    assert list(values) == [
        0, 1, 3, 6, 2, 7, 13, 20, 12, 21, 11,
        22, 10, 23, 9, 24, 8, 25, 43, 62, 42,
    ]
    assert len(bits) == 21


def test_density_accounting_invariants() -> None:
    density = load_script("recaman_densities_test", "scripts/densities.py")
    snapshots, visited = density.collect_snapshots([100, 1_000])

    assert len(snapshots) == 2
    assert visited == sorted(set(visited))
    for snapshot in snapshots:
        assert snapshot.obstructions + snapshot.free_moves == snapshot.step
        assert snapshot.revisit_hits + snapshot.boundary_blocks == snapshot.obstructions
        assert 0.0 <= snapshot.fill_density <= 1.0
        assert 0.0 <= snapshot.hole_density <= 1.0
        assert snapshot.fill_density + snapshot.hole_density == 1.0
