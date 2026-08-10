# Vendored: no-ai-slop

Source: https://github.com/petergyang/no-ai-slop (MIT License)
Vendored: 2026-08-05 (upstream commit D30eddb9)

Files taken verbatim: `SKILL.md`, `eval.md`, `LICENSE`. The upstream repo also
ships `agents/` and `scripts/` (plugin machinery), not needed here.

## Why this is here

`ai-consultant-career` runs this skill's post-generation check on cover
letters, case studies, and LinkedIn About sections: employers screen for AI
writing patterns, so application copy must pass `eval.md` before it goes out.
The pointer in `ai-consultant-career/SKILL.md` (Writing Hygiene,
post-generation check) resolves to this folder.

To refresh: pull the same three files from upstream and commit.
