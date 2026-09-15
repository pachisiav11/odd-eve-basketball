"""Read a game back out of an exported JSON file and play it again.

The page writes every beat of a game to JSON: both numbers, both roles, the
position before and after, and the equilibrium mixes the beat was played
against.  This script takes that file and rebuilds the game from the move list
alone, using the transition rules in rules.py -- a second implementation, in a
different language, that never sees the browser's arithmetic.

Every field the file states is then checked against what the rules produce, so
a file that passes here really does contain the whole game and not a summary
of it.  Prints a beat-by-beat transcript unless asked not to.

    python3 replay.py odd-eve-15-12-beat73.json
    python3 replay.py odd-eve-history.json --quiet

Reads a single game or a whole exported history.  Exit status is 0 only if
every game in the file checks out.
"""

import argparse
import json
import sys

from rules import (
    BOOSTS,
    CHARGE_GAIN,
    DEFENDER_ACTIONS,
    DRIBBLES,
    DUNK,
    DUNK_MIN_CHARGE,
    PASSES,
    SHOOT_MIN_CHARGE,
    SHOTS,
    TARGET,
    dunk_points_triangular,
    offense_actions,
)

SAVE_FORMAT = "odd-eve-basketball/save"
HIST_FORMAT = "odd-eve-basketball/history"
VERSION = 2

LABELS = {DUNK: "dunk"}
LABELS.update({n: "dribble" for n in DRIBBLES})
LABELS.update({n: "pass" for n in PASSES})
LABELS.update({n: "shot" for n in SHOTS})
LABELS.update({n: "penalty" for n in (8, 9, 10)})
LABELS.update({n: "boost" for n in BOOSTS})


class Mismatch(Exception):
    """The file says one thing and the rules say another."""


def check(ok, what):
    if not ok:
        raise Mismatch(what)


def other(side):
    return "eng" if side == "you" else "you"


def step(state, off_num, def_num, cap):
    """Apply one beat to a position.  The rules, and nothing else.

    Returns the position afterwards and what happened, in the same shape the
    save file uses, so the two can be compared field by field.
    """
    off = state["holder"]
    new = dict(state)
    out = {
        "event": None,
        "points": 0,
        "scoredBy": None,
        "matched": False,
        "turnover": False,
    }

    if off_num == DUNK:
        points = dunk_points_triangular(state["charges"])
        new[off] += points
        new["charges"] = state["charges"] - 10
        out.update(event="dunk", points=points, scoredBy=off)
    elif off_num == def_num:
        out.update(
            event="block" if off_num in SHOTS else "tackle",
            matched=True,
            turnover=True,
        )
        new["holder"] = other(off)
        new["charges"] = 0
    elif off_num in SHOTS:
        new[off] += 2
        new["holder"] = other(off)
        new["charges"] = 0
        out.update(event="shot", points=2, scoredBy=off, turnover=True)
    else:
        gain = CHARGE_GAIN[off_num]
        new["charges"] = min(cap, state["charges"] + gain)
        out["event"] = LABELS[off_num]

    out["chargeDelta"] = new["charges"] - state["charges"]
    out["possessionAfter"] = new["holder"]
    return new, out


def check_rules(rules):
    """The file carries the rules it was played under.  Refuse to verify a game
    played under rules this checkout does not implement, rather than report
    false mismatches on every beat."""
    check(rules["target"] == TARGET, f"file targets {rules['target']}, rules.py targets {TARGET}")
    check(rules["shootMinCharge"] == SHOOT_MIN_CHARGE, "shot gate differs from rules.py")
    check(rules["dunkMinCharge"] == DUNK_MIN_CHARGE, "dunk gate differs from rules.py")
    check(
        {int(k): v for k, v in rules["chargeGain"].items()} == CHARGE_GAIN,
        "charge gains differ from rules.py",
    )
    check(
        sorted(rules["defenderActions"]) == sorted(DEFENDER_ACTIONS),
        "defender action set differs from rules.py",
    )
    for charges, points in rules["dunk"]["points"].items():
        check(
            dunk_points_triangular(int(charges)) == points,
            f"file pays {points} for a dunk at {charges} charges, "
            f"rules.py pays {dunk_points_triangular(int(charges))}",
        )


def check_beat(e, n, state, after, out, cap):
    """Everything one beat claims, against what the rules just produced."""
    where = f"beat {n}"
    check(e["n"] == n, f"{where}: numbered {e['n']}")
    check(e["offSide"] == state["holder"], f"{where}: offense is {e['offSide']}, ball is with {state['holder']}")
    check(e["defSide"] == other(state["holder"]), f"{where}: defSide wrong")
    check(e["defNum"] in DEFENDER_ACTIONS, f"{where}: defender showed {e['defNum']}")
    check(
        e["offNum"] in offense_actions(state["charges"], cap),
        f"{where}: {e['offNum']} is not legal at {state['charges']} charges",
    )

    for key, want in (("you", None), ("eng", None)):
        side = e[key]
        num = e["offNum"] if state["holder"] == key else e["defNum"]
        role = "offense" if state["holder"] == key else "defense"
        check(side["number"] == num, f"{where}: {key} number {side['number']} != {num}")
        check(side["role"] == role, f"{where}: {key} role {side['role']} != {role}")
        check(side["label"] == LABELS[num], f"{where}: {key} label {side['label']} != {LABELS[num]}")

    for key in ("you", "eng", "holder", "charges"):
        check(e["before"][key] == state[key], f"{where}: before.{key} is {e['before'][key]}, rules say {state[key]}")
        check(e["after"][key] == after[key], f"{where}: after.{key} is {e['after'][key]}, rules say {after[key]}")
    check(
        e["after"]["over"] == (after["you"] >= TARGET or after["eng"] >= TARGET),
        f"{where}: after.over wrong",
    )

    for key, value in out.items():
        check(e["outcome"][key] == value, f"{where}: outcome.{key} is {e['outcome'][key]}, rules say {value}")

    eq = e["equilibrium"]
    check(
        eq["legalOffense"] == offense_actions(state["charges"], cap),
        f"{where}: legalOffense does not match the rules",
    )
    for which in ("offenseMix", "defenseMix"):
        total = sum(eq[which].values())
        check(abs(total - 1) < 1e-4, f"{where}: {which} sums to {total:.6f}")
    expect_dunk = dunk_points_triangular(state["charges"]) if state["charges"] >= DUNK_MIN_CHARGE else None
    check(eq["dunkPoints"] == expect_dunk, f"{where}: dunkPoints is {eq['dunkPoints']}, rules say {expect_dunk}")
    drawn = e["eng"]["drawnFrom"]
    check(
        drawn == (eq["offenseMix"] if e["eng"]["role"] == "offense" else eq["defenseMix"]),
        f"{where}: the engine's mix is not the equilibrium mix for its role",
    )


def blank_side():
    return {
        "points": 0, "scores": [], "dunks": 0, "shots": 0, "shotsBlocked": 0,
        "tackled": 0, "steals": 0, "possessions": 0, "beatsOnOffense": 0,
        "beatsOnDefense": 0, "chargesGained": 0, "chargePeak": 0,
        "dunkCharges": [], "numbers": {},
    }


def verify(save, show=True, out=sys.stdout):
    """Replay one exported game and check every field in it.

    Returns a one-line result.  Raises Mismatch on the first thing the rules
    disagree with.
    """
    check(isinstance(save, dict), "not an object")
    check(save.get("format") == SAVE_FORMAT, f"format is {save.get('format')!r}")
    check(save.get("version") == VERSION, f"version is {save.get('version')!r}, this reader wants {VERSION}")
    for key in ("rules", "engine", "summary", "beats", "state"):
        check(key in save, f"no {key} block")

    rules, state_block, beats = save["rules"], save["state"], save["beats"]
    check_rules(rules)
    cap = rules["chargeCap"]

    toss = state_block["toss"]
    check(toss in ("you", "eng"), f"toss is {toss!r}")
    check(len(beats) == state_block["beat"], "the file's beat count and its beat list disagree")

    state = {"you": 0, "eng": 0, "holder": toss, "charges": 0}
    side = {"you": blank_side(), "eng": blank_side()}
    side[toss]["possessions"] = 1
    score_line = []
    turnovers = tackles = blocks = 0

    if show:
        print(f"{'':>4}  {'ball':<5} {'you':<13} {'engine':<13} {'result':<26} "
              f"{'charges':<9} {'score':<7} your win", file=out)

    for i, e in enumerate(beats):
        after, outcome = step(state, e["offNum"], e["defNum"], cap)
        check_beat(e, i + 1, state, after, outcome, cap)

        off, deff = state["holder"], other(state["holder"])
        side[off]["beatsOnOffense"] += 1
        side[deff]["beatsOnDefense"] += 1
        for key in ("you", "eng"):
            num = str(e[key]["number"])
            side[key]["numbers"][num] = side[key]["numbers"].get(num, 0) + 1
        if outcome["points"]:
            scorer = side[outcome["scoredBy"]]
            scorer["points"] += outcome["points"]
            scorer["scores"].append(outcome["points"])
            score_line.append({
                "n": i + 1, "by": outcome["scoredBy"], "how": outcome["event"],
                "points": outcome["points"], "you": after["you"], "eng": after["eng"],
            })
        if outcome["event"] == "dunk":
            side[off]["dunks"] += 1
            side[off]["dunkCharges"].append(state["charges"])
        if outcome["event"] == "shot":
            side[off]["shots"] += 1
        if outcome["event"] == "block":
            side[off]["shotsBlocked"] += 1
            side[deff]["steals"] += 1
            blocks += 1
        if outcome["event"] == "tackle":
            side[off]["tackled"] += 1
            side[deff]["steals"] += 1
            tackles += 1
        if outcome["matched"]:
            turnovers += 1
        if outcome["chargeDelta"] > 0:
            side[off]["chargesGained"] += outcome["chargeDelta"]
        side[off]["chargePeak"] = max(side[off]["chargePeak"], state["charges"], after["charges"])
        if after["holder"] != off:
            side[after["holder"]]["possessions"] += 1

        if show:
            print(
                f"{i + 1:>4}  {('YOU' if off == 'you' else 'ENG'):<5} "
                f"{e['you']['number']:>2} {e['you']['label']:<10} "
                f"{e['eng']['number']:>2} {e['eng']['label']:<10} "
                f"{e['text']:<26} "
                f"{state['charges']:>2} → {after['charges']:<3} "
                f"{after['you']:>2}–{after['eng']:<3} "
                f"{e['after']['yourWinProb'] * 100:5.1f}%",
                file=out,
            )

        state = after
        if state["you"] >= TARGET or state["eng"] >= TARGET:
            check(i == len(beats) - 1, f"beat {i + 1} won the game but the file carries more beats")

    for key in ("you", "eng", "holder", "charges"):
        check(
            state_block[key] == state[key],
            f"the file ends at {key}={state_block[key]}, the moves end at {state[key]}",
        )

    # The summary is derived, so it has to agree with a recount.
    s = save["summary"]
    recount = {
        "beats": len(beats), "turnovers": turnovers, "tackles": tackles, "blocks": blocks,
        "toss": toss, "possessions": side["you"]["possessions"] + side["eng"]["possessions"],
        "over": state["you"] >= TARGET or state["eng"] >= TARGET,
        "score": {"you": state["you"], "eng": state["eng"]},
        "scoreLine": score_line,
    }
    for key, value in recount.items():
        check(s[key] == value, f"summary.{key} is {s[key]!r}, a recount gives {value!r}")
    winner = ("you" if state["you"] >= TARGET else "eng") if recount["over"] else None
    check(s["winner"] == winner, f"summary.winner is {s['winner']!r}, the moves say {winner!r}")
    for key in ("you", "eng"):
        for field, value in side[key].items():
            check(
                s[key][field] == value,
                f"summary.{key}.{field} is {s[key][field]!r}, a recount gives {value!r}",
            )

    result = (
        f"{len(beats)} beats · {turnovers} turnovers "
        f"({tackles} tackles, {blocks} blocks) · "
        f"final {state['you']}–{state['eng']} · "
        + (f"{'you' if winner == 'you' else 'the engine'} won" if winner else "unfinished")
    )
    return result


def games_in(doc):
    """A file is either one save or a whole exported history."""
    if isinstance(doc, dict) and doc.get("format") == HIST_FORMAT:
        for i, row in enumerate(doc.get("games", [])):
            label = f"game {i + 1} ({row.get('you')}–{row.get('eng')}, {row.get('date', '')[:10]})"
            yield label, row.get("game"), row.get("detail")
    else:
        yield "game", doc, "full"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("path", help="an exported .json game or history file")
    ap.add_argument("-q", "--quiet", action="store_true", help="check only, no transcript")
    args = ap.parse_args(argv)

    with open(args.path, encoding="utf-8") as fh:
        doc = json.load(fh)

    failures = skipped = checked = 0
    for label, save, detail in games_in(doc):
        if save is None:
            skipped += 1
            print(f"{label}: no beats in the file ({detail}) — nothing to replay")
            continue
        if not args.quiet:
            print(f"\n=== {label} ===")
        try:
            print(f"{label}: OK — {verify(save, show=not args.quiet)}")
            checked += 1
        except (Mismatch, KeyError, TypeError) as exc:
            failures += 1
            kind = "missing field" if isinstance(exc, KeyError) else "mismatch"
            print(f"{label}: FAILED ({kind}) — {exc}", file=sys.stderr)

    print(f"\n{checked} game(s) replayed and verified, {failures} failed, {skipped} without beats")
    return 1 if failures else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:      # piping into head is a normal way to read this
        sys.stderr.close()
