"""Forward-held-out model arena for the Recaman next obstruction bit."""

from __future__ import annotations

import math
from collections import defaultdict
from functools import lru_cache

from recaman import UP_BLOCKED, generate


def _fit_table(rows: list[dict], key: str) -> tuple[dict[object, float], float]:
    counts: dict[object, list[int]] = defaultdict(lambda: [0, 0])
    positives = 0
    for row in rows:
        bucket = row[key]
        counts[bucket][1] += 1
        counts[bucket][0] += int(row["target"])
        positives += int(row["target"])
    global_probability = (positives + 1) / (len(rows) + 2)
    table = {
        bucket: (positive + 1) / (total + 2)
        for bucket, (positive, total) in counts.items()
    }
    return table, global_probability


def _predict(table: dict[object, float], fallback: float, value: object) -> float:
    return min(max(table.get(value, fallback), 1e-6), 1 - 1e-6)


def _log_loss(targets: list[int], probabilities: list[float]) -> float:
    return -sum(
        target * math.log(probability) + (1 - target) * math.log(1 - probability)
        for target, probability in zip(targets, probabilities)
    ) / len(targets)


def _auc(targets: list[int], scores: list[float]) -> float:
    positives = sum(targets)
    negatives = len(targets) - positives
    if not positives or not negatives:
        return 0.5
    ordered = sorted(zip(scores, targets), key=lambda pair: pair[0])
    rank_sum = 0.0
    index = 0
    while index < len(ordered):
        end = index + 1
        while end < len(ordered) and ordered[end][0] == ordered[index][0]:
            end += 1
        average_rank = (index + 1 + end) / 2
        rank_sum += average_rank * sum(target for _, target in ordered[index:end])
        index = end
    return (rank_sum - positives * (positives + 1) / 2) / (positives * negatives)


def _metrics(targets: list[int], probabilities: list[float]) -> dict[str, float]:
    loss = _log_loss(targets, probabilities)
    return {
        "auc": _auc(targets, probabilities),
        "accuracy": sum((probability >= 0.5) == bool(target) for target, probability in zip(targets, probabilities)) / len(targets),
        "log_loss": loss,
        "bits_per_step": loss / math.log(2),
        "brier": sum((probability - target) ** 2 for target, probability in zip(targets, probabilities)) / len(targets),
    }


def _records(steps: int, base: int, modulus: int) -> list[dict]:
    run = generate(steps)
    seen = {run.terms[0]}
    last_slip = 1
    residue = base % modulus
    records: list[dict] = []
    for step in range(1, steps + 1):
        previous_value = run.terms[step - 1]
        candidate = previous_value - step
        previous_bit = run.bit(step - 1) if step > 1 else UP_BLOCKED
        since_slip = max(step - last_slip, 1)
        sign = 1 if step % 2 else -1
        residue = pow((sign * base) % modulus, residue + 1, modulus)
        target = run.bit(step)
        records.append(
            {
                "step": step,
                "target": target,
                "previous_bit": previous_bit,
                "candidate": candidate,
                "collision": candidate <= 0 or candidate in seen,
                "alternation_key": previous_bit,
                "arithmetic_key": (
                    int(candidate > 0),
                    max(-1, min(candidate // max(step // 8, 1), 16)),
                ),
                "modulo_key": (-1, step % 6) if candidate <= 0 else (candidate % 30, step % 6),
                "phase_key": (previous_bit, min(since_slip.bit_length(), 14)),
                "tower_key": (int(residue >= modulus / 2), step % 2),
            }
        )
        if step > 1 and target == previous_bit:
            last_slip = step
        seen.add(run.terms[step])
    return records[1:]


@lru_cache(maxsize=12)
def evaluate_arena(steps: int = 100_000, base: int = 3, modulus: int = 210) -> dict:
    """Fit on the first 80% and score one untouched future block."""
    steps = max(10_000, min(int(steps), 200_000))
    base = max(2, min(abs(int(base)), 10_000))
    modulus = max(3, min(abs(int(modulus)), 10_000))
    records = _records(steps, base, modulus)
    split = int(len(records) * 0.8)
    train, test = records[:split], records[split:]
    targets = [int(row["target"]) for row in test]

    definitions = [
        ("Historical inference champion", "alternation_key", "previous obstruction bit"),
        ("Arithmetic process model", "arithmetic_key", "candidate sign and scale"),
        ("Phase-slip hunter", "phase_key", "previous bit and time since last slip"),
        ("Modulo hunter", "modulo_key", "candidate mod 30 and step mod 6"),
        ("Tower scout", "tower_key", "signed modular-power shadow"),
    ]
    agents: list[dict] = []
    predictions: dict[str, list[float]] = {}
    train_predictions: dict[str, list[float]] = {}
    for name, key, feature in definitions:
        table, fallback = _fit_table(train, key)
        test_probabilities = [_predict(table, fallback, row[key]) for row in test]
        fitted_probabilities = [_predict(table, fallback, row[key]) for row in train]
        predictions[name] = test_probabilities
        train_predictions[name] = fitted_probabilities
        agents.append(
            {
                "name": name,
                "target": "next blocked/free bit",
                "feature": feature,
                "status": "forward-held-out",
                **_metrics(targets, test_probabilities),
            }
        )

    train_targets = [int(row["target"]) for row in train]
    uniform_loss = math.log(2)
    raw_weights = {
        name: max(0.01, uniform_loss - _log_loss(train_targets, probabilities))
        for name, probabilities in train_predictions.items()
    }
    weight_total = sum(raw_weights.values())
    weights = {name: weight / weight_total for name, weight in raw_weights.items()}
    ensemble = [
        sum(weights[name] * predictions[name][index] for name in predictions)
        for index in range(len(test))
    ]
    agents.append(
        {
            "name": "Forward ensemble",
            "target": "next blocked/free bit",
            "feature": "train-weighted combination of inferred agents",
            "status": "forward-held-out",
            "weights": weights,
            **_metrics(targets, ensemble),
        }
    )

    base_rate = (sum(train_targets) + 1) / (len(train_targets) + 2)
    skeptic = [base_rate] * len(test)
    agents.append(
        {
            "name": "Skeptic / prevalence control",
            "target": "next blocked/free bit",
            "feature": "training prevalence only",
            "status": "negative control",
            **_metrics(targets, skeptic),
        }
    )
    oracle = [0.999 if target else 0.001 for target in targets]
    agents.append(
        {
            "name": "Exact visited-set oracle",
            "target": "next blocked/free bit",
            "feature": "candidate collision with complete history",
            "status": "oracle reference; not inferred",
            **_metrics(targets, oracle),
        }
    )

    inferred = [agent for agent in agents if agent["status"] == "forward-held-out"]
    champion = min(inferred, key=lambda agent: agent["bits_per_step"])
    return {
        "steps": steps,
        "train_steps": len(train),
        "test_steps": len(test),
        "base": base,
        "modulus": modulus,
        "target": "b(n): 1 = backward move blocked, 0 = backward move free",
        "split": "first 80% fit / final 20% untouched test",
        "agents": agents,
        "champion": champion["name"],
        "champion_bits_per_step": champion["bits_per_step"],
        "champion_auc": champion["auc"],
        "uniform_bits_per_step": 1.0,
        "tower_added_to_ensemble": weights["Tower scout"],
        "leakage_boundary": (
            "The exact collision oracle is displayed only as a ceiling. It is never an ensemble input."
        ),
    }


def evidence_registry(measurements: dict) -> list[dict]:
    benchmark = measurements["signed_tower"]["benchmark"]
    return [
        {
            "model": "Value-side gap dynamics D",
            "target": "gap between catalogued obstruction events",
            "auc": measurements["value_side"]["dataset_d"]["mean_auc"],
            "role": "separate value-side champion; not mixed with next-bit labels",
        },
        {
            "model": "Arithmetic-only process tower",
            "target": "next blocked/free bit",
            "auc": benchmark["auc_without_prev_is_down"],
            "role": "process inference without previous sign",
        },
        {
            "model": "Full predecision process tower",
            "target": "next blocked/free bit",
            "auc": benchmark["auc_full_predecision"],
            "role": "dominated by near-alternation; retained and labelled",
        },
        {
            "model": "Visited-set collision oracle",
            "target": "next blocked/free bit",
            "auc": benchmark["auc_oracle_visited_set"],
            "role": "exact ceiling; excluded from inferred ensembles",
        },
    ]
