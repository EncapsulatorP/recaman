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


def _average_precision(targets: list[int], scores: list[float]) -> float:
    positives = sum(targets)
    if not positives:
        return 0.0
    ranked = sorted(zip(scores, targets), reverse=True)
    found = 0
    precision_sum = 0.0
    for rank, (_, target) in enumerate(ranked, start=1):
        if target:
            found += 1
            precision_sum += found / rank
    return precision_sum / positives


def _metrics(
    targets: list[int],
    probabilities: list[float],
    previous_bits: list[int] | None = None,
) -> dict[str, float]:
    loss = _log_loss(targets, probabilities)
    predicted = [probability >= 0.5 for probability in probabilities]
    true_positives = sum(bool(target) and guess for target, guess in zip(targets, predicted))
    predicted_positives = sum(predicted)
    positives = sum(targets)
    metrics = {
        "auc": _auc(targets, probabilities),
        "accuracy": sum(guess == bool(target) for target, guess in zip(targets, predicted)) / len(targets),
        "precision": true_positives / predicted_positives if predicted_positives else 0.0,
        "recall": true_positives / positives if positives else 0.0,
        "log_loss": loss,
        "bits_per_step": loss / math.log(2),
        "brier": sum((probability - target) ** 2 for target, probability in zip(targets, probabilities)) / len(targets),
    }
    if previous_bits is not None:
        slip_targets = [int(target == previous) for target, previous in zip(targets, previous_bits)]
        slip_scores = [
            probability if previous else 1 - probability
            for probability, previous in zip(probabilities, previous_bits)
        ]
        metrics["phase_slip_ap"] = _average_precision(slip_targets, slip_scores)
        metrics["phase_slip_rate"] = sum(slip_targets) / len(slip_targets)
    return metrics


DEFINITIONS = (
    ("Historical inference champion", "alternation_key", "previous obstruction bit"),
    ("Arithmetic process model", "arithmetic_key", "candidate sign and scale"),
    ("Phase-slip hunter", "phase_key", "previous bit and time since last slip"),
    ("Modulo hunter", "modulo_key", "candidate mod 30 and step mod 6"),
    ("Tower scout", "tower_key", "signed modular-power shadow"),
    (
        "Tower-augmented challenger",
        "phase_tower_key",
        "phase state crossed with signed modular-power shadow",
    ),
)


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
                "phase_tower_key": (
                    previous_bit,
                    min(since_slip.bit_length(), 14),
                    int(residue >= modulus / 2),
                    step % 2,
                ),
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

    agents: list[dict] = []
    predictions: dict[str, list[float]] = {}
    train_predictions: dict[str, list[float]] = {}
    previous_bits = [int(row["previous_bit"]) for row in test]
    for name, key, feature in DEFINITIONS:
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
                **_metrics(targets, test_probabilities, previous_bits),
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
            **_metrics(targets, ensemble, previous_bits),
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
            **_metrics(targets, skeptic, previous_bits),
        }
    )
    oracle = [0.999 if target else 0.001 for target in targets]
    agents.append(
        {
            "name": "Exact visited-set oracle",
            "target": "next blocked/free bit",
            "feature": "candidate collision with complete history",
            "status": "oracle reference; not inferred",
            **_metrics(targets, oracle, previous_bits),
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
        "tower_challenger_added_to_ensemble": weights["Tower-augmented challenger"],
        "leakage_boundary": (
            "The exact collision oracle is displayed only as a ceiling. It is never an ensemble input."
        ),
    }


@lru_cache(maxsize=64)
def evaluate_replay(
    steps: int = 100_000,
    base: int = 3,
    modulus: int = 210,
    reveal: int = 256,
) -> dict:
    """Reveal a prefix of the untouched test block for an interactive blind replay."""
    steps = max(10_000, min(int(steps), 200_000))
    base = max(2, min(abs(int(base)), 10_000))
    modulus = max(3, min(abs(int(modulus)), 10_000))
    records = _records(steps, base, modulus)
    split = int(len(records) * 0.8)
    train, test = records[:split], records[split:]
    reveal = max(32, min(int(reveal), len(test)))
    targets = [int(row["target"]) for row in test]
    previous_bits = [int(row["previous_bit"]) for row in test]

    predictions: dict[str, list[float]] = {}
    train_predictions: dict[str, list[float]] = {}
    for name, key, _ in DEFINITIONS:
        table, fallback = _fit_table(train, key)
        predictions[name] = [_predict(table, fallback, row[key]) for row in test]
        train_predictions[name] = [_predict(table, fallback, row[key]) for row in train]

    train_targets = [int(row["target"]) for row in train]
    raw_weights = {
        name: max(0.01, math.log(2) - _log_loss(train_targets, probabilities))
        for name, probabilities in train_predictions.items()
    }
    weight_total = sum(raw_weights.values())
    weights = {name: weight / weight_total for name, weight in raw_weights.items()}
    predictions["Forward ensemble"] = [
        sum(weights[name] * predictions[name][index] for name in train_predictions)
        for index in range(len(test))
    ]

    visible_names = (
        "Historical inference champion",
        "Phase-slip hunter",
        "Tower scout",
        "Tower-augmented challenger",
        "Forward ensemble",
    )
    scoreboard = []
    for name in visible_names:
        scoreboard.append(
            {
                "name": name,
                **_metrics(
                    targets[:reveal],
                    predictions[name][:reveal],
                    previous_bits[:reveal],
                ),
            }
        )
    champion = min(scoreboard, key=lambda row: row["bits_per_step"])
    current_index = reveal - 1
    current_row = test[current_index]
    actual = targets[current_index]
    current_predictions = [
        {
            "name": name,
            "probability_blocked": predictions[name][current_index],
            "predicted_bit": int(predictions[name][current_index] >= 0.5),
            "correct": int(predictions[name][current_index] >= 0.5) == actual,
        }
        for name in visible_names
    ]
    first = max(0, reveal - 192)
    history = []
    for index in range(first, reveal):
        row = test[index]
        history.append(
            {
                "step": int(row["step"]),
                "truth": targets[index],
                "previous_bit": previous_bits[index],
                "phase_slip": targets[index] == previous_bits[index],
                "probabilities": {
                    name: predictions[name][index]
                    for name in visible_names
                },
            }
        )
    return {
        "steps": steps,
        "train_steps": len(train),
        "test_steps": len(test),
        "revealed": reveal,
        "hidden_remaining": len(test) - reveal,
        "base": base,
        "modulus": modulus,
        "current": {
            "step": int(current_row["step"]),
            "actual_bit": actual,
            "previous_bit": int(current_row["previous_bit"]),
            "candidate": int(current_row["candidate"]),
            "phase_slip": actual == int(current_row["previous_bit"]),
            "predictions": current_predictions,
        },
        "scoreboard": scoreboard,
        "champion_so_far": champion["name"],
        "champion_bits_per_step": champion["bits_per_step"],
        "history": history,
        "weights": weights,
        "protocol": (
            "Models fit on the first 80%. This response exposes only the requested prefix "
            "of the untouched final 20%; no future labels are returned."
        ),
    }


def evaluate_weekly_league(
    steps: int = 200_000,
    candidates: tuple[tuple[int, int], ...] = (
        (2, 97),
        (3, 210),
        (5, 256),
        (7, 420),
        (11, 997),
    ),
) -> dict:
    """Select a tower challenger on validation, then judge it on a sealed future block."""
    steps = max(30_000, min(int(steps), 500_000))
    validation_rows = []
    chosen: tuple[int, int] | None = None
    chosen_validation_bits = float("inf")
    chosen_records: list[dict] | None = None
    for base, modulus in candidates:
        records = _records(steps, base, modulus)
        train_end = int(len(records) * 0.6)
        validation_end = int(len(records) * 0.8)
        train = records[:train_end]
        validation = records[train_end:validation_end]
        table, fallback = _fit_table(train, "phase_tower_key")
        probabilities = [
            _predict(table, fallback, row["phase_tower_key"])
            for row in validation
        ]
        metrics = _metrics(
            [int(row["target"]) for row in validation],
            probabilities,
            [int(row["previous_bit"]) for row in validation],
        )
        validation_rows.append(
            {"base": base, "modulus": modulus, **metrics}
        )
        if metrics["bits_per_step"] < chosen_validation_bits:
            chosen = (base, modulus)
            chosen_validation_bits = metrics["bits_per_step"]
            chosen_records = records

    if chosen is None or chosen_records is None:
        raise RuntimeError("weekly challenger search produced no candidates")

    fit_end = int(len(chosen_records) * 0.8)
    fit = chosen_records[:fit_end]
    test = chosen_records[fit_end:]
    targets = [int(row["target"]) for row in test]
    previous_bits = [int(row["previous_bit"]) for row in test]

    champion_table, champion_fallback = _fit_table(fit, "phase_key")
    champion_probabilities = [
        _predict(champion_table, champion_fallback, row["phase_key"])
        for row in test
    ]
    challenger_table, challenger_fallback = _fit_table(fit, "phase_tower_key")
    challenger_probabilities = [
        _predict(challenger_table, challenger_fallback, row["phase_tower_key"])
        for row in test
    ]
    champion = _metrics(targets, champion_probabilities, previous_bits)
    challenger = _metrics(targets, challenger_probabilities, previous_bits)
    margin = champion["bits_per_step"] - challenger["bits_per_step"]
    promoted = margin > 0.0005 and challenger["phase_slip_ap"] >= champion["phase_slip_ap"] - 0.01
    return {
        "steps": steps,
        "protocol": "60% fit / 20% challenger selection / 20% sealed promotion test",
        "train_steps": int((steps - 1) * 0.6),
        "validation_steps": int((steps - 1) * 0.2),
        "test_steps": len(test),
        "primary_metric": "bits per step on sealed final block",
        "promotion_margin_required": 0.0005,
        "champion": {"name": "Phase-slip hunter", **champion},
        "challenger": {
            "name": "Tower-augmented challenger",
            "base": chosen[0],
            "modulus": chosen[1],
            **challenger,
        },
        "margin_bits_per_step": margin,
        "promoted": promoted,
        "decision": "PROMOTE CHALLENGER" if promoted else "KEEP CHAMPION",
        "validation_search": validation_rows,
        "selection_warning": (
            "Tower base/modulus are selected only on the middle validation block; "
            "the final promotion block stays sealed until one configuration is chosen."
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
