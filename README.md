# Odd-Eve Basketball

A two-player hand-signal game, solved exactly and made playable in the browser.

**[Play it here](https://pachisiav11.github.io/odd-eve-basketball/)** &mdash; you against the exact Nash equilibrium.

## The game

Two players face each other on a one-second beat. On every beat both show a
number with their hand. One player holds an imaginary ball and is trying to work
it up the court; the other is trying to take it away. First to 15 points wins.

| number | meaning |
|---|---|
| 1, 2, 3 | dribble, +1 charge |
| 4, 5 | pass, +2 charges |
| 6, 7 | shoot for 2 points, needs 5 charges, possession then changes |
| 0 | dunk, needs 10 charges, `0.5k² − 0.5k + 3` points for `k = floor(charges/10)` — 3, 4, 6, 9, 13 at 10/20/30/40/50 — cannot be blocked, keeps possession, costs 10 charges |
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
- **The two-point shot is all but dead.** It carries equilibrium weight in 1.68%
  of states, and only at 5&ndash;9 charges &mdash; below the dunk gate &mdash; as an endgame
  finisher. A dunk pays more, keeps possession and cannot be blocked, for the
  same one beat.
- Equilibrium **still cashes out first at 20 charges**, because the reward curve
  is unchanged below that point. What pins the first cash-out at 20 is not the
  reward at all, but the rule gating 11/12/13 behind a current charge count of
  10: dunking at 10 drops you to 0 and revokes the fast, safe numbers, while
  dunking at 20 drops you to 10 and keeps them.
- Above 20 the curve does bite: a **second cash-out band opens at 30**, and the
  push-or-cash margin goes positive again in between, so a stack that overshoots
  20 is worth carrying to 30 rather than spending. About 4% of dunks now land at
  30 or more, which the old linear rule never reached.
- The per-beat risk of losing the ball is set purely by how many numbers the
  offense can credibly mix over: **19.5%** below 10 charges, **11.8%** above.
  Neither number moved when the reward curve changed.

## Saving, replaying and exporting games

The page keeps games as plain JSON, entirely in your browser. Nothing is
uploaded and there is no server.

- **Autosave.** The game in progress is written after every beat and restored
  when you reopen the page, so closing the tab mid-game costs nothing.
- **Three slots.** Save the current position to a named slot and load it back
  later.
- **Export / import.** Any game downloads as a `.json` file holding the whole
  game, not a result: every beat, both players' numbers and what each of them
  meant, the score, possession and charge count before and after it, the
  equilibrium mixes both sides were playing against, the win probability at
  each end of it, and the time it was played. About 1.2 KB a beat, so a
  finished game is 100&ndash;200 KB.
- **Replay.** Any game with beats in it can be replayed in the page: step
  through it, scrub the slider, or let it play. The arena, the score, the
  charge meter and the win probability redraw at every beat, and the engine
  strategy card shows the mix the engine drew its number from next to the mix
  you should have been playing. The replay is read-only &mdash; leaving it puts
  the live game back exactly as it was.
- **History.** Finished games are archived automatically with a running
  win&ndash;loss record. The ten most recent keep every beat and can be
  replayed from the archive; the rest keep their result row, because browser
  storage is about 5 MB and a game is 100&ndash;200 KB. The whole archive
  exports as one file, each game a complete save in its own right.

One beat out of an exported game:

```json
{
  "n": 44,
  "t": "2026-09-15T09:18:57.522Z",
  "sincePrevMs": 4,
  "offSide": "eng", "defSide": "you",
  "offNum": 0, "defNum": 1,
  "text": "DUNK — 4 points",
  "you": { "role": "defense", "number": 1, "label": "dribble", "equilibrium": 0.062178 },
  "eng": { "role": "offense", "number": 0, "label": "dunk", "equilibrium": 1,
           "drawnFrom": { "0": 1 } },
  "outcome": { "event": "dunk", "points": 4, "scoredBy": "eng", "chargeDelta": -10,
               "matched": false, "turnover": false, "possessionAfter": "eng" },
  "before": { "you": 0, "eng": 0, "holder": "eng", "charges": 21, "yourWinProb": 0.263609 },
  "after":  { "you": 0, "eng": 4, "holder": "eng", "charges": 11, "yourWinProb": 0.263609 },
  "equilibrium": {
    "offenseMix": { "0": 1 },
    "defenseMix": { "1": 0.062178, "2": 0.062178, "3": 0.062178, "4": 0.107411,
                    "5": 0.107411, "11": 0.107411, "12": 0.203604, "13": 0.28763 },
    "legalOffense": [1, 2, 3, 4, 5, 6, 7, 0, 11, 12, 13],
    "tackleRisk": 0, "cashOut": true, "dunkPoints": 4
  }
}
```

Every field is documented in [SAVE_FORMAT.md](SAVE_FORMAT.md).

Loading a file does not trust it. The opening toss and the two numbers per
beat are the whole game; the page replays them through the same transition
function it uses live, rebuilding the scores, charges, possession and all of
the analysis from the rules. A file whose moves do not add up to the position
it claims is rejected rather than half-loaded, and a file written by an older
version is refused outright.

The same thing can be done from the command line, against a separate
implementation of the rules:

```bash
python3 replay.py odd-eve-15-12-beat73.json
```

`replay.py` rebuilds the game with `rules.py`, prints a beat-by-beat
transcript, and checks every field in the file &mdash; the summary counters
included &mdash; against what the rules produce. It reads a single game or a
whole exported history.

## Repository layout

| file | purpose |
|---|---|
| `index.html` | the playable page, self-contained, no dependencies |
| `SAVE_FORMAT.md` | field-by-field specification of the save and history files |
| `rules.py` | transition function and legal action sets |
| `matgame.py` | closed-form single-beat solver, plus a linear-program reference |
| `solver.py` | layered backward induction over the full state space |
| `analyze.py` | thresholds, tackle rates, shot usage, push-or-cash crossover |
| `simulate.py` | equilibrium self-play for distributional statistics |
| `build.py` | re-solve and refresh the table embedded in `index.html` |
| `replay.py` | rebuild an exported game from its JSON and check every field of it |
| `sweep.py`, `confirm.py`, `gate_test.py` | reward-rule and rule-variant experiments |
| `exploit_test.py`, `spam_test.py` | checks that the engine really is unexploitable |

## Rebuilding

Needs Python with `numpy` and `scipy`.

```bash
python build.py
```

This solves the game (about 30 seconds), writes `W_cap60.npy` for the
analysis scripts, and rewrites the table inside `index.html` so the page and the
solver cannot drift apart. Solved tables are not committed; regenerate them.

## Verification

- The closed-form beat solver agrees with a `scipy.linprog` reference, and
  reproduces known matching-pennies values.
- The JavaScript port reproduces the Python solver to seven decimal places.
- 4,000 simulated equilibrium games return a 0.4955 win rate against the exact
  0.5000 that a fair toss forces.
- An exhaustive scan of all 12,150 states finds **no** action anywhere that beats
  the equilibrium value, so no fixed-number strategy can exploit the engine.
  Measured over 20,000 games each, the best fixed number (always 13) wins 0.06%
  of them and always 5 or always 1 wins none.
- A game exported from the page replays beat for beat in Python against
  `rules.py`, and every field the file states &mdash; positions, outcomes, legal
  moves, the per-side statistics &mdash; is checked against the rules rather
  than taken on trust.
- Charge caps of 60 and 100 agree to five decimal places and give the same
  push-or-cash decisions, so the cap does not bind under equilibrium play. It can
  be reached by a player who deliberately stalls, which does not affect the
  analysis.

## Licence

MIT.
