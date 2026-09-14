"""Play equilibrium against equilibrium to get distributional statistics.

The solver already gives the exact value of the game, so the main purpose here
is to measure things the value table does not directly expose -- game length,
possession outcomes, the spread of charge counts actually reached -- and to
check the simulated win rate against the computed value.
"""

import random
from collections import Counter

import numpy as np

from analyze import defender_mix, payoffs
from rules import CHARGE_GAIN, DUNK, SHOTS, TARGET, dunk_points_triangular
from solver import beat_at


def pick(mix, rng):
    roll = rng.random()
    total = 0.0
    for action, weight in mix.items():
        total += weight
        if roll <= total:
            return action
    return action


def play_game(table, cap, rng, dunk_points=dunk_points_triangular, stats=None):
    score = [0, 0]
    holder = rng.randrange(2)      # the toss is a fair coin
    charges = 0
    beats = 0
    possession_beats = 0

    while max(score) < TARGET:
        beats += 1
        possession_beats += 1
        mine, theirs = score[holder], score[1 - holder]

        value, offense_mix = beat_at(table, mine, theirs, charges, cap, dunk_points)
        succ, fail_value, _ = payoffs(table, mine, theirs, charges, cap, dunk_points)
        defence = defender_mix(succ, fail_value, value, offense_mix)

        action = pick(offense_mix, rng)
        if stats is not None:
            stats["actions"][action] += 1

        if action == DUNK:
            if stats is not None:
                stats["dunk_charges"].append(charges)
                stats["points"][dunk_points(charges)] += 1
            score[holder] += dunk_points(charges)
            charges -= 10
            continue

        guess = pick(defence, rng) if defence else None
        if guess == action:
            if stats is not None:
                stats["possession_end"]["turnover"] += 1
                stats["possession_beats"].append(possession_beats)
                stats["peak_charges"].append(charges)
            holder = 1 - holder
            charges = 0
            possession_beats = 0
        elif action in SHOTS:
            if stats is not None:
                stats["possession_end"]["shot"] += 1
                stats["possession_beats"].append(possession_beats)
                stats["points"][2] += 1
            score[holder] += 2
            holder = 1 - holder
            charges = 0
            possession_beats = 0
        else:
            charges = min(cap, charges + CHARGE_GAIN[action])

    return score, beats


def run(table, cap, games=20000, seed=1, dunk_points=dunk_points_triangular):
    rng = random.Random(seed)
    stats = {
        "actions": Counter(), "points": Counter(),
        "possession_end": Counter(), "possession_beats": [],
        "peak_charges": [], "dunk_charges": [],
    }
    lengths, first_wins = [], 0
    for _ in range(games):
        score, beats = play_game(table, cap, rng, dunk_points, stats)
        lengths.append(beats)
        if score[0] >= TARGET:
            first_wins += 1
    stats["games"] = games
    stats["mean_beats"] = float(np.mean(lengths))
    stats["median_beats"] = float(np.median(lengths))
    stats["p95_beats"] = float(np.percentile(lengths, 95))
    stats["player0_winrate"] = first_wins / games
    return stats
