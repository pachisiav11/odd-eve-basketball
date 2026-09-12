"""Solving one beat of Odd-Eve Basketball as a zero-sum matrix game.

Every beat has the same special shape.  The offense picks an action i; the
defender picks a number j.  If j == i the offense loses the ball and the payoff
is F, the same value for every action, because a tackle and a blocked shot lead
to the identical state.  Otherwise the payoff is S_i, which depends only on the
offense's action.  The dunk is a row the defender cannot match at all.

That structure is a weighted generalisation of matching pennies and has a
closed form, so the inner loop of the solver needs no linear program.

Writing M = sum_i x_i S_i, the offense's payoff when the defender picks j is

    M - x_j (S_j - F)

so the offense maximises  M - max_j x_j g_j  with  g_j = S_j - F.  Equalising
x_j g_j = t across a support P and writing H = sum 1/g_j, K = sum S_j/g_j over
P gives a value of (K - 1) / H.  The value is linear in the weight given to the
dunk, so the dunk is played either never or always.
"""

import numpy as np
from scipy.optimize import linprog

from rules import DEFENDER_ACTIONS


def solve_beat(succ_values, fail_value, unmatched=None):
    """Exact value and offense strategy for one beat.

    succ_values: {action -> payoff when the defender does not match}
    fail_value:  payoff when the defender matches, identical for every action
    unmatched:   {action -> payoff} for actions the defender cannot match,
                 which in this game means the dunk

    Returns (value, {action -> probability}).
    """
    unmatched = unmatched or {}

    best_dunk_action, best_dunk_value = None, -np.inf
    for action, value in unmatched.items():
        if value > best_dunk_value:
            best_dunk_action, best_dunk_value = action, value

    gains = [(a, s, s - fail_value) for a, s in succ_values.items()]
    usable = [(a, s, g) for a, s, g in gains if g > 1e-15]

    if not usable:
        # Being matched would not hurt, so the defender declines to match and
        # every action simply pays its own success value.
        if succ_values:
            mixed_action = max(succ_values, key=succ_values.get)
            mixed_value = succ_values[mixed_action]
        else:
            mixed_action, mixed_value = None, -np.inf
        if best_dunk_action is not None and best_dunk_value >= mixed_value:
            return best_dunk_value, {best_dunk_action: 1.0}
        return mixed_value, {mixed_action: 1.0}

    # The optimal support is a prefix of the actions ranked by success value.
    usable.sort(key=lambda t: t[1], reverse=True)
    best_value, best_size, best_h = -np.inf, None, None
    h = k = 0.0
    for size in range(1, len(usable) + 1):
        _, s, g = usable[size - 1]
        h += 1.0 / g
        k += s / g
        candidate = (k - 1.0) / h
        if candidate > best_value:
            best_value, best_size, best_h = candidate, size, h

    if best_dunk_action is not None and best_dunk_value >= best_value:
        return best_dunk_value, {best_dunk_action: 1.0}

    t = 1.0 / best_h
    strategy = {a: t / g for a, _, g in usable[:best_size]}
    return best_value, strategy


def solve_beat_lp(succ_values, fail_value, unmatched=None):
    """Reference implementation via a linear program, used only for validation."""
    unmatched = unmatched or {}
    rows = list(succ_values) + list(unmatched)
    cols = list(DEFENDER_ACTIONS)

    payoff = np.empty((len(rows), len(cols)))
    for i, a in enumerate(rows):
        for j, d in enumerate(cols):
            if a in unmatched:
                payoff[i, j] = unmatched[a]
            elif a == d:
                payoff[i, j] = fail_value
            else:
                payoff[i, j] = succ_values[a]

    n = len(rows)
    # Variables: x_0..x_{n-1}, v.  Maximise v subject to (x^T A)_j >= v.
    objective = np.zeros(n + 1)
    objective[-1] = -1.0
    ub_matrix = np.hstack([-payoff.T, np.ones((len(cols), 1))])
    ub_vector = np.zeros(len(cols))
    eq_matrix = np.zeros((1, n + 1))
    eq_matrix[0, :n] = 1.0
    bounds = [(0, 1)] * n + [(None, None)]

    result = linprog(objective, A_ub=ub_matrix, b_ub=ub_vector,
                     A_eq=eq_matrix, b_eq=[1.0], bounds=bounds, method="highs")
    if not result.success:
        raise RuntimeError(result.message)
    return result.x[-1], {a: result.x[i] for i, a in enumerate(rows)}
