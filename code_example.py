"""A stop rule for the loop where a coding agent fixes what an AI reviewer flags.

The loop runs: review the pull request, the agent fixes what was flagged, review again.
It ends at the first pass that blocks nothing. So what you allow to block decides how many
rounds you get, and one clean pass from a reviewer that misses half the bugs proves little.

ReviewGate below is the part to lift. It reads one review pass of findings and decides:
"fix" (hand the agent the blocking list), "pass", or "escalate" (a person takes over).
The simulation under it scores three policies on the same seeded pull requests.

Run: python3 code_example.py
"""
import random
from dataclasses import dataclass, field

REQUIRED_CLEAN = 2      # clean passes in a row before the gate passes. 1 = the usual loop
MAX_FIX_ROUNDS = 3      # agent fix rounds before a person decides
RECALL = 0.5            # chance one pass catches a given real bug. Raise it and k=1 looks better


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    rule: str           # the reviewer's name for the problem, e.g. "null-deref"
    severity: str       # "important" or "nit", as the reviewer tags it

    @property
    def key(self):      # the same problem on the same line is the same finding next round
        return (self.path, self.line, self.rule)


@dataclass
class ReviewGate:
    changed: set                                  # {(path, line)} the pull request touches
    seen: set = field(default_factory=set)
    notes: list = field(default_factory=list)     # non-blocking: posted once, never fixed here
    clean_streak: int = 0
    fix_rounds: int = 0

    def decide(self, findings):
        blocking = []
        for f in findings:
            if f.key in self.seen:
                continue                          # never post the same thing twice
            self.seen.add(f.key)
            on_change = (f.path, f.line) in self.changed
            if f.severity == "important" and on_change:
                blocking.append(f)
            else:
                self.notes.append(f)              # nits and old code: a list, not a round
        if not blocking:
            self.clean_streak += 1
            return ("pass", []) if self.clean_streak >= REQUIRED_CLEAN else ("review", [])
        self.clean_streak = 0
        if self.fix_rounds >= MAX_FIX_ROUNDS:
            return ("escalate", blocking)         # the loop is not converging; ask a person
        self.fix_rounds += 1
        return ("fix", blocking)


# ---- simulation: a reviewer that misses bugs and invents nits, an agent that fixes all ----
def simulate(policy, prs=4000, seed=7):
    rng = random.Random(seed)
    fix_rounds, escaped, introduced, escalated = [], 0, 0, 0
    for n in range(prs):
        size = rng.choice([30, 80, 200, 600, 1500])            # changed lines
        bugs = {("a.py", i, "bug") for i in range(size) if rng.random() < 0.003}
        old = {("a.py", -i, "old") for i in range(1, 2 * size) if rng.random() < 0.0015}
        introduced += len(bugs)
        gate = ReviewGate(changed={("a.py", i) for i in range(size)})
        rounds, uid = 0, 0
        for _ in range(60):
            found = [Finding(*b, "important") for b in bugs if rng.random() < RECALL]
            found += [Finding(*o, "important") for o in old if rng.random() < 0.15]
            for i in range(size):                  # low-value comments, fresh every pass
                if rng.random() < 0.0006:
                    uid += 1; found.append(Finding("a.py", i, f"nit{uid}", "nit"))
                if rng.random() < 0.0003:          # a confident false "important"
                    uid += 1; found.append(Finding("a.py", i, f"fp{uid}", "important"))
            if policy == "fix everything, stop at first clean pass":
                todo = found                       # every comment blocks, every pass
                verdict = "fix" if todo else "pass"
            else:
                verdict, todo = gate.decide(found)
            if verdict in ("pass", "escalate"):
                escalated += verdict == "escalate"
                break
            if verdict == "review":
                continue                           # clean, but not clean enough yet
            rounds += 1
            fixed = {(f.path, f.line, f.rule) for f in todo}
            bugs -= fixed; old -= fixed
            for f in todo:                         # each fix commit can add a new bug
                if rng.random() < 0.05:
                    uid += 1; bugs.add(("a.py", rng.randrange(size), f"bug{uid}"))
                    introduced += 1
        fix_rounds.append(rounds); escaped += len(bugs)
    return {
        "fix rounds per PR": sum(fix_rounds) / prs,
        "PRs with 5+ rounds": sum(r >= 5 for r in fix_rounds) / prs,
        "bugs that escaped": escaped / introduced,
        "sent to a person": escalated / prs,
    }


def main():
    global REQUIRED_CLEAN
    rows = [("fix everything, stop at first clean pass", None),
            ("block only new important findings, 1 clean pass", 1),
            ("block only new important findings, 2 clean passes", 2)]
    print(f"4000 seeded pull requests, reviewer recall per pass = {RECALL:.0%}\n")
    for name, k in rows:
        if k:
            REQUIRED_CLEAN = k
        r = simulate(name)
        print(name)
        print(f"  fix rounds per PR {r['fix rounds per PR']:.2f}   "
              f"5+ rounds {r['PRs with 5+ rounds']:.1%}   "
              f"bugs escaped {r['bugs that escaped']:.1%}   "
              f"sent to a person {r['sent to a person']:.1%}")


if __name__ == "__main__":
    main()
