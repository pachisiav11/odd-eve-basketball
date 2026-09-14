# Odd-Eve Basketball — Equilibrium Analysis

## Summary

The dunk reward is `0.5k^2 - 0.5k + 3` for `k = floor(c/10)`, paying 3, 4, 6, 9,
13 at 10 through 50 charges. It replaced a linear `k+2` rule that paid 3, 4, 5, 6.

The reward formula is a weaker lever than it looks. The two curves are identical
at k=1 and k=2, so the *first* cash-out is unchanged: equilibrium still builds
past 10 and spends at 20. What actually pins that first threshold is not the
reward at all, but the rule gating 11/12/13 behind a current charge count of 10
or more.

Where the new curve does bite is above 20. The push-or-cash decision is no longer
monotonic: it flips to dunk at 20, back to build at 23, and to dunk again at 30.
A stack that overshoots the first threshold is now worth carrying to 30 rather
than spending, and about 4% of dunks land at 30 or more — a region the linear
rule never reached.

Two larger problems are unchanged by any of this: the two-point shot is still
all but dead, and roughly three quarters of all possessions produce no points.

## Method

This game does not need a trained model. It is a zero-sum stochastic game with
simultaneous moves and no hidden state — both players always see the score, the
possession and the charge count. That means it has an exact value and exact
equilibrium mixed strategies, which can be computed directly.

State is written from the point of view of the player holding the ball:
`(score_off, score_def, charges)`. The solver exploits two structural facts.
The combined score never decreases and every scoring event raises it by at least
two, so score layers solve from the top down. Inside a layer the only route back
to a lower charge count is a turnover, which always lands on exactly one state —
the opponent in possession at zero charges — so each layer collapses to a fixed
point in two scalars with plain backward induction over the charge count.

Every beat is a matrix game with a special shape: payoff `S_i` when the defender
misses, and a single shared payoff `F` when the defender matches, because a
tackle and a blocked shot lead to identical states. That is a weighted
generalisation of matching pennies and has a closed form, so the inner loop needs
no linear program. A full solve takes about 30 seconds and the value table is
107 KB.

### Validation

- The closed-form beat solver agrees with a `scipy.linprog` reference.
- It reproduces known matching-pennies values (2 equal actions gives 1/2, 3 gives 2/3).
- 4,000 simulated equilibrium-vs-equilibrium games gave a win rate of 0.4955
  against the exact value of 0.5000, which the fair toss forces.
- Charge caps of 60 and 100 agree to five decimal places and produce the same
  push-or-cash flips at 20, 23 and 30, so the cap does not bind.
- An exhaustive scan of all 12,150 states finds no action anywhere whose payoff
  against the engine's defence beats the equilibrium value.

## Findings

### 1. Possession is worth almost nothing

Holding the ball at 0–0 with no charges wins **51.27%** of the time. The game is
very close to balanced, and the toss barely matters. No reward rule tested moved
this outside 51.2%–51.9%.

### 2. The two-point shot is all but dead

The shot is dominated by its own side effects. A made shot pays 2 points, resets
charges to zero and hands over possession. A dunk from 20 charges pays 4 points,
keeps possession, keeps 10 charges, and cannot be blocked. Both cost one beat.

So the numbers 6 and 7 carry equilibrium weight in only 212 of 12,600 states, or
**1.68%** — and only at 5–9 charges, below the dunk gate, at offense scores 7, 9,
10, 11, 13 and 14, where 2 points can end the game before a dunk unlocks. It is
an endgame finisher and nothing else.

Across 4,000 simulated games the scoring events were:

| event | count |
|---|---|
| 4-point dunk (20–29 charges) | 12,960 |
| 3-point dunk (10–19 charges) | 4,293 |
| 6-point dunk (30+ charges) | 703 |
| 2-point shot | 406 |

Under the old linear rule the shot was played **zero** times in 4,000 games. It
appears at all now only because 6-point dunks change which scores are reachable,
so those endgame states actually come up. At 2% of scoring events it is still
barely a real option.

### 3. The first cash-out is still 20, but a second one opens at 30

At 0–0 the equilibrium still builds past 10 and spends at exactly 20, because the
new curve is identical to the old one at k=1 and k=2 — 3 points then 4. What
changed is that the decision is no longer monotonic in the charge count. It flips
to dunk at 20, back to build at 23, and to dunk again at 30:

| charges | cash now | keep building | choice |
|---|---|---|---|
| 18 | 0.63130 | 0.69752 | build |
| 20 | 0.72768 | 0.71915 | **dunk** |
| 22 | 0.74594 | 0.74419 | dunk |
| 23 | 0.75566 | 0.75905 | **build** |
| 28 | 0.81523 | 0.85138 | build |
| 30 | 0.91671 | 0.87742 | **dunk** |

The middle band is the interesting part. Landing on exactly 20 is worth cashing,
but overshooting to 23 is not: from there the next dunk is still only worth 4
points, while pushing to 30 makes it 6. So a stack that overshoots the first
threshold should be carried, not spent. In 4,000 simulated games this produced
703 dunks at 30 or more and a peak stack of 35 — under the linear rule the
equilibrium never went past the low twenties.

Because charges arrive in steps of 1, 2, 4 and 6, which band a possession lands
in is partly luck. That is a real change in feel: the old rule had one decision
point, this one has two and a dead zone between them.

Sweeping reward rules (`k` = `floor(c/10)`, threshold measured at 0–0):

| rule | points per dunk | cash-out at 20 charges | threshold |
|---|---|---|---|
| flat 2 | 2, 2, 2, 2 | 4 | 10 |
| flat 3 | 3, 3, 3, 3 | 6 | 10 |
| `k` | 1, 2, 3, 4 | 3 | 20 |
| `k+2` (previous rule) | 3, 4, 5, 6 | 7 | 20 |
| **`0.5k^2-0.5k+3` (current)** | **3, 4, 6, 9** | **7** | **20, then 30** |
| `k+5` | 6, 7, 8, 9 | 13 | 20 |
| `k^2+2` (quadratic) | 3, 6, 11, 18 | 9 | 20 |
| `2k+1` | 1, 3, 5, 7 | 8 | 30 |
| `3k-2` | 1, 4, 7, 10 | 5 | 30 |

The absolute reward level is irrelevant — `k`, `k+2` and `k+5` all give 20 despite
paying 1, 3 and 6 points for the first dunk.

The rules that *do* move the first threshold to 30 are `2k+1` and `3k-2`, and
what they share is not steepness but a **miserable first dunk**: 1 point at k=1.
They move the threshold by punishing an early cash-out, not by rewarding a late
one. `k^2+2` is steeper than either and still gives 20, because it pays a
perfectly decent 3 points at k=1.

The current rule is the clean demonstration. It pays the same 3 and 4 as the old
linear rule at k=1 and k=2, so it cannot move the first threshold and does not.
Its steepness lives entirely above 20, which is exactly where the second
threshold appears. **The reward curve only affects the decision in the range
where the curve itself differs** — obvious in hindsight, and the reason a
quadratic that starts flat buys no extra risk appetite at the bottom of the game.

### 4. The real cause of the 20-charge threshold is the unlock gate

Because 11/12/13 require a *current* charge count of 10 or more, cashing out at
exactly 10 drops the player to 0 and revokes access to the fast, safe actions.
Cashing out at 20 drops them to 10 and keeps everything. That asymmetry, not the
reward curve, is what makes 20 the natural target.

Removing the gate while leaving the reward formula untouched:

| variant | threshold | possession value | tackle rate at 0 charges |
|---|---|---|---|
| gated at 10 (real game) | 20 | 0.51273 | 19.5% |
| no gate, 11/12/13 always legal | **10** | 0.55055 | 11.8% |

Re-run under the new reward curve, this gives the same answer it gave under the
old one. The gate moves the first threshold by a full ten charges; swapping a
linear reward for a quadratic one does not move it at all. That is the clearest
statement of which lever is which.

### 5. Bigger action sets are the only real defence

The per-beat tackle rate is set by how many distinct numbers the offense can
credibly mix over, and nothing else. It was identical under every reward rule
tested:

- below 10 charges, 5 usable numbers, **19.5%** per beat
- at 10+ charges, 8 usable numbers, **11.8%** per beat

So crossing 10 charges makes a player both faster *and* substantially safer. The
mechanic compounds in one direction only.

### 6. Making the dunk a turnover makes players more conservative

Tested as a structural variant: if a dunk handed over possession like a normal
score, the threshold drops from 20 to 10 and possession is worth 0.51713. Once
the stack is forfeited either way, the extra ten charges buy only one more point
(3 to 4) and are not worth the risk. Like the gate result, this is unchanged by
the new reward curve.

### 7. Pacing

Mean game length is **120 beats**, median 103, 95th percentile 267. At roughly one
beat per second that is a two-minute typical game with a four-minute tail. There
are about 20.6 possessions per game producing only 4.6 scoring events, so
**roughly three quarters of possessions end with no points scored**. Players lose
an average of 4.7 charges to each tackle.

The new reward curve made games about 3 beats longer, because possessions that
carry a stack from 23 to 30 spend more beats building and fewer scoring.

## Recommendations

**The current rule half-works, and it is worth being clear about which half.**
`0.5k^2-0.5k+3` did open a genuine second decision at 30, which the linear rule
never had, and 30+ dunks now happen. But it left the first and far more common
decision exactly where it was, because it did not change the payout at k=1 or
k=2. Only about 4% of dunks reach 30; the median possession plays identically to
before.

**If the goal is to move the first threshold too**, the lever is the k=1 payout,
not the steepness. Dropping the first dunk to 1 or 2 points — `2k+1` gives
1, 3, 5, 7 — moves it to 30 outright. That punishes cashing out early rather than
rewarding stacking, and it is the only thing in the sweep that reliably works.

**Weigh that against teachability.** "Three, four, six, nine, thirteen" is harder
to hold in your head than "three, four, five, six", and the dead zone at 23–29,
where the right play is to keep building a stack you could already spend, is
genuinely unintuitive at the table. That cost is real and it buys a decision that
4% of dunks ever face.

**Fix the two-point shot.** It is the larger design problem and the reward change
did not touch it: 2% of scoring events, and only ever as an endgame finisher
below the dunk gate. The cheapest fixes, in rough order of how little they
disturb the rest of the game:

1. Let a made shot keep the charges, so shooting is not a reset.
2. Raise the shot to 3 points, matching the minimum dunk.
3. Drop the shot requirement below 5 charges so it occupies a genuinely
   different part of the game from the dunk.

**Consider the pacing.** Three quarters of possessions being scoreless is what
drives the 120-beat average. Lowering the dunk requirement from 10 charges, or
widening the low-charge action set to cut the 19.5% tackle rate, would both
shorten games.

## Files

- `rules.py` — transition function and legal action sets
- `matgame.py` — closed-form single-beat solver, plus an LP reference
- `solver.py` — layered backward induction over the full state space
- `analyze.py` — thresholds, tackle rates, shot usage, push-or-cash crossover
- `simulate.py` — equilibrium self-play for distributional statistics
- `sweep.py`, `confirm.py`, `gate_test.py` — the experiments above
