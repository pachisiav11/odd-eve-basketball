"""Reading strategy and design metrics out of a solved value table."""

import numpy as np

from matgame import solve_beat
from rules import CHARGE_GAIN, DUNK, SHOTS, TARGET, dunk_points_linear, offense_actions
from solver import beat_at


def payoffs(table, score_off, score_def, charges, cap, dunk_points=dunk_points_linear):
    """Success payoff per action, plus the shared payoff for losing the ball."""
    fail_value = 1.0 - table[score_def, score_off, 0]
    succ, unmatched = {}, {}
    for action in offense_actions(charges, cap):
        if action == DUNK:
            new_score = score_off + dunk_points(charges)
            unmatched[action] = (1.0 if new_score >= TARGET
                                 else table[new_score, score_def, charges - 10])
        elif action in SHOTS:
            new_score = score_off + 2
            succ[action] = (1.0 if new_score >= TARGET
                            else 1.0 - table[score_def, new_score, 0])
        else:
            succ[action] = table[score_off, score_def, charges + CHARGE_GAIN[action]]
    return succ, fail_value, unmatched


def defender_mix(succ, fail_value, value, offense_mix):
    """Defender's equilibrium mix.

    The defender must leave the offense indifferent across its support, which
    forces y_i = (S_i - V) / (S_i - F).  These weights sum to one exactly.
    """
    if DUNK in offense_mix:
        return {}
    mix = {}
    for action in offense_mix:
        gain = succ[action] - fail_value
        mix[action] = (succ[action] - value) / gain
    return mix


def tackle_rate(table, score_off, score_def, charges, cap,
                dunk_points=dunk_points_linear):
    """Probability the offense loses the ball on this beat, in equilibrium."""
    value, offense_mix = beat_at(table, score_off, score_def, charges, cap, dunk_points)
    succ, fail_value, unmatched = payoffs(table, score_off, score_def, charges,
                                          cap, dunk_points)
    if DUNK in offense_mix:
        return 0.0
    defence = defender_mix(succ, fail_value, value, offense_mix)
    return sum(offense_mix[a] * defence.get(a, 0.0) for a in offense_mix)


def dunk_threshold(table, score_off, score_def, cap, dunk_points=dunk_points_linear):
    """Lowest charge count at which equilibrium cashes the stack out."""
    for charges in range(10, cap + 1):
        _, mix = beat_at(table, score_off, score_def, charges, cap, dunk_points)
        if mix.get(DUNK, 0.0) > 0.5:
            return charges
    return None


def shot_usage(table, cap, dunk_points=dunk_points_linear):
    """Every state where the two-point shot carries any equilibrium weight."""
    used = []
    for score_off in range(TARGET):
        for score_def in range(TARGET):
            for charges in range(5, cap + 1):
                _, mix = beat_at(table, score_off, score_def, charges, cap, dunk_points)
                weight = sum(mix.get(s, 0.0) for s in SHOTS)
                if weight > 1e-9:
                    used.append((score_off, score_def, charges, weight))
    return used


def crossover(table, score_off, score_def, cap, dunk_points=dunk_points_linear,
              low=10, high=35):
    """Cash out now, or push for a bigger stack?

    Returns rows of (charges, value of dunking immediately, value of holding
    on and continuing to build, and the margin between them).  The equilibrium
    takes whichever is larger, so the sign flip is the risk/reward crossover.
    """
    rows = []
    for charges in range(low, min(high, cap) + 1):
        succ, fail_value, unmatched = payoffs(table, score_off, score_def,
                                              charges, cap, dunk_points)
        cash_now = unmatched.get(DUNK)
        if cash_now is None:
            continue
        keep_building, _ = solve_beat(succ, fail_value, None)
        rows.append((charges, cash_now, keep_building, keep_building - cash_now))
    return rows
