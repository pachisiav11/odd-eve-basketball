"""Does the 20-charge threshold come from the reward curve or from the
11/12/13 unlock gate?

Cashing out at exactly 10 charges drops the player to 0 and therefore revokes
access to 11, 12 and 13.  Cashing out at 20 drops them to 10 and keeps it.
If that is what sets the threshold, removing the gate should move the
threshold down to 10 even though the reward curve is unchanged.
"""

import analyze
import solver
from analyze import dunk_threshold, tackle_rate
from rules import BOOSTS, DRIBBLES, PASSES, SHOTS, SHOOT_MIN_CHARGE

CAP = 100


def ungated_actions(charges, charge_cap):
    """Same game, except 11/12/13 need no minimum charge."""
    acts = []
    if charges + 1 <= charge_cap:
        acts.extend(DRIBBLES)
    if charges + 2 <= charge_cap:
        acts.extend(PASSES)
    if charges >= SHOOT_MIN_CHARGE:
        acts.extend(SHOTS)
    if charges >= 10:
        acts.append(0)
    for number, gain in BOOSTS.items():
        if charges + gain <= charge_cap:
            acts.append(number)
    return acts


for label, fn in (("gated at 10 charges (real game)", solver.offense_actions),
                  ("no gate, 11/12/13 always legal", ungated_actions)):
    solver.offense_actions = fn
    analyze.offense_actions = fn
    table = solver.solve(cap=CAP)
    print("%-32s threshold=%-4s poss.value=%.5f  tackle@0=%.4f tackle@12=%.4f"
          % (label, dunk_threshold(table, 0, 0, CAP), table[0, 0, 0],
             tackle_rate(table, 0, 0, 0, CAP), tackle_rate(table, 0, 0, 12, CAP)),
          flush=True)
