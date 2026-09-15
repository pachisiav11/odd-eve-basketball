# The save file

Version 2 of `odd-eve-basketball/save` is a complete record of a game. Not a
result and not a summary: every beat, both players' numbers, the position
before and after it, what the rules made of it, and the equilibrium mixes it
was played against. A game can be rebuilt from the file alone, and the page
does exactly that when you load one.

Files are written by **Export .json** in the Saved games card, by **Download
.json** on the game-over screen, and — one envelope per game — inside an
exported history. There is no size limit: a beat costs about 1.2 KB, so a
finished game is 100–200 KB.

Everything here is UTF-8 JSON, pretty-printed with two-space indents.

---

## 1. The envelope

```json
{
  "format": "odd-eve-basketball/save",
  "version": 2,
  "saved":  "2026-09-15T09:18:57.560Z",
  "name":   "You 15–12 Engine",
  "label":  "You 15–12 Engine · beat 73",
  "rules":   { ... },
  "engine":  { ... },
  "summary": { ... },
  "beats":   [ ... ],
  "state":   { ... }
}
```

| field | type | meaning |
|---|---|---|
| `format` | string | always `odd-eve-basketball/save`. Anything else is not one of these files. |
| `version` | number | `2`. Version 1 files carried only a thin log and are refused by this page. |
| `saved` | ISO-8601 UTC | when the file was written, which is not when the game was played. |
| `name` | string | what the save was called. Free text, up to 40 characters from the slot dialog. |
| `label` | string | one-line description: score and beat number at the moment of saving. |
| `rules` | object | §2 — the rules the game was played under. |
| `engine` | object | §3 — what the opponent was. |
| `summary` | object | §4 — everything derivable from `beats`, worked out for you. |
| `beats` | array | §5 — the game itself, one object per beat, in order. |
| `state` | object | §6 — the position the game stands at. |

Two sides appear throughout, always spelled `"you"` (the human) and `"eng"`
(the engine).

---

## 2. `rules`

The rules the game ran on, so a file stays readable if the rules later change.

```json
"rules": {
  "target": 15,
  "chargeCap": 60,
  "shootMinCharge": 5,
  "dunkMinCharge": 10,
  "shotPoints": 2,
  "chargeGain": { "1":1, "2":1, "3":1, "4":2, "5":2, "11":2, "12":4, "13":6 },
  "numbers": { "0":"dunk", "1":"dribble", ..., "8":"penalty", "11":"boost" },
  "defenderActions": [1,2,3,4,5,6,7,8,9,10,11,12,13],
  "dunk": {
    "number": 0,
    "formula": "0.5k^2 - 0.5k + 3 points, k = floor(charges / 10)",
    "cost": 10,
    "blockable": false,
    "keepsPossession": true,
    "points": { "10":3, "20":4, "30":6, "40":9, "50":13, "60":18 }
  },
  "match": "Identical numbers hand the ball over and reset charges; ..."
}
```

| field | meaning |
|---|---|
| `target` | points needed to win. |
| `chargeCap` | the highest charge count the solved table covers. A charge gain that would pass it is not a legal move. |
| `shootMinCharge` | charges needed before 6 or 7 may be shown. |
| `dunkMinCharge` | charges needed before 0, 11, 12 or 13 may be shown. |
| `shotPoints` | points for an unblocked shot. |
| `chargeGain` | charges each non-scoring number adds, keyed by number. |
| `numbers` | every number's kind: `dunk`, `dribble`, `pass`, `shot`, `penalty`, `boost`. |
| `defenderActions` | what the defender may show. 0 is absent, which is why a dunk cannot be matched. |
| `dunk.points` | the reward at each ten charges, so a reader never has to evaluate the formula. |
| `match` | the matching rule in prose. |

## 3. `engine`

```json
"engine": {
  "kind": "exact-equilibrium",
  "opponent": "engine",
  "table": { "shape": [15, 15, 61], "dtype": "float32", "checksum": "fnv1a:a47d32ae" },
  "note": "Win probabilities for the player in possession, ..."
}
```

`table.checksum` is FNV-1a over the packed win-probability table the page
carries. Two files with the same checksum were played against the same solve;
a different checksum means the table was rebuilt, and probabilities in the two
files are not strictly comparable. `shape` is `[target, target, chargeCap + 1]`.

## 4. `summary`

Derived entirely from `beats`. Nothing here is needed to rebuild the game —
it is written out so a reader does not have to recount it, and it is checked
against a recount when the file is loaded.

| field | meaning |
|---|---|
| `beats` | number of beats played. |
| `possessions` | total possessions, counting the opening toss. |
| `turnovers` | beats where the numbers matched: `tackles + blocks`. |
| `tackles` | matched beats that were not shots. |
| `blocks` | matched shots. |
| `toss` | who started on offense, `"you"` or `"eng"`. |
| `startedAt`, `endedAt` | ISO-8601 UTC. `endedAt` is `null` while a game is unfinished. |
| `durationMs` | wall-clock length, or `null` if either timestamp is missing. |
| `over` | whether the game finished. |
| `winner` | `"you"`, `"eng"`, or `null` if unfinished. |
| `score` | `{ "you": n, "eng": n }` as it stands. |
| `yourWinProb` | your win probability at the current position, 0–1. |
| `leadChanges` | how many times the lead changed hands. |
| `largestLead` | `{ "you": n, "eng": n }`, the biggest margin each side held. |
| `biggestSwing` | `{ "n": beat, "delta": ±p }` — the beat that moved your win probability furthest. |
| `scoreLine` | one entry per scoring beat: `{ n, by, how, points, you, eng }`. |
| `you`, `eng` | per-side statistics, below. |

Per side:

| field | meaning |
|---|---|
| `points` | total scored. |
| `scores` | each scoring play's points, in order. |
| `dunks`, `shots` | successful dunks, and shots that went in. |
| `shotsBlocked` | this side's shots that were matched. |
| `tackled` | times this side lost the ball to a match while holding it. |
| `steals` | times this side took the ball by matching. |
| `possessions` | possessions held. |
| `beatsOnOffense`, `beatsOnDefense` | beats played in each role. |
| `chargesGained` | total charges accumulated across the game. |
| `chargePeak` | highest charge count reached. |
| `dunkCharges` | the charge count each dunk was cashed at. |
| `numbers` | how often this side showed each number, keyed by number. |

---

## 5. `beats` — the game

One object per beat, in playing order, `n` running from 1. This is the part
the rest of the file is derived from.

```json
{
  "n": 44,
  "t": "2026-09-15T09:18:57.522Z",
  "sinceStartMs": 794,
  "sincePrevMs": 4,
  "offSide": "eng",
  "defSide": "you",
  "offNum": 0,
  "defNum": 1,
  "kind": "big",
  "text": "DUNK — 4 points",
  "sub": "unblockable · 21 → 11 charges · possession kept",
  "you": { "role": "defense", "number": 1, "label": "dribble", "equilibrium": 0.062178 },
  "eng": { "role": "offense", "number": 0, "label": "dunk", "equilibrium": 1,
           "drawnFrom": { "0": 1 }, "uniformFallback": false },
  "outcome": { "event": "dunk", "points": 4, "scoredBy": "eng", "chargeDelta": -10,
               "matched": false, "turnover": false, "possessionAfter": "eng" },
  "before": { "you": 0, "eng": 0, "holder": "eng", "charges": 21,
              "yourWinProb": 0.263609, "ballWinProb": 0.736391 },
  "after":  { "you": 0, "eng": 4, "holder": "eng", "charges": 11, "over": false,
              "yourWinProb": 0.263609, "ballWinProb": 0.736391 },
  "equilibrium": {
    "offenseMix": { "0": 1 },
    "defenseMix": { "1": 0.062178, "2": 0.062178, "3": 0.062178, "4": 0.107411,
                    "5": 0.107411, "11": 0.107411, "12": 0.203604, "13": 0.28763 },
    "offenseValue": 0.736391,
    "legalOffense": [1, 2, 3, 4, 5, 6, 7, 0, 11, 12, 13],
    "tackleRisk": 0,
    "cashOut": true,
    "dunkPoints": 4
  }
}
```

That beat reads: on beat 44 the engine held the ball at 0–0 with 21 charges,
you guessed 1 on defense, the engine dunked for 4 and kept the ball with 11
charges left. Cashing out was the whole of its equilibrium there, so the dunk
carries weight 1 and the position was worth the same before and after it —
which is what an exactly solved game looks like when it takes the move it is
supposed to.

### When

| field | type | meaning |
|---|---|---|
| `n` | integer ≥ 1 | beat number, and the index in the array plus one. |
| `t` | ISO-8601 UTC or `null` | when the beat was played. `null` if the file carried no usable timestamp. |
| `sinceStartMs` | integer or `null` | milliseconds from the first tip-off. |
| `sincePrevMs` | integer or `null` | milliseconds since the previous beat — how long the player took. |

### Who played what

| field | type | meaning |
|---|---|---|
| `offSide` | `"you"` \| `"eng"` | who held the ball going into the beat. |
| `defSide` | `"you"` \| `"eng"` | the other one. |
| `offNum` | 0–13 | the number the ball carrier showed. |
| `defNum` | 1–13 | the number the defender showed. Never 0. |
| `you`, `eng` | object | the same beat told per side, below. |

Each side's object:

| field | meaning |
|---|---|
| `role` | `"offense"` or `"defense"` on this beat. |
| `number` | the number that side showed. Equal to `offNum` or `defNum` depending on `role`. |
| `label` | that number's kind: `dunk`, `dribble`, `pass`, `shot`, `boost`, `penalty`. |
| `equilibrium` | the weight the equilibrium mix for that side's role put on the number actually shown, 0–1. Zero means the move was off book. |

`eng` carries two more:

| field | meaning |
|---|---|
| `drawnFrom` | the mix the engine sampled its number from — the equilibrium mix for whichever role it had. |
| `uniformFallback` | `true` in the one case where the ball carrier has no matchable move at all and the defender guesses evenly instead. False in every ordinary beat. |

### What happened

`outcome`:

| field | meaning |
|---|---|
| `event` | `dribble`, `pass`, `boost`, `shot`, `dunk`, `tackle`, `block`. `tackle` and `block` are matched beats; `block` is a matched shot. |
| `points` | points scored on the beat, 0 if none. |
| `scoredBy` | `"you"`, `"eng"` or `null`. |
| `chargeDelta` | change in the ball carrier's charge count: `+1`/`+2`/`+4`/`+6` building, `−10` for a dunk, and the whole stack lost on a turnover. |
| `matched` | both players showed the same number. |
| `turnover` | possession changed — true for a match and for a made shot. |
| `possessionAfter` | who holds the ball after the beat. |

`kind` is the page's display class for the beat: `ok` (a build), `score` (a
shot), `big` (a dunk), `bad` (a turnover). `text` and `sub` are the two lines
the page showed at the time, e.g. `"DUNK — 4 points"` and `"unblockable · 21 →
11 charges · possession kept"`. They are regenerated from the rules when a
file is loaded, so they are for reading, not for trusting.

### Where it stood

`before` and `after` are full positions:

| field | meaning |
|---|---|
| `you`, `eng` | the score. |
| `holder` | who has the ball. |
| `charges` | the holder's charge count. |
| `over` | (`after` only) whether that beat ended the game. |
| `yourWinProb` | your win probability from that position, 0–1, six decimal places. |
| `ballWinProb` | the ball carrier's win probability, or `null` once the game is decided. |

`before` of beat *n* always equals `after` of beat *n−1*; beat 1's `before` is
0–0 with no charges, held by `state.toss`.

### What it was played against

`equilibrium` describes the position in `before`, not the position after:

| field | meaning |
|---|---|
| `offenseMix` | the ball carrier's equilibrium mix: number → probability. |
| `defenseMix` | the defender's equilibrium mix. Covers only matchable numbers, so it may not mention every legal one. |
| `offenseValue` | the value of the beat to the ball carrier — the same number as `before.ballWinProb`. |
| `legalOffense` | every number the carrier could have shown at that charge count. |
| `tackleRisk` | probability the ball changes hands on this beat under equilibrium play by both sides. Zero when the carrier is cashing out, because a dunk cannot be matched. |
| `cashOut` | whether equilibrium dunks here. |
| `dunkPoints` | what a dunk would pay at this charge count, or `null` below the gate. |

Probabilities are rounded to six decimal places. Mixes sum to 1 to within
rounding; a mix omits any number it puts no weight on.

---

## 6. `state`

Where the game stands. Scores, possession and charges are all re-derived from
`beats` on load and must agree with this block, so it is a checksum as much as
a position.

| field | meaning |
|---|---|
| `started`, `ended` | ISO-8601 UTC. `ended` is `null` until the game finishes. |
| `toss` | who started on offense. Every reconstruction begins here. |
| `you`, `eng` | the score. |
| `holder` | who has the ball. |
| `charges` | the holder's charge count. |
| `beat` | beats played. Always equal to `beats.length`. |
| `over` | whether the game is finished. |
| `tackles` | matched beats, the same number as `summary.turnovers`. |
| `yourPoints`, `engPoints` | each side's scoring plays in order. |
| `last` | the beat the arena was showing: `{ offSide, offNum, defNum, matched }`, or `null` before the first beat. |
| `view` | the verdict panel: `{ kind, text, sub }`. |
| `archived` | whether this game has already been counted in the win–loss record. |

---

## 7. Rebuilding a game from the file

Everything except the toss and the two numbers per beat is derived, so a
reader can ignore the rest and still reproduce the game exactly:

```
state = { you: 0, eng: 0, holder: state.toss, charges: 0 }
for each beat in beats:
    off = state.holder,  def = the other side
    if beat.offNum == 0:                       # dunk
        state[off]    += dunkPoints(state.charges)
        state.charges -= 10
    else if beat.offNum == beat.defNum:        # tackle, or a blocked shot
        state.holder = def;  state.charges = 0
    else if beat.offNum in (6, 7):             # shot
        state[off] += 2;  state.holder = def;  state.charges = 0
    else:                                      # dribble, pass or boost
        state.charges = min(chargeCap, state.charges + chargeGain[beat.offNum])
    # the game is over the moment a side reaches target
```

This is what the page does when you import a file, and what `replay.py` does
from Python:

```bash
python3 replay.py odd-eve-15-12-beat73.json     # transcript and full check
python3 replay.py odd-eve-history.json --quiet  # check every game, no transcript
```

`replay.py` rebuilds the game with `rules.py` — a separate implementation of
the same rules — and then checks every field the file states against what the
rules produce, the summary included. It exits non-zero on the first thing that
does not add up.

### What gets a file rejected

The page refuses a file rather than half-loading it when:

- `format` is not `odd-eve-basketball/save`, or `version` is not `2`;
- `state.toss` or `state.holder` is not `"you"` or `"eng"`, or a score, charge
  count or beat count is not an integer in range;
- `beats.length` and `state.beat` disagree;
- a beat's `offSide` is not the side the reconstruction says holds the ball;
- `offNum` is not legal at that charge count, or `defNum` is outside 1–13;
- the game continues after a side has reached `target`;
- the move list does not arrive at the score, possession and charge count in
  `state`.

Anything else in the file — the mixes, win probabilities, summary, verdict
text — is recomputed from the rules and the solved table on load, so a damaged
or edited analysis field cannot make the page show a game that was not played.

---

## 8. The history file

**export** next to the win–loss record writes every finished game the browser
still holds.

```json
{
  "format": "odd-eve-basketball/history",
  "version": 2,
  "exported": "2026-09-15T09:19:02.118Z",
  "rules":  { ... },
  "engine": { ... },
  "record": { "played": 12, "won": 5, "lost": 7, "withEveryBeat": 10 },
  "games": [
    { "won": false, "you": 9, "eng": 15, "beats": 75, "tackles": 11,
      "date": "2026-09-15T09:18:57.560Z", "detail": "full",
      "game": { "format": "odd-eve-basketball/save", "version": 2, ... } }
  ]
}
```

Each entry's `game` is a complete save envelope as described above, so a game
can be lifted straight out of a history file and read — or imported — on its
own.

`detail` is `"full"` when `game` carries every beat, and `"summary"` when it is
`null`. Browser storage is small and a game is 100–200 KB, so only the most
recent ten finished games keep their beats there; older ones keep the result
row only. Download a game while it is still recent — or export the history —
and nothing is lost, as exported files are never trimmed.

`record.withEveryBeat` says how many of the games in the file can be replayed.
