"""Exact equilibrium solver for Odd-Eve Basketball.

The game is a zero-sum stochastic game with simultaneous moves and no hidden
state, so it has an exact value and exact equilibrium mixed strategies.  This
module computes them by backward induction instead of by training.

W[a][b][c] is the probability that the player in possession eventually wins the
game, given that they have score a, their opponent has score b, and they hold c
charges.

The recursion is organised around two facts.  First, the combined score a + b
never decreases, and every scoring event raises it by at least two, so score
layers can be solved from the top down.  Second, inside one layer the only way
back to a lower charge count is a turnover, which always lands on exactly one
state: the opponent in possession with zero charges.  So each layer reduces to
a fixed point in two scalars, and everything else is plain backward induction
over the charge count.
"""

import numpy as np

from matgame import solve_beat
from rules import (
    CHARGE_GAIN,
    DUNK,
    SHOTS,
    TARGET,
    dunk_points_triangular,
    offense_actions,
)

DEFAULT_CAP = 60


def _chain(score_off, score_def, fail_value, table, cap, dunk_points, dunk_keeps=True):
    """Values over every charge level for one fixed score pair.

    fail_value is the payoff for losing the ball, held fixed during the pass.
    Higher score layers are read from `table` and are already final.
    """
    values = np.empty(cap + 1)
    for charges in range(cap, -1, -1):
        succ, unmatched = {}, {}
        for action in offense_actions(charges, cap):
            if action == DUNK:
                new_score = score_off + dunk_points(charges)
                if new_score >= TARGET:
                    unmatched[action] = 1.0
                elif dunk_keeps:
                    unmatched[action] = table[new_score, score_def, charges - 10]
                else:
                    # Variant: a dunk hands the ball over like any other score.
                    unmatched[action] = 1.0 - table[score_def, new_score, 0]
            elif action in SHOTS:
                new_score = score_off + 2
                if new_score >= TARGET:
                    succ[action] = 1.0
                else:
                    succ[action] = 1.0 - table[score_def, new_score, 0]
            else:
                succ[action] = values[charges + CHARGE_GAIN[action]]
        values[charges] = solve_beat(succ, fail_value, unmatched)[0]
    return values


def solve(cap=DEFAULT_CAP, dunk_points=dunk_points_triangular, tol=1e-13, max_iter=5000,
          dunk_keeps=True):
    """Solve the whole game. Returns the value table W."""
    table = np.zeros((TARGET, TARGET, cap + 1))

    for layer in range(2 * (TARGET - 1), -1, -1):
        for high in range(min(layer, TARGET - 1), -1, -1):
            low = layer - high
            if low > high or low < 0 or low > TARGET - 1:
                continue

            if low == high:
                # Symmetric: both sides of the turnover face the same position.
                guess = 0.5
                for _ in range(max_iter):
                    values = _chain(high, low, 1.0 - guess, table, cap, dunk_points, dunk_keeps)
                    if abs(values[0] - guess) < tol:
                        guess = values[0]
                        break
                    guess = values[0]
                values = _chain(high, low, 1.0 - guess, table, cap, dunk_points, dunk_keeps)
                table[high, low, :] = values
                continue

            top, bot = 0.5, 0.5
            for _ in range(max_iter):
                upper = _chain(high, low, 1.0 - bot, table, cap, dunk_points, dunk_keeps)
                lower = _chain(low, high, 1.0 - top, table, cap, dunk_points, dunk_keeps)
                if abs(upper[0] - top) < tol and abs(lower[0] - bot) < tol:
                    top, bot = upper[0], lower[0]
                    break
                top, bot = upper[0], lower[0]
            table[high, low, :] = _chain(high, low, 1.0 - bot, table, cap, dunk_points, dunk_keeps)
            table[low, high, :] = _chain(low, high, 1.0 - top, table, cap, dunk_points, dunk_keeps)

    return table


def beat_at(table, score_off, score_def, charges, cap=DEFAULT_CAP,
            dunk_points=dunk_points_triangular):
    """Recompute the equilibrium mix for a single state, for analysis."""
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
    return solve_beat(succ, fail_value, unmatched)
