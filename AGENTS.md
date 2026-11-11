# AGENTS.md

## Course requirements

This is an ECON3086 (Python Programming for FinTech) group project. Read `docs/course_requirements/project-brief.md` before making design or stack decisions. The constraints that most shape the code:

- Only Python code earns programming marks; any non-Python code earns none.
- Library usage is 40% of the mark, and harder libraries used correctly score higher.
- Code must be simple and readable, with functions tested using `assert`. Every group member must write code and be able to explain every line.
- The app must show its answer is right (checked by hand or against past data) and say what it cannot tell you.

## Live data sources

Before calling HKMA, Midland, a bank site or any other live source by hand, read `docs/research/api-access-log.md`. It says how to work from the saved snapshot, and logs each source's limits (HKMA blocked us on 2026-11-11).

## Agent skills

### Issue tracker

Issues live in this repo's GitHub Issues (gh CLI). See `docs/agents/issue-tracker.md`.

### Triage labels

Default five-role vocabulary (needs-triage, needs-info, ready-for-agent, ready-for-human, wontfix). See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: one `CONTEXT.md` + `docs/adr/` at the repo root. See `docs/agents/domain.md`.
