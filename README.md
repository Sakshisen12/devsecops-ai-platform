# DevSecOps AI Platform

An automated CI/CD pipeline that combines traditional static security scanning with an AI code reviewer, producing a single HTML audit report on every push.

## What it does

On every push to `main`, the Azure Pipeline:

1. **Sets up** a Python 3.11 environment
2. **Installs** dependencies from `requirements.txt`
3. **Runs unit tests** with `pytest`, publishing JUnit results to the Azure DevOps summary screen
4. **Runs a static security scan** with [Bandit](https://bandit.readthedocs.io/) against `app.py`, catching issues like hardcoded credentials and unsafe shell calls
5. **Runs an AI code review** using the Gemini API (`review_code.py`), which reads the source and flags issues a static scanner can't — logic errors, unclear intent, missing validation
6. **Generates a single HTML dashboard** (`generate_report.py` → `index.html`) that merges the Bandit findings and the AI review into one audit report
7. **Publishes** the dashboard as a pipeline artifact, downloadable from the Azure DevOps run

## Why both Bandit *and* an AI reviewer

Bandit is a pattern-matching SAST tool — fast, deterministic, but limited to known-bad patterns (e.g. `os.system`, hardcoded secrets, `eval`). It won't catch things like "this discount function should validate its inputs more defensively" or "this error message leaks internal state." Layering a Gemini-based review on top adds that second, more contextual pass, closer to what a human reviewer would flag in a PR.

## Demo vulnerabilities

`app.py` intentionally contains two seeded flaws so the pipeline has something real to catch and report on:

- **Hardcoded secret key** — a fake production API key committed directly in source
- **Command injection risk** — `run_system_health_check()` builds a shell command from unsanitized input and passes it to `os.system()`

These aren't bugs in the pipeline — they're fixtures to prove the scanning stage actually works. In a real deployment, `app.py` would be your service code and these patterns would be things Bandit/Gemini catch *before* merge, not demo material.

## Pipeline behavior on findings

Bandit results are captured to `bandit_results.json`. The pipeline currently reports findings but does not block the build on them — see "Known limitations" below for how that's expected to change.

## Local setup

```bash
pip install -r requirements.txt
python app.py
```

To run the security scan locally:

```bash
bandit -r app.py -f json -o bandit_results.json
```

To run the AI review locally, set `GEMINI_API_KEY` in your environment first:

```bash
export GEMINI_API_KEY=your_key_here
python review_code.py
```

## Tech stack

- **CI/CD:** Azure Pipelines
- **SAST:** Bandit
- **AI review:** Gemini API
- **Testing:** pytest
- **Report generation:** Python (Jinja/HTML templating via `template.html`)

## Known limitations / roadmap

- Bandit currently runs with `|| true`, so the pipeline never fails the build on security findings — it just records them. The plan is to fail the build on any **high-severity** finding while still allowing low/medium findings to pass with a warning (see the updated pipeline in this repo for a starting point on that).
- No containerized deploy step yet, despite the included `Dockerfile` — the pipeline builds and reports but doesn't ship the container anywhere.
- Single demo file (`app.py`) — the seeded-vulnerability approach works well for showing the pipeline mechanics, but a stronger portfolio version would scan a small multi-file service instead of one file.
- No linting stage (flake8/ruff) yet alongside Bandit.

## Architecture

```
push to main
     │
     ▼
┌─────────────┐    ┌───────────┐    ┌────────────────┐    ┌──────────────────┐
│ pytest unit  │ →  │  Bandit   │ →  │  Gemini AI code │ →  │ generate_report  │
│    tests     │    │  (SAST)   │    │     review      │    │  → index.html    │
└─────────────┘    └───────────┘    └────────────────┘    └──────────────────┘
                                                                     │
                                                                     ▼
                                                       Published as pipeline artifact
```
