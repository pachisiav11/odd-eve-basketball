"""Rules of Odd-Eve Basketball, expressed as a pure transition function.

State is always written from the point of view of the player currently holding
the ball: (score_off, score_def, charges).  Possession is therefore implicit --
when possession changes, the two scores swap and charges reset to zero.

Action encoding (the number a player shows on a beat):

    1, 2, 3   dribble   -> +1 charge
    4, 5      pass      -> +2 charges
    6, 7      shoot     -> +2 points, requires >= 5 charges
    0         dunk      -> 0.5k^2-0.5k+3 points for k = floor(c/10),
                           requires >= 10 charges, cannot be blocked,
                           keeps possession, -10 charges
    11        -> +2 charges,  requires >= 10 charges
    12        -> +4 charges,  requires >= 10 charges
    13        -> +6 charges,  requires >= 10 charges

The defender shows a number from 1..13.  Zero is reserved for the dunk, which
is why the dunk can never be matched.  8, 9 and 10 belong to the penalty
system; the offense never plays them under legal play, so for the defender they
are strictly wasted guesses and equilibrium gives them zero weight.

If both players show the same number the offense loses the ball: charges reset
to zero and possession passes to the other player.  This covers both an
ordinary tackle and a blocked shot, which have identical consequences.
"""

TARGET = 15

DEFENDER_ACTIONS = tuple(range(1, 14))

DUNK = 0
DRIBBLES = (1, 2, 3)
PASSES = (4, 5)
SHOTS = (6, 7)
BOOSTS = {11: 2, 12: 4, 13: 6}

SHOOT_MIN_CHARGE = 5
DUNK_MIN_CHARGE = 10

CHARGE_GAIN = {1: 1, 2: 1, 3: 1, 4: 2, 5: 2, 11: 2, 12: 4, 13: 6}


def dunk_points_triangular(charges):
    """The current reward rule: 0.5k^2 - 0.5k + 3 for k = floor(c/10).

    Written as k*(k-1)//2 + 3 because k*(k-1) is always even, so the reward is
    an exact integer at every charge level and scores stay usable as indices.
    Pays 3, 4, 6, 9, 13, 18 at 10 through 60 charges: the step per ten charges
    is k rather than a constant 1.
    """
    k = charges // 10
    return k * (k - 1) // 2 + 3


def offense_actions(charges, charge_cap):
    """Legal numbers for the player in possession at this charge level.

    Charge-gaining actions that would push the total past the cap are dropped.
    This keeps the backward recursion over charges well founded; the cap is set
    high enough that equilibrium play never reaches it.
    """
    acts = []
    if charges + 1 <= charge_cap:
        acts.extend(DRIBBLES)
    if charges + 2 <= charge_cap:
        acts.extend(PASSES)
    if charges >= SHOOT_MIN_CHARGE:
        acts.extend(SHOTS)
    if charges >= DUNK_MIN_CHARGE:
        acts.append(DUNK)
        for number, gain in BOOSTS.items():
            if charges + gain <= charge_cap:
                acts.append(number)
    return acts


def total_cashout(charges, dunk_points=dunk_points_triangular):
    """Points from dunking repeatedly until the stack falls below 10.

    Because a dunk cannot be blocked and keeps possession, this whole sequence
    is risk-free once the charges are banked.
    """
    points = 0
    c = charges
    while c >= DUNK_MIN_CHARGE:
        points += dunk_points(c)
        c -= 10
    return points
