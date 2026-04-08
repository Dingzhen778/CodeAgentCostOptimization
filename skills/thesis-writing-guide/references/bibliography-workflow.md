# Bibliography Workflow

Use this workflow when the thesis draft has missing citation keys, weak references, or outdated bibliography content.

## Goal

Build a reliable bibliography with traceable sources and stable BibTeX entries, especially for:

- rewritten front chapters
- related work
- benchmark and tool references
- model and system references

## Preferred toolchain

Use this order of preference:

1. Zotero Desktop
2. Zotero Connector
3. Better BibTeX for Zotero
4. Crossref Simple Text Query for DOI matching when only rough references exist

## Working rules

- Prefer official paper pages, ACL Anthology, OpenReview, arXiv official pages, ACM/IEEE pages, and official technical reports.
- Do not treat Google Scholar exports as the final source of truth.
- Do not add unverified BibTeX entries directly into `refs.bib` unless the user explicitly wants a draft.
- For company models, avoid vague series-level references when a model-specific technical report or official page is available.
- If a benchmark or dataset does not have a stable paper, it is acceptable to cite the official project page, but mark it as such in the bibliography.
- When a local paper source package is available, its `ref.bib` can be used as a candidate-reference source, but the package's `main.tex` should not be assumed to carry final publication metadata unless the venue/DOI fields are clearly finalized.

## Repair steps

1. Extract citation keys used in the target `.tex` files.
2. Compare them against `overleaf/paper/ref/refs.bib`.
3. For `chap01` and `chap02`, consult `SYSU_documents/reference_candidates_chap01_chap02.md`.
4. Collect candidate papers and official pages.
5. Import them into Zotero or record them in a candidate list for later import.
6. Manually verify author list, title, venue, year, DOI, and URL.
7. Export curated BibTeX with Better BibTeX.
8. Update citation keys in the `.tex` files if generic or unstable names should be replaced.

## Special cautions

### Commercial models

Examples:

- Claude
- DeepSeek

Do not assume a generic citation key like `anthropic2024claude` or `liu2024deepseek` is sufficient. First determine whether the text refers to:

- a model family
- a specific model release
- a system card
- an official announcement

Then cite the most precise available source.

### SWE-bench Verified

If there is no stable formal paper for the exact claim being made:

- cite the official project page or official release page
- avoid inventing a paper-like BibTeX entry

### Local source packages

If the repository contains a source package for a prior paper:

- use its `ref.bib` to accelerate candidate collection for related work
- use its `main.tex` to inspect title variants and task framing
- do not trust placeholder publication metadata from submission templates
- prefer the final published page, DOI page, or clearly finalized camera-ready source for the authoritative BibTeX record

## Outputs to maintain

- `SYSU_documents/reference_candidates_chap01_chap02.md` for candidate-source planning
- `overleaf/paper/ref/refs.bib` for curated final bibliography
