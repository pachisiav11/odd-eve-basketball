"""Compare candidate dunk reward rules at equilibrium.

Each rule changes how many points one dunk is worth.  Because a dunk keeps
possession and cannot be blocked, a banked stack is always cashed out as a
chain of dunks, so what really matters is the total cash-out curve rather than
the per-dunk number.
"""

import sys
import time

import numpy as np

from analyze import dunk_threshold, tackle_rate
from rules import dunk_points_triangular, total_cashout
from solver import solve

CAP = 100

RULES = {
    "triangular":      dunk_points_triangular,     # current rule, 3,4,6,9,13
    "linear_k_plus_2": lambda c: c // 10 + 2,
    "flat_2":          lambda c: 2,
    "flat_3":          lambda c: 3,
    "steep_2k_plus_1": lambda c: 2 * (c // 10) + 1,
    "quadratic":       lambda c: (c // 10) ** 2 + 2,
}


def run(name, rule):
    start = time.time()
    table = solve(cap=CAP, dunk_points=rule)
    np.save("W_%s_cap%d.npy" % (name, CAP), table)
    threshold = dunk_threshold(table, 0, 0, CAP, rule)
    return {
        "rule": name,
        "cashout": [total_cashout(c, rule) for c in (10, 20, 30, 40, 50)],
        "possession_value": float(table[0, 0, 0]),
        "dunk_threshold_00": threshold,
        "tackle_rate_low": tackle_rate(table, 0, 0, 0, CAP, rule),
        "tackle_rate_high": tackle_rate(table, 0, 0, 12, CAP, rule),
        "seconds": time.time() - start,
    }


if __name__ == "__main__":
    wanted = sys.argv[1:] or list(RULES)
    for name in wanted:
        result = run(name, RULES[name])
        print(result, flush=True)
