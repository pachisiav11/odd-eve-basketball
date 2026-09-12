"""Solve the game and refresh the table embedded in index.html.

Run this after changing anything in rules.py or solver.py:

    python build.py

It writes W_linear_cap60.npy for the analysis scripts and rewrites the
TABLE_B64 constant inside index.html so the page and the solver never drift
apart.
"""

import base64
import re
import time

import numpy as np

from solver import solve

CAP = 60


def main():
    start = time.time()
    table = solve(cap=CAP)
    np.save("W_linear_cap60.npy", table)

    payload = base64.b64encode(table.astype(np.float32).tobytes()).decode("ascii")
    html = open("index.html", encoding="utf-8").read()
    patched, count = re.subn(r'(const TABLE_B64 = ")[^"]*(")',
                             lambda m: m.group(1) + payload + m.group(2), html)
    if count != 1:
        raise SystemExit("expected exactly one TABLE_B64 constant, found %d" % count)
    open("index.html", "w", encoding="utf-8").write(patched)

    print("solved in %.0fs" % (time.time() - start))
    print("value of possession at 0-0: %.6f" % table[0, 0, 0])
    print("embedded %d base64 chars into index.html" % len(payload))


if __name__ == "__main__":
    main()
