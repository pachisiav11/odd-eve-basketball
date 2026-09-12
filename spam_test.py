"""Does always showing the same number beat the engine?

An equilibrium makes the opponent indifferent across every action in its
support, so a fixed-number strategy should score exactly the value of the game
on offense and should be punished on defense, where the engine's offensive mix
is not designed to keep the defender indifferent.
"""

import random
from collections import Counter

import numpy as np

from analyze import defender_mix, payoffs
from matgame import solve_beat
from rules import CHARGE_GAIN, DUNK, SHOTS, TARGET, dunk_points_linear, offense_actions

CAP = 60
table = np.load("W_linear_cap60.npy")


def pick(mix, rng):
    roll, last = rng.random(), None
    for a, p in mix.items():
        last = a
        roll -= p
        if roll <= 0:
            return a
    return last


def play(policy, rng, stats):
    score = {"you": 0, "eng": 0}
    holder = "you" if rng.random() < 0.5 else "eng"
    charges, beats = 0, 0

    while max(score.values()) < TARGET and beats < 20000:
        beats += 1
        mine, theirs = score[holder], score["eng" if holder == "you" else "you"]
        succ, fail, unmatched = payoffs(table, mine, theirs, charges, CAP)
        legal = offense_actions(charges, CAP)

        if holder == "you":
            off = policy(legal, charges)
            sub_v, sub_m = solve_beat(succ, fail, None)
            dfn = pick(defender_mix(succ, fail, sub_v, sub_m), rng)
        else:
            off = pick(solve_beat(succ, fail, unmatched)[1], rng)
            dfn = policy(list(range(1, 14)), charges)

        if off == DUNK:
            score[holder] += dunk_points_linear(charges)
            charges -= 10
            stats["peak"] = max(stats["peak"], charges + 10)
        elif off == dfn:
            holder = "eng" if holder == "you" else "you"
            stats["peak"] = max(stats["peak"], charges)
            charges = 0
        elif off in SHOTS:
            score[holder] += 2
            holder = "eng" if holder == "you" else "you"
            charges = 0
        else:
            charges = min(CAP, charges + CHARGE_GAIN[off])
    return score, beats


def always(n):
    def policy(legal, charges):
        if n in legal:
            return n
        return max(legal, key=lambda a: (a != DUNK, a))
    return policy


GAMES = 20000
print("Player strategy               win rate   mean beats   best stack reached")
for n in (5, 1, 13, 12):
    rng = random.Random(11)
    stats = {"peak": 0}
    wins, total = 0, 0
    for _ in range(GAMES):
        score, beats = play(always(n), rng, stats)
        wins += score["you"] >= TARGET
        total += beats
    print("always show %-2d               %8.4f %12.1f %18d"
          % (n, wins / GAMES, total / GAMES, stats["peak"]))
