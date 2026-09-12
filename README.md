# Odd-Eve Basketball

A two-player hand-signal game, solved exactly and made playable in the browser.

**[Play it here](#)** &mdash; you against the exact Nash equilibrium.

## The game

Two players face each other on a one-second beat. On every beat both show a
number with their hand. One player holds an imaginary ball and is trying to work
it up the court; the other is trying to take it away. First to 15 points wins.

| number | meaning |
|---|---|
| 1, 2, 3 | dribble, +1 charge |
| 4, 5 | pass, +2 charges |
| 6, 7 | shoot for 2 points, needs 5 charges, possession then changes |
| 0 | dunk, needs 10 charges, `floor(charges/10) + 2` points, cannot be blocked, keeps possession, costs 10 charges |
| 11, 12, 13 | +2, +4, +6 charges, need 10 charges to use |
| 8, 9, 10 | penalty signals, not modelled here |

If both players show the same number the ball changes hands and all charges are
lost. That applies to a blocked shot too. The dunk is the one exception: the
defender may only show 1 to 13, so a dunk can never be matched.

## The engine

There is no neural network here and nothing was trained.

The game is zero-sum, the moves are simultaneous, and no state is hidden, so it
has an exact value and exact equilibrium mixed strategies. Those are computed
directly by backward induction. The browser page carries the resulting
`15 x 15 x 61` table of win probabilities (107 KB as float32) and applies a
closed-form matching-pennies solution on each beat.

That means the engine cannot be exploited by any strategy, and it does not need
to read or adapt to its opponent. It also publishes its own mix on request,
which costs it nothing: at an equilibrium, knowing the probabilities still
leaves you no better reply.

## What the analysis found

Full write-up in [FINDINGS.md](FINDINGS.md). The short version:

- Holding the ball at 0&ndash;0 is worth only **51.27%**. The game is near balanced.
- **The two-point shot is dead.** It carries equilibrium weight in 1.7% of
  states and was played zero times in 4,000 simulated games. A dunk pays more,
  keeps possession and cannot be blocked, for the same one beat.
- Equilibrium **cashes out at 20 charges**, and that threshold barely moves no
  matter how the dunk reward is shaped &mdash; a quadratic curve changes nothing.
  What actually pins it at 20 is the rule gating 11/12/13 behind a current
  charge count of 10.
- The per-beat risk of losing the ball is set purely by how many numbers the
  offense can credibly mix over: **19.5%** below 10 charges, **11.8%** above.

## Repository layout

| file | purpose |
|---|---|
| `index.html` | the playable page, self-contained, no dependencies |
| `rules.py` | transition function and legal action sets |
| `matgame.py` | closed-form single-beat solver, plus a linear-program reference |
| `solver.py` | layered backward induction over the full state space |
| `analyze.py` | thresholds, tackle rates, shot usage, push-or-cash crossover |
| `simulate.py` | equilibrium self-play for distributional statistics |
| `build.py` | re-solve and refresh the table embedded in `index.html` |
| `sweep.py`, `confirm.py`, `gate_test.py` | reward-rule and rule-variant experiments |
| `exploit_test.py`, `spam_test.py` | checks that the engine really is unexploitable |

## Rebuilding

Needs Python with `numpy` and `scipy`.

```bash
python build.py
```

This solves the game (about 50 seconds), writes `W_linear_cap60.npy` for the
analysis scripts, and rewrites the table inside `index.html` so the page and the
solver cannot drift apart. Solved tables are not committed; regenerate them.

## Verification

- The closed-form beat solver agrees with a `scipy.linprog` reference, and
  reproduces known matching-pennies values.
- The JavaScript port reproduces the Python solver to seven decimal places.
- 4,000 simulated equilibrium games return a 0.5015 win rate against the exact
  0.5000 that a fair toss forces.
- An exhaustive scan of all 12,150 states finds **no** action anywhere that beats
  the equilibrium value, so no fixed-number strategy can exploit the engine.
  Measured over 20,000 games, always showing the same number wins 0.0% of them.
- Charge caps of 60 and 100 agree to seven decimal places, so the cap does not
  bind under equilibrium play. It can be reached by a player who deliberately
  stalls, which does not affect the analysis.

## Licence

MIT.
