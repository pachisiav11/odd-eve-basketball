# Odd-Eve Basketball — Equilibrium Analysis

## Summary

The dunk reward formula is not the lever you think it is. Under optimal play the
game already pins the cash-out threshold at 20 charges, and it stays at 20 across
an enormous range of reward curves — including a quadratic one. What actually
sets that threshold is the rule gating 11/12/13 behind a current charge count of
10 or more.

Two larger problems showed up along the way: the two-point shot is effectively
dead, and roughly three quarters of all possessions produce no points at all.

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
no linear program. A full solve takes about 50 seconds and the value table is
107 KB.

### Validation

- The closed-form beat solver agrees with a `scipy.linprog` reference.
- It reproduces known matching-pennies values (2 equal actions gives 1/2, 3 gives 2/3).
- 4,000 simulated equilibrium-vs-equilibrium games gave a win rate of 0.5015
  against the exact value of 0.5000, which the fair toss forces.
- Charge caps of 60 and 100 agree to seven decimal places, so the cap does not
  bind.

## Findings

### 1. Possession is worth almost nothing

Holding the ball at 0–0 with no charges wins **51.27%** of the time. The game is
very close to balanced, and the toss barely matters. No reward rule tested moved
this outside 51.2%–51.9%.

### 2. The two-point shot is dead

The numbers 6 and 7 carry equilibrium weight in only 215 of 12,600 states, or
1.7%, and in 4,000 simulated games the shot was **never played once**. Across
those games the scoring events were 14,279 four-point dunks, 4,000 three-point
dunks and zero two-point shots.

The reason is that the shot is dominated by its own side effects. A made shot
pays 2 points, resets charges to zero and hands over possession. A dunk from 20
charges pays 4 points, keeps possession, keeps 10 charges, and cannot be blocked.
Both cost one beat. The shot survives only as an endgame finisher at scores
11, 13 and 14, where 2 points ends the game before the dunk unlocks.

### 3. The threshold sits at 20 charges, and the reward curve barely moves it

At 0–0 the equilibrium builds past 10 and cashes out at exactly 20. The
push-or-cash margin is positive through 10–19 and flips negative at 20:

| charges | cash now | keep building | choice |
|---|---|---|---|
| 15 | 0.59464 | 0.66269 | build |
| 19 | 0.64718 | 0.70855 | build |
| 20 | 0.72820 | 0.71695 | **dunk** |
| 25 | 0.77747 | 0.76654 | dunk |

Sweeping reward rules (`k` = `floor(c/10)`, threshold measured at 0–0):

| rule | points per dunk | cash-out at 20 charges | threshold |
|---|---|---|---|
| flat 2 | 2, 2, 2, 2 | 4 | 10 |
| flat 3 | 3, 3, 3, 3 | 6 | 10 |
| `k` | 1, 2, 3, 4 | 3 | 20 |
| **`k+2` (current)** | **3, 4, 5, 6** | **7** | **20** |
| `k+5` | 6, 7, 8, 9 | 13 | 20 |
| `k^2+2` (quadratic) | 3, 6, 11, 18 | 9 | 20 |
| `2k+1` | 1, 3, 5, 7 | 8 | 30 |
| `3k-2` | 1, 4, 7, 10 | 5 | 30 |

The absolute reward level is irrelevant — `k`, `k+2` and `k+5` all give 20 despite
paying 1, 3 and 6 points for the first dunk. **A quadratic curve does not
increase risk appetite at all.** Only the marginal step per ten charges matters,
and it has to reach +2 before the threshold moves, at which point it goes to 30.

### 4. The real cause of the 20-charge threshold is the unlock gate

Because 11/12/13 require a *current* charge count of 10 or more, cashing out at
exactly 10 drops the player to 0 and revokes access to the fast, safe actions.
Cashing out at 20 drops them to 10 and keeps everything. That asymmetry, not the
reward curve, is what makes 20 the natural target.

Removing the gate while leaving the reward formula untouched:

| variant | threshold | possession value | tackle rate at 0 charges |
|---|---|---|---|
| gated at 10 (real game) | 20 | 0.51268 | 19.5% |
| no gate, 11/12/13 always legal | **10** | 0.55193 | 11.8% |

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
score, the threshold drops from 20 to 10. Once the stack is forfeited either way,
the extra ten charges buy only one more point and are not worth the risk.

### 7. Pacing

Mean game length is **117 beats**, median 102, 95th percentile 258. At roughly one
beat per second that is a two-minute typical game with a four-minute tail. There
are about 20 possessions per game producing only 4.6 dunks, so **roughly three
quarters of possessions end with no points scored**. Players lose an average of
4.6 charges to each tackle.

## Recommendations

**Keep the linear rule.** It is doing its job, and switching to a quadratic curve
would change nothing about risk appetite while making scores swingier and the
game harder to teach.

**If you want players pushing past 20 charges**, raise the marginal step to +2 per
ten charges — `2k+1` gives 1, 3, 5, 7 and moves the threshold to 30. Note that
this makes the first dunk worth only 1 point, which is the actual mechanism: it
punishes cashing out early rather than rewarding stacking.

**Fix the two-point shot first.** It is the larger design problem and it is
currently unplayable. The cheapest fixes, in rough order of how little they
disturb the rest of the game:

1. Let a made shot keep the charges, so shooting is not a reset.
2. Raise the shot to 3 points, matching the minimum dunk.
3. Drop the shot requirement below 5 charges so it occupies a genuinely
   different part of the game from the dunk.

**Consider the pacing.** Three quarters of possessions being scoreless is what
drives the 117-beat average. Lowering the dunk requirement from 10 charges, or
widening the low-charge action set to cut the 19.5% tackle rate, would both
shorten games.

## Files

- `rules.py` — transition function and legal action sets
- `matgame.py` — closed-form single-beat solver, plus an LP reference
- `solver.py` — layered backward induction over the full state space
- `analyze.py` — thresholds, tackle rates, shot usage, push-or-cash crossover
- `simulate.py` — equilibrium self-play for distributional statistics
- `sweep.py`, `confirm.py`, `gate_test.py` — the experiments above
