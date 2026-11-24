# Contributing

How we, the group, work on this repo. AI agents read `AGENTS.md`; its rules on where code goes, tests and data apply to you too, so read it once.

## Set up

Install [uv](https://docs.astral.sh/uv/) for Python, and Node 22 with [pnpm](https://pnpm.io/) for the site. The commands to run the tests, the scrapers and the site are in the README's "Run it" section.

Make your commits under your own GitHub account: set `git config user.name` and `user.email` to match it. The brief asks that every member writes code, and the git history is how we show it.

## Pick something to work on

Work comes from the repo's GitHub Issues. Assign yourself before you start, so two people don't build the same thing. `ready-for-human` issues are for us; `ready-for-agent` ones are specified well enough to hand to an AI agent.

## Make the change

1. Start a branch off an up-to-date `main`: `git switch main && git pull && git switch -c <your-name>/<topic>`, e.g. `may/stamp-duty-2026`.
2. Write the code and its `assert` tests (see "Tests" in `AGENTS.md`). Work out each expected number by hand and put the working in a comment.
3. Run `uv run pytest` and see it pass.
4. Stage only the files you meant to change (`git add <file>…`). A local scraper run rewrites `data/`; leave those changes out, since the daily job owns that folder.
5. Write each commit message as one plain sentence saying what changes, like the ones already in `git log`: "Use Centaline's asking prices when Midland refuses us".

## Using AI tools

Copilot, Claude, ChatGPT and the like are fine to use. Copilot in VS Code and Claude Code read `AGENTS.md` by themselves; with other tools, paste the relevant part in.

Whoever opens the PR owns every line in it. The brief says each of us must be able to explain any line of the code, so before you open the PR, read what the AI wrote until you could explain it to the class. Where you can't, make it simpler or ask about it in the PR.

## Open a pull request

Push your branch and open a PR into `main` (`gh pr create`, or on GitHub). The description says:

- what changed, and which issue it closes (`Closes #12`);
- how you checked it is right: which test, which hand calculation, or which past data;
- what it still cannot tell you, if anything.

Another member reviews it, and merges once they could explain it too. Tests run on GitHub only after a merge to `main` (in the deploy job), so the `uv run pytest` you ran is the check before that.
