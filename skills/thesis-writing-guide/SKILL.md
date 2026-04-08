---
name: thesis-writing-guide
description: Use when working on this repository's SYSU master's thesis writing. It guides what documents to read first, how to keep thesis content aligned with the current code-agent cost-optimization project, which files to update for outlines versus formal thesis text, and how to avoid leaking experiment results into pre-method chapters.
---

# Thesis Writing Guide

Use this skill whenever the task is to summarize thesis progress, draft thesis sections, rewrite chapter structure, or decide which project documents are the current source of truth.

## Core goal

Keep thesis writing aligned with the current project:

- Topic: code repair agents, context compression, and cost optimization.
- Main setting: `mini-swe-agent` on `SWE-bench`.
- Current risk: the Overleaf thesis body still contains old Web3 template content that does not match the active project.
- Another recurring task is to integrate prior published or submitted papers into the thesis without turning the thesis into a disconnected paper bundle.

## Read order

Read only what is needed, in this order:

1. [SYSU_documents/abstract.md](references/document-map.md) summary entry first.
2. [SYSU_documents/sysu_system.md](references/document-map.md) for topic framing, contributions, and innovation points.
3. [progress.md](references/document-map.md) for current experiment status.
4. [SYSU_documents/thesis_outline_pre_method.md](references/document-map.md) when drafting pre-method chapters.
5. `SYSU_documents/reference_candidates_chap01_chap02.md` when adding or repairing references for the rewritten front chapters.
6. `SYSU_documents/thesis_outline_with_prior_work.md` when the user wants to absorb prior papers into the thesis architecture.
7. `overleaf/paper/data/abstract.tex` only when syncing the thesis abstract.
8. `overleaf/paper/data/chap*.tex` only when editing actual thesis chapters.
9. `papers/ICSE26R2_CodeLongContext/*` only when writing related work or prior foundation.

Do not start from `overleaf/paper/data/chap01.tex` to infer the current project topic. Those files may still reflect old template material.

## Source-of-truth rules

- For thesis topic and positioning, trust `SYSU_documents/abstract.md` and `SYSU_documents/sysu_system.md`.
- For current experiment completion and status wording, trust `progress.md`.
- For formal thesis output, edit files under `overleaf/paper/data/`.
- For reusable planning or drafting artifacts, store them under `SYSU_documents/`.
- Do not overwrite or repurpose `skills.md`; it is runtime input for experiments, not thesis guidance.
- When integrating prior papers, treat them as research assets to absorb into a unified thesis storyline:
  - problem/background assets
  - benchmark/task-setting assets
  - method/motivation assets
  - evaluation/design assets
- Do not default to one-paper-one-chapter unless the user explicitly wants a thesis-by-compilation structure.

## What to write before methods and experiments

Before the methods chapter, write only:

- research background
- problem importance
- technical background
- related work
- problem definition
- research motivation
- overall research framing

Avoid these in pre-method chapters:

- concrete experiment numbers
- method ranking
- claims that one method outperforms another
- finalized empirical conclusions

You may write motivations or hypotheses such as:

- repository-level repair introduces large context overhead
- multi-turn interaction can accumulate redundant observations
- cost deserves separate study beyond repair success rate

## File update policy

When the user asks for an outline:

- update or create Markdown in `SYSU_documents/`
- do not directly rewrite thesis chapters unless asked

When the user asks for formal thesis prose:

- first check whether the target section is abstract, chapter draft, or supporting notes
- if it is formal thesis content, update the corresponding `overleaf/paper/data/*.tex` file
- if the user is still exploring structure, draft in `SYSU_documents/` first

When the user asks for references or missing citations:

- first inspect which citation keys are used in the target `.tex` files
- then consult `SYSU_documents/reference_candidates_chap01_chap02.md` if the task concerns the rewritten front chapters
- prefer collecting candidate sources and a validation workflow before bulk-editing `refs.bib`
- treat `refs.bib` as a curated artifact, not a scratchpad for unverified entries

When syncing structure into Overleaf:

- update chapter titles and section structure before filling long prose
- remove or replace old Web3-specific headings rather than editing them piecemeal
- to push edits to Overleaf, invoke the `overleaf-sync` skill or run:
  `cd overleaf/paper && ols --store-path ../.olauth -n "毕业论文___江润汉" -l`

When the user asks how to use prior papers:

- inspect the prior-paper topic first
- identify whether it contributes background, task framing, benchmark design, method motivation, or reusable prose/figures
- prefer integrating those assets into a single thesis line
- explicitly avoid making the thesis look like an unrelated anthology

## Writing workflow

1. Confirm whether the task is outline, note, or formal thesis text.
2. Read the minimal source-of-truth documents from the read order above.
3. Separate stable framing from unstable experiment progress.
4. Draft pre-method content without embedding results.
5. If related work is needed and current local materials are insufficient, prepare a search plan instead of inventing citations.
6. Only after the user wants formal write-back, update the `.tex` chapter files.
7. Keep chapter prose in normal paragraph form; do not pad apparent length by splitting one sentence across many lines or by using outline-like filler instead of real literature synthesis.

## When to propose online research

Propose online search when the user needs:

- recent related work
- citation-ready literature review
- up-to-date survey of code agents, SWE-bench agents, or context compression papers
- exact references for OpenAI or current commercial agent systems
- missing bibliography entries for new chapter drafts

When proposing search, give:

- topic buckets
- suggested keywords
- what each bucket should answer

## Current repository-specific cautions

- `overleaf/paper/data/abstract.tex` is already aligned with the active thesis topic.
- `overleaf/paper/data/chap01.tex` to `chap07.tex` still largely reflect old Web3 material.
- `progress.md` contains live experiment status and can change; do not hard-code its in-progress numbers into stable thesis framing unless the user explicitly asks for current progress reporting.
- `papers/ICSE26R2_CodeLongContext/abstract.tex` is relevant as prior work on code-context compression and can support related-work or research-foundation sections.
- `papers/ICSE26R2_CodeLongContext/*` also contains benchmark and long-context-task framing that can be reused in background or related-work chapters.
- `OmniGIRL` is best treated as issue-resolution benchmark background rather than the core experimental setting of this thesis unless the user changes scope.
- local source packages for the issue-resolution paper may contain rich `ref.bib` files that are useful for candidate references, but submission-stage `main.tex` metadata can still contain placeholder venue/DOI fields.
- `SYSU_documents/reference_candidates_chap01_chap02.md` stores the current reference-repair plan for the rewritten introduction and background chapters.
- `SYSU_documents/thesis_outline_with_prior_work.md` stores the current plan for integrating prior papers into the thesis architecture.
- commercial-model references such as Claude or DeepSeek may need model-specific replacement rather than generic series-level citation keys.

## Reference files

- For file purposes and when to consult each document, read `references/document-map.md`.
- For chapter-writing boundaries and result leakage avoidance, read `references/writing-rules.md`.
- For related-work search planning, read `references/search-plan.md`.
- For bibliography repair workflow, read `references/bibliography-workflow.md`.
