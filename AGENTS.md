# Codex Collaboration Rules

These instructions apply to the entire repository.

## Authoritative State

- Read `CONTEXT.md`, `STATUS.md`, `plan/research_plan.md`,
  `plan/timeline.md`, `tasks/TODO.md`, and `docs/decisions.md` before
  substantial work.
- Treat Confirmed content as a constraint.
- Treat Candidate content as unconfirmed and do not present it as a fixed
  method or finding.
- Do not invent experimental results or modify raw data.
- Do not skip the current phase gate or start Refiner training before the
  required error-analysis and baseline work is complete.

## Progress Tracking

- Update `tasks/TODO.md` whenever a listed task is completed.
- Update `STATUS.md` when the project stage, active work, blockers, findings,
  or immediate next steps materially change.
- Record only durable research decisions in `docs/decisions.md`; do not use it
  as an experiment log.
- Report results and candidate responses before changing the research plan.
- Keep scripts and analyses reproducible and preserve raw, normalized, and
  per-sample artifacts separately.

## Git Synchronization

- After completing and verifying each coherent task, inspect `git diff` and
  `git status`, create a descriptive commit, and push it to `origin/main` in
  the same Codex task.
- Do not commit incomplete work merely to show activity. For long work, commit
  only independently useful and internally consistent milestones.
- Never commit secrets, private keys, credentials, local environments, caches,
  large generated artifacts, or unrelated user changes.
- Do not rewrite published history or force-push unless the user explicitly
  requests it.
- If a push is blocked, preserve the local commit and report the exact blocker.

## Commit Messages

- Use concise imperative subjects that describe the completed result.
- Group documentation, implementation, tests, and generated outputs only when
  they form one coherent milestone.
