# Completed Tasks

- Added: 2026-09-12 16:40 | Completed: 2026-09-12 17:02 | Confirm ambiguous rules with the user (defender action set, 11/12/13 unlock persistence, win threshold, shot-clock).
- Added: 2026-09-12 16:40 | Completed: 2026-09-12 17:02 | Write rules.py — pure transition function and legal action sets.
- Added: 2026-09-12 16:40 | Completed: 2026-09-12 17:02 | Write matgame.py — closed-form solver for one beat, plus an LP reference.
- Added: 2026-09-12 16:40 | Completed: 2026-09-12 17:02 | Write solver.py — score-layer ordering plus backward induction over charges.
- Added: 2026-09-12 16:40 | Completed: 2026-09-12 17:02 | Validate solver — LP cross-check on the beat solver, simulated win rate 0.5015 vs exact 0.5000, charge cap 60 vs 100 agree to 7 decimals.
- Added: 2026-09-12 16:40 | Completed: 2026-09-12 17:02 | Write analyze.py — dunk threshold, tackle rate, shot usage, push-or-cash crossover.
- Added: 2026-09-12 16:40 | Completed: 2026-09-12 17:02 | Sweep reward functions and compare risk/reward crossover.
- Added: 2026-09-12 16:40 | Completed: 2026-09-12 17:08 | Write up findings and a recommendation on the dunk reward formula.
- Added: 2026-09-12 17:20 | Completed: 2026-09-12 17:23 | Build a playable HTML page against the solved equilibrium, verified in the browser.
- Added: 2026-09-12 17:23 | Completed: 2026-09-12 17:43 | Verify the engine is unexploitable after a player reported spamming 5; confirmed no bug (exhaustive scan plus 20,000-game test).
- Added: 2026-09-12 17:23 | Completed: 2026-09-12 17:43 | Create GitHub repo and publish index.html as a static site.
- Added: 2026-09-15 09:05 | Completed: 2026-09-15 09:26 | Export the whole game to JSON rather than a result: every beat with both numbers, the position before and after, the equilibrium mixes and the timings, plus a derived summary and the rules the game was played under.
- Added: 2026-09-15 09:05 | Completed: 2026-09-15 09:26 | Rebuild a loaded game from its move list through the live transition function, and reject a file whose moves do not add up.
- Added: 2026-09-15 09:05 | Completed: 2026-09-15 09:26 | Replay viewer: step, scrub or play any game back in the page, read-only, including games in the archive.
- Added: 2026-09-15 09:05 | Completed: 2026-09-15 09:26 | Write replay.py and SAVE_FORMAT.md — verify an exported file against rules.py, and document every field of it.
