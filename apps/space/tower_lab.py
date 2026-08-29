"""Exact signed towers, saved rank towers, and exploratory power iterators."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path

from hole_catalogue import load_catalogue
from recaman import DOWN_FREE, UP_BLOCKED, RecamanRun, generate

HERE = Path(__file__).resolve().parent
MEASUREMENTS_PATH = HERE / "tower_measurements.json"
MEASUREMENTS = json.loads(MEASUREMENTS_PATH.read_text(encoding="utf-8"))
CATALOGUE = load_catalogue()

CHAFFIN_SOURCE_URL = "https://benchaffin.com/recaman/recaman.html"
CHAFFIN_COMPUTED_HORIZON = "over 10^612 terms"
CHAFFIN_SMALLEST_MISSING = 852_655
CHAFFIN_HOLE_LIMIT = 2**32


@lru_cache(maxsize=24)
def run_prefix(steps: int) -> RecamanRun:
    return generate(steps)


@dataclass(frozen=True)
class SignedTowerSnapshot:
    step: int
    previous_value: int
    candidate: int
    value: int
    obstruction_bit: int
    signed_step: int
    move: str
    reason: str
    triangular_envelope: int
    down_count: int
    down_sum: int
    identity_value: int
    identity_verified: bool
    phase_slip: bool

    def to_dict(self) -> dict:
        return asdict(self)


def signed_snapshot(step: int) -> tuple[SignedTowerSnapshot, RecamanRun]:
    step = max(1, min(int(step), 200_000))
    run = run_prefix(step)
    bit = run.bit(step)
    candidate = run.terms[step - 1] - step
    down_indices = [index for index, value in enumerate(run.bits, start=1) if value == DOWN_FREE]
    down_sum = sum(down_indices)
    triangular = step * (step + 1) // 2
    identity_value = triangular - 2 * down_sum

    if bit == DOWN_FREE:
        move = "−"
        reason = "candidate was positive and unvisited"
        signed_step = -step
    else:
        move = "+"
        reason = "candidate was non-positive" if candidate <= 0 else "candidate was already visited"
        signed_step = step

    snapshot = SignedTowerSnapshot(
        step=step,
        previous_value=run.terms[step - 1],
        candidate=candidate,
        value=run.terms[step],
        obstruction_bit=bit,
        signed_step=signed_step,
        move=move,
        reason=reason,
        triangular_envelope=triangular,
        down_count=len(down_indices),
        down_sum=down_sum,
        identity_value=identity_value,
        identity_verified=identity_value == run.terms[step],
        phase_slip=step > 1 and run.bit(step) == run.bit(step - 1),
    )
    return snapshot, run


def signed_window(run: RecamanRun, step: int, width: int = 72) -> list[dict[str, int | bool]]:
    first = max(1, step - width + 1)
    return [
        {
            "step": index,
            "bit": run.bit(index),
            "sign": 1 if run.bit(index) == UP_BLOCKED else -1,
            "contribution": index if run.bit(index) == UP_BLOCKED else -index,
            "value": run.terms[index],
            "phase_slip": index > 1 and run.bit(index) == run.bit(index - 1),
        }
        for index in range(first, step + 1)
    ]


def rank_tower(level: int) -> dict:
    tower = MEASUREMENTS["power_of_two_tower"]
    level = max(0, min(int(level), len(tower["real"]) - 1))

    def row(name: str) -> dict:
        return tower[name][level]

    real = row("real")
    random = row("null_random")
    alternating = row("pure_alternation")
    return {
        "level": level,
        "stride": 2**level,
        "real_rank": real["rank"],
        "random_rank": random["rank"],
        "alternating_rank": alternating["rank"],
        "rank_deficit_from_random": random["rank"] - real["rank"],
        "artifact_free": level <= tower["artifact_free_max_level"],
        "vec_dim": tower["vec_dim"],
        "stream_length": tower["stream_length"],
    }


def modular_power_probe(base: int, modulus: int, layers: int) -> dict:
    """Compare a sign-flipping modular power iterator with a fixed-sign control.

    This is deliberately a bounded modular recurrence, not an uncomputable
    literal tetration value:

        r_0 = |base| mod m
        r_(h+1) = ((-1)^h base)^(r_h + 1) mod m

    The upper/lower-half shadow of each residue is compared with the real
    Recamán obstruction bit at the same layer. It is a hypothesis probe, not a
    fitted predictor.
    """
    base = max(2, min(abs(int(base)), 10_000))
    modulus = max(3, min(abs(int(modulus)), 10_000))
    layers = max(8, min(int(layers), 512))

    flipped = base % modulus
    control = flipped
    flipped_residues: list[int] = []
    control_residues: list[int] = []
    signs: list[int] = []

    for layer in range(1, layers + 1):
        sign = 1 if layer % 2 else -1
        flipped = pow((sign * base) % modulus, flipped + 1, modulus)
        control = pow(base % modulus, control + 1, modulus)
        signs.append(sign)
        flipped_residues.append(flipped)
        control_residues.append(control)

    bits = list(run_prefix(layers).bits)
    threshold = modulus / 2
    flipped_shadow = [int(residue >= threshold) for residue in flipped_residues]
    control_shadow = [int(residue >= threshold) for residue in control_residues]

    def agreement(shadow: list[int]) -> float:
        return sum(left == right for left, right in zip(shadow, bits)) / layers

    majority = max(sum(bits), layers - sum(bits)) / layers
    return {
        "base": base,
        "modulus": modulus,
        "layers": layers,
        "definition": "r[h+1] = ((-1)^h * base)^(r[h] + 1) mod modulus",
        "signs": signs,
        "flipped_residues": flipped_residues,
        "fixed_residues": control_residues,
        "flipped_shadow": flipped_shadow,
        "fixed_shadow": control_shadow,
        "recaman_bits": bits,
        "flipped_agreement": agreement(flipped_shadow),
        "fixed_agreement": agreement(control_shadow),
        "majority_baseline": majority,
        "selection_warning": (
            "Interactive parameter choice is multiple testing. Agreement is descriptive only "
            "until parameters are frozen and evaluated on a held-out horizon."
        ),
    }


def evolution_rollout(seed_step: int, horizon: int, base: int, modulus: int) -> dict:
    """Race exact Recaman evolution against two autonomous sign models.

    All lanes inherit the same exact state at ``seed_step``. From the next
    layer onward, the deterministic lane retains the full visited set while
    each model must consume its own previous predictions. This free-running
    setup makes compounding error visible instead of quietly teacher-forcing
    every prediction from the true previous bit.

    Chaffin's final published hole is included as provenance, but is not used
    as a Recaman checkpoint: a hole value alone does not contain the visited
    set required to continue the deterministic recurrence.
    """
    horizon = max(16, min(int(horizon), 512))
    seed_step = max(24, min(int(seed_step), 200_000 - horizon))
    base = max(2, min(abs(int(base)), 10_000))
    modulus = max(3, min(abs(int(modulus)), 10_000))

    run = run_prefix(seed_step + horizon)
    seed_value = run.terms[seed_step]
    seed_bit = run.bit(seed_step)

    alternating_value = seed_value
    alternating_previous_bit = seed_bit
    alternating_seen = set(run.terms[: seed_step + 1])

    power_value = seed_value
    power_seen = set(alternating_seen)
    power_residue = base % modulus
    for layer in range(1, seed_step + 1):
        sign = 1 if layer % 2 else -1
        power_residue = pow((sign * base) % modulus, power_residue + 1, modulus)

    rows: list[dict[str, int | bool]] = []
    alternating_matches = 0
    power_matches = 0
    alternating_illegal_downs = 0
    power_illegal_downs = 0

    for step in range(seed_step + 1, seed_step + horizon + 1):
        exact_bit = run.bit(step)
        exact_value = run.terms[step]

        alternating_bit = 1 - alternating_previous_bit
        alternating_candidate = alternating_value - step
        alternating_legal = alternating_candidate > 0 and alternating_candidate not in alternating_seen
        if alternating_bit == DOWN_FREE and not alternating_legal:
            alternating_illegal_downs += 1
        alternating_value += step if alternating_bit == UP_BLOCKED else -step
        alternating_seen.add(alternating_value)
        alternating_previous_bit = alternating_bit

        sign = 1 if step % 2 else -1
        power_residue = pow((sign * base) % modulus, power_residue + 1, modulus)
        power_bit = int(power_residue >= modulus / 2)
        power_candidate = power_value - step
        power_legal = power_candidate > 0 and power_candidate not in power_seen
        if power_bit == DOWN_FREE and not power_legal:
            power_illegal_downs += 1
        power_value += step if power_bit == UP_BLOCKED else -step
        power_seen.add(power_value)

        alternating_matches += int(alternating_bit == exact_bit)
        power_matches += int(power_bit == exact_bit)
        rows.append(
            {
                "step": step,
                "exact_value": exact_value,
                "exact_bit": exact_bit,
                "alternating_value": alternating_value,
                "alternating_bit": alternating_bit,
                "alternating_legal": alternating_legal,
                "power_value": power_value,
                "power_bit": power_bit,
                "power_residue": power_residue,
                "power_legal": power_legal,
            }
        )

    def first_divergence(key: str) -> int | None:
        return next((int(row["step"]) for row in rows if row[key] != row["exact_bit"]), None)

    exact_final = int(rows[-1]["exact_value"])
    alternating_final = int(rows[-1]["alternating_value"])
    power_final = int(rows[-1]["power_value"])
    return {
        "seed_step": seed_step,
        "seed_value": seed_value,
        "seed_bit": seed_bit,
        "horizon": horizon,
        "end_step": seed_step + horizon,
        "base": base,
        "modulus": modulus,
        "rows": rows,
        "exact_final_value": exact_final,
        "alternating_final_value": alternating_final,
        "power_final_value": power_final,
        "alternating_final_error": alternating_final - exact_final,
        "power_final_error": power_final - exact_final,
        "alternating_bit_agreement": alternating_matches / horizon,
        "power_bit_agreement": power_matches / horizon,
        "alternating_first_divergence": first_divergence("alternating_bit"),
        "power_first_divergence": first_divergence("power_bit"),
        "alternating_illegal_downs": alternating_illegal_downs,
        "power_illegal_downs": power_illegal_downs,
        "free_running": True,
        "chaffin_frontier": {
            "last_catalogued_hole": CATALOGUE.span_end,
            "hole_search_limit_exclusive": CHAFFIN_HOLE_LIMIT,
            "computed_horizon": CHAFFIN_COMPUTED_HORIZON,
            "smallest_missing_after_horizon": CHAFFIN_SMALLEST_MISSING,
            "source_url": CHAFFIN_SOURCE_URL,
            "continuation_available": False,
            "reason": (
                "The published hole value is not a sequence checkpoint. Exact continuation "
                "requires Chaffin's full visited-range state."
            ),
        },
    }


def hole_status(value: int) -> dict:
    value = int(value)
    status, containing, nearest = CATALOGUE.locate(value)
    payload: dict[str, int | str | bool | None] = {
        "value": value,
        "status": status,
        "catalogue_start": CATALOGUE.span_start,
        "catalogue_end": CATALOGUE.span_end,
        "catalogued": status == "catalogued",
        "event_start": containing.start if containing else None,
        "event_end": containing.end if containing else None,
        "event_length": containing.length if containing else None,
        "nearest_event_start": nearest.start if nearest else None,
        "nearest_event_end": nearest.end if nearest else None,
    }
    if nearest and status == "not_catalogued":
        payload["distance_to_nearest"] = min(abs(value - nearest.start), abs(value - nearest.end))
    return payload
