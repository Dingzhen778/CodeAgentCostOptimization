# Transferable Skills For Mini-SWE-Agent

These skills are reusable heuristics distilled from previously resolved SWE-bench runs.
They are not instance-specific ground truth. Use them only to reduce search cost and
avoid low-value trajectories.

## Core Workflow

1. Start with the issue text and identify 2-5 likely nouns, function names, classes, or modules.
2. Use `rg` to narrow candidate files before any large file reads.
3. Once you have 1-3 plausible files, stop broad search and switch to local inspection.
4. Prefer focused snippets around matching symbols, error strings, or test names.
5. Make the smallest patch that changes behavior only at the suspected fault site.
6. Run the narrowest possible verification first, then submit once behavior is confirmed.

## Search Heuristics

- Search for exact error messages, API names, option names, and test names from the issue.
- If the issue describes argument validation, start near the public API entrypoint and trace one level inward.
- If the issue describes ORM/query, dispatch, parsing, or normalization behavior, prioritize files whose names match those subsystems.
- If tests are named in the issue metadata, inspect the nearest test module to infer target code paths.

## Read Heuristics

- Avoid whole-file dumps unless the file is short.
- Read the function containing the suspected behavior first, then one caller and one callee if needed.
- Do not re-read the same file unless you are checking a different symbol or validating an edit.
- When multiple files look similar, prefer the one referenced by tests or public API imports.

## Edit Heuristics

- Prefer minimal conditional changes, validation guards, or return-path fixes over broad refactors.
- Preserve existing style and error semantics unless the issue explicitly asks for new behavior.
- If the problem is dispatch or operator fallback, check whether `NotImplemented` is more appropriate than raising early.
- If the problem is validation, ensure symmetric handling across equivalent input forms.

## Verification Heuristics

- Reproduce with the smallest command possible before editing if reproduction is cheap.
- After editing, run the narrowest targeted check that can falsify the fix quickly.
- If a targeted check passes, avoid broad test suites unless necessary for confidence.

## Submission Heuristics

- Before submission, inspect `git diff -- path/to/file`.
- Submit only after the patch is minimal and verification evidence exists.
