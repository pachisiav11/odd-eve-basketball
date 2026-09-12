"""Test whether risk appetite is driven by the growth rate of the dunk reward
or by how poor the minimum cash-out is."""

from solver import solve
from analyze import dunk_threshold
from rules import total_cashout

CAP = 100
RULES = {
    "k_plus_2 (current) 3,4,5,6": lambda c: c // 10 + 2,
    "k          low start 1,2,3,4": lambda c: c // 10,
    "3k-2   low start, steep 1,4,7": lambda c: 3 * (c // 10) - 2,
    "k+5    high start 6,7,8,9": lambda c: c // 10 + 5,
}

for name, rule in RULES.items():
    table = solve(cap=CAP, dunk_points=rule)
    print("%-30s per-dunk@10=%2d  cashout@20=%3d  threshold=%s"
          % (name, rule(10), total_cashout(20, rule),
             dunk_threshold(table, 0, 0, CAP, rule)), flush=True)
