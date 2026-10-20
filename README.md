# How to Stop a Coding Agent and an AI Reviewer From Looping on One Pull Request

**TL;DR:** An agent and an AI reviewer stop looping only when a review finds nothing to fix. Let only new, important problems on changed lines block, and stop after two clean reviews in a row.

Published from [The AI Commit](https://theaicommit.com/#2026-10-20/code) — AI Engineering Practices, 2026-10-20.

## Run

```bash
python3 code_example.py
```

## Output

```
4000 seeded pull requests, reviewer recall per pass = 50%

fix everything, stop at first clean pass
  fix rounds per PR 2.07   5+ rounds 16.5%   bugs escaped 13.1%   sent to a person 0.0%
block only new important findings, 1 clean pass
  fix rounds per PR 0.77   5+ rounds 0.0%   bugs escaped 24.4%   sent to a person 7.1%
block only new important findings, 2 clean passes
  fix rounds per PR 1.01   5+ rounds 0.0%   bugs escaped 13.1%   sent to a person 13.4%

```

## Code

See [`code_example.py`](code_example.py).
