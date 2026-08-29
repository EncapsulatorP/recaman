"""Tests for the combined long-lasting-obstruction and tower Space."""

from __future__ import annotations

import importlib.util
import json
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
from arena_figures import arena_scoreboard
from hole_catalogue import load_catalogue
from model_arena import (
    evaluate_arena,
    evaluate_replay,
    evaluate_weekly_league,
    evidence_registry,
)
from tower_figures import (
    evolution_race_svg,
    hole_density_svg,
    power_probe_svg,
    rank_tower_svg,
    signed_tower_svg,
)
from tower_lab import (
    MEASUREMENTS,
    MEASUREMENTS_PATH,
    evolution_rollout,
    hole_status,
    modular_power_probe,
    rank_tower,
    signed_snapshot,
    signed_window,
)

ROOT = Path(__file__).resolve().parents[1]


def test_space_catalogue_is_synchronised_and_structurally_sound() -> None:
    catalogue = load_catalogue()
    assert catalogue.event_count == 3_102
    assert catalogue.singleton_count == 2_535
    assert catalogue.range_count == 567
    assert catalogue.integer_count == 1_277_399
    assert catalogue.longest_run == 368_058
    assert (ROOT / "apps" / "space" / "holes.txt").read_bytes() == (ROOT / "obstructions.txt").read_bytes()


def test_hole_status_distinguishes_membership_from_scope() -> None:
    first = hole_status(930_058)
    assert first["catalogued"] is True
    assert first["event_start"] == 930_058
    inside = hole_status(930_059)
    assert inside["status"] == "not_catalogued"
    assert inside["distance_to_nearest"] == 1
    assert hole_status(10)["status"] == "outside"


def test_signed_tower_reconstructs_the_sequence() -> None:
    for step in (24, 682, 20_000):
        snapshot, run = signed_snapshot(step)
        assert snapshot.identity_verified
        assert snapshot.identity_value == snapshot.value == run.terms[step]
        assert snapshot.signed_step == (step if snapshot.obstruction_bit else -step)
        assert signed_window(run, step)[-1]["contribution"] == snapshot.signed_step


def test_saved_rank_tower_preserves_the_null_comparison() -> None:
    level_seven = rank_tower(7)
    assert level_seven["artifact_free"] is True
    assert level_seven["real_rank"] == 221
    assert level_seven["random_rank"] == 255
    assert level_seven["alternating_rank"] == 2
    assert level_seven["rank_deficit_from_random"] == 34
    assert rank_tower(8)["artifact_free"] is False


def test_modular_power_probe_is_bounded_deterministic_and_controlled() -> None:
    first = modular_power_probe(3, 210, 128)
    second = modular_power_probe(3, 210, 128)
    assert first == second
    assert len(first["flipped_residues"]) == 128
    assert len(first["fixed_residues"]) == 128
    assert all(0 <= value < 210 for value in first["flipped_residues"])
    assert 0 <= first["flipped_agreement"] <= 1
    assert 0 <= first["fixed_agreement"] <= 1
    assert "multiple testing" in first["selection_warning"].lower()


def test_evolution_rollout_is_free_running_and_keeps_chaffin_boundary_honest() -> None:
    payload = evolution_rollout(20_000, 192, 3, 210)
    assert payload["seed_step"] == 20_000
    assert payload["end_step"] == 20_192
    assert len(payload["rows"]) == 192
    assert payload["free_running"] is True
    assert 0 <= payload["alternating_bit_agreement"] <= 1
    assert 0 <= payload["power_bit_agreement"] <= 1
    assert payload["chaffin_frontier"]["last_catalogued_hole"] == 4_293_242_951
    assert payload["chaffin_frontier"]["continuation_available"] is False
    assert "visited-range state" in payload["chaffin_frontier"]["reason"]

    first = payload["rows"][0]
    assert first["step"] == 20_001
    assert first["exact_bit"] in (0, 1)
    assert first["alternating_bit"] in (0, 1)
    assert first["power_bit"] in (0, 1)


def test_model_arena_uses_a_chronological_holdout_and_keeps_oracle_separate() -> None:
    payload = evaluate_arena(20_000, 3, 210)
    assert payload["train_steps"] + payload["test_steps"] == 19_999
    assert payload["test_steps"] > 0
    assert payload["champion"]
    assert 0 < payload["champion_bits_per_step"] < 1
    assert 0 <= payload["tower_added_to_ensemble"] <= 1
    names = {agent["name"] for agent in payload["agents"]}
    assert {
        "Tower scout",
        "Tower-augmented challenger",
        "Modulo hunter",
        "Phase-slip hunter",
        "Forward ensemble",
    } <= names
    oracle = next(agent for agent in payload["agents"] if agent["name"] == "Exact visited-set oracle")
    assert "not inferred" in oracle["status"]
    ensemble = next(agent for agent in payload["agents"] if agent["name"] == "Forward ensemble")
    assert "Exact visited-set oracle" not in ensemble["weights"]


def test_blind_replay_exposes_only_the_requested_test_prefix() -> None:
    payload = evaluate_replay(20_000, 3, 210, 64)
    assert payload["revealed"] == 64
    assert len(payload["history"]) == 64
    assert payload["hidden_remaining"] == payload["test_steps"] - 64
    assert payload["history"][-1]["step"] == payload["current"]["step"]
    assert all("phase_slip_ap" in row for row in payload["scoreboard"])
    assert "no future labels" in payload["protocol"].lower()


def test_weekly_league_selects_before_opening_the_promotion_block() -> None:
    payload = evaluate_weekly_league(
        30_000,
        candidates=((2, 97), (3, 210)),
    )
    assert payload["protocol"].startswith("60% fit / 20% challenger selection")
    assert len(payload["validation_search"]) == 2
    assert payload["decision"] in {"PROMOTE CHALLENGER", "KEEP CHAMPION"}
    assert payload["champion"]["phase_slip_ap"] >= 0
    assert payload["challenger"]["phase_slip_ap"] >= 0


def test_evidence_registry_labels_value_and_process_targets_separately() -> None:
    registry = evidence_registry(MEASUREMENTS)
    assert {row["target"] for row in registry} == {
        "gap between catalogued obstruction events",
        "next blocked/free bit",
    }
    assert next(row for row in registry if row["model"] == "Value-side gap dynamics D")["auc"] == pytest.approx(0.7586356315)


def test_new_figures_are_well_formed_svg() -> None:
    snapshot, run = signed_snapshot(2_000)
    probe = modular_power_probe(3, 210, 64)
    evolution = evolution_rollout(2_000, 64, 3, 210)
    svgs = (
        hole_density_svg(load_catalogue()),
        signed_tower_svg(signed_window(run, snapshot.step)),
        rank_tower_svg(MEASUREMENTS, 7),
        power_probe_svg(probe),
        evolution_race_svg(evolution),
        arena_scoreboard(evaluate_arena(10_000, 3, 210)),
    )
    for svg in svgs:
        root = ET.fromstring(svg)
        assert root.tag.endswith("svg")
        assert root.get("role") == "img"


def test_compact_measurements_match_their_builder() -> None:
    spec = importlib.util.spec_from_file_location(
        "build_obstruction_tower_space",
        ROOT / "scripts" / "build_obstruction_tower_space.py",
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.build() == json.loads(MEASUREMENTS_PATH.read_text(encoding="utf-8"))
