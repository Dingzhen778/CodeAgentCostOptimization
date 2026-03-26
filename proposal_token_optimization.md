# Proposal: Token Cost Optimization For SWE-bench Code Agents

## 1. Problem Statement

Modern code agents can solve increasingly difficult SWE-bench tasks, but their inference cost grows rapidly with multi-step repository exploration. In practice, the main cost is often not the final code edit itself, but the repeated search, file reading, and context accumulation needed before the edit is produced.

This project studies how to reduce token usage for SWE-bench-style code agents while preserving patch-generation ability and resolve rate.

The current execution framework is already in place:

- `mini-swe-agent` is used as the core agent
- official `SWE-bench Verified` Docker images can run locally
- token usage is tracked through a gateway layer
- `trajectory.json`, `result.json`, and `patch.diff` are produced for each instance

This means the project is already beyond framework setup and can now focus on cost-optimization methods.

## 2. Motivation

The key motivation is that code-agent cost does not come from a single prompt. Instead, it accumulates over a long trajectory:

- the agent searches for relevant files
- the agent reads multiple files or file fragments
- the outputs of these reads are carried forward into later turns
- the agent may re-read similar content or enter low-yield loops

Therefore, optimizing only the final edit step is unlikely to yield large savings. The optimization target should be the code-understanding stage and the historical context it creates.

## 3. Current Empirical Findings

We performed a first-pass token phase analysis over real trajectories and grouped agent work into:

- `bootstrap`
- `search`
- `read`
- `edit`
- `verify`
- `submit`
- `other`

These were further aggregated into:

- `understand = bootstrap + search + read`
- `implement = edit`
- `validate = verify + submit`
- `other = other`

The current summary artifacts are:

- [experiments/verified_model_sweep_150/token_phase_summary.csv](/home/azureuser/jrh/CodeAgentCostOptimization/experiments/verified_model_sweep_150/token_phase_summary.csv)
- [experiments/verified_model_sweep_150/token_phase_summary.json](/home/azureuser/jrh/CodeAgentCostOptimization/experiments/verified_model_sweep_150/token_phase_summary.json)
- [experiments/verified_model_sweep_150/token_phase_findings.md](/home/azureuser/jrh/CodeAgentCostOptimization/experiments/verified_model_sweep_150/token_phase_findings.md)

### 3.1 Phase Distribution By Model

#### DPSK

- `understand`: `61.31%`
- `read`: `43.77%`
- `search`: `17.51%`
- `implement`: `6.24%`
- `validate`: `1.46%`
- `other`: `31.00%`

#### GLM

- `understand`: `80.89%`
- `read`: `64.90%`
- `search`: `15.99%`
- `implement`: `0.94%`
- `validate`: `5.32%`
- `other`: `12.85%`

#### MINIMAX

- `understand`: `53.97%`
- `read`: `43.87%`
- `search`: `10.09%`
- `implement`: `1.21%`
- `validate`: `16.25%`
- `other`: `28.57%`

### 3.2 Main Observations

1. Across all three models, the dominant token cost lies in the `understand` stage rather than the `implement` stage.
2. `read` is the largest single token-consuming phase for every model.
3. `GLM` is especially dominated by file-reading cost.
4. `MINIMAX` succeeds more often when it transitions earlier into `verify` and `submit`.
5. Failed runs tend to spend more budget in `other`-type loops and prolonged reading/searching behavior.

These findings imply that the most promising optimization target is not edit-time compression, but context reduction for repository understanding.

## 4. Research Question

The main research question is:

How can we reduce token cost for SWE-bench code agents by shrinking repository-understanding context and historical interaction context, while preserving patch quality and resolve rate?

This can be divided into three subquestions:

1. Can retrieval-based narrowing reduce unnecessary `search + read` cost?
2. Can observation/history compression reduce later-step context accumulation?
3. Can loop-aware control reduce long-tail failure cost?

## 5. Baselines

### Baseline 0: Raw Mini-SWE-Agent

This is the direct baseline:

- official issue statement
- official Docker image
- no semantic compression
- no retrieval narrowing
- standard `mini-swe-agent` patch submission flow

This baseline reflects the original cost-quality tradeoff of the agent.

### Baseline 1: Budget-Control Only

This is a control baseline with no semantic retrieval or learned compression:

- limit file read length
- limit repeated reads
- cap old observation length
- optionally apply simple truncation or windowing

This baseline is important because it distinguishes true semantic optimization from brute-force clipping.

## 6. Proposed Methods

## 6.1 Method A: Retrieval-Guided Context Narrowing

### Core Idea

Before the agent starts free exploration, use the issue text to retrieve a small candidate set of relevant files and snippets.

Instead of letting the agent search the whole repository from scratch, provide:

- top-k candidate file paths
- optionally top-k relevant snippets per file
- optionally matched symbols, function names, or retrieval scores

### Why It Fits The Current Evidence

The current token profile shows that:

- `search + read` is the dominant cost center
- `read` alone is the largest cost component

Therefore, narrowing what the agent reads is the most direct way to attack the largest token sink.

### Expected Benefit

- lower `search` cost
- lower `read` cost
- fewer irrelevant observations entering later context
- lower total token usage without directly compressing crucial source content

### Variants

- `A1`: top-k file paths only
- `A2`: top-k file paths + relevant snippets
- `A3`: top-k file paths + snippets + brief retrieval rationale

The most practical first implementation is `A2`.

## 6.2 Method B: Observation / History Compression

### Core Idea

Do not compress the issue statement or the currently focused code fragment. Instead, compress older observations produced by earlier `search` and `read` steps.

This targets the fact that long read outputs are repeatedly carried into future turns.

### Why It Fits The Current Evidence

Even when retrieval is improved, the agent still accumulates large historical context across many steps. This method specifically targets that second source of cost.

### Candidate Implementations

- extractive summarization of older observations
- structured summaries of file contents
- LLMLingua-style prompt compression for stale history only
- rolling memory that preserves recent raw context and summarizes older context

### Expected Benefit

- lower prompt growth over time
- smaller late-stage context windows
- lower cost for long trajectories

## 6.3 Method C: Loop-Aware Context Control

### Core Idea

Detect repetitive low-yield behavior and trigger intervention:

- repeated reading of the same file
- repeated search with low novelty
- repeated `other`-type turns without entering verification

Possible responses:

- summarize and replace old observations
- force narrower candidate focus
- trigger an early stop or fallback mode

### Why It Fits The Current Evidence

Failed runs frequently spend a large portion of budget in `other` and prolonged non-submitting behavior. This suggests a need for trajectory-aware cost control, especially on long-tail failures.

### Role In The Proposal

This method is better framed as an auxiliary control mechanism than as the sole core method.

## 7. Recommended Priority

Based on the current token distribution, the recommended order is:

1. `Retrieval-Guided Context Narrowing`
2. `Observation / History Compression`
3. `Loop-Aware Context Control`

Not recommended as first priority:

- edit-stage compression
- prompt-only compression on the initial issue
- step-limit tuning as the main contribution

These do not directly target the dominant cost centers identified by the current token analysis.

## 8. Experimental Plan

### 8.1 Minimal Experimental Matrix

- `B0`: Raw baseline
- `B1`: Budget-control baseline
- `M1`: Retrieval-guided narrowing
- `M2`: Retrieval-guided narrowing + observation compression
- `M3`: Retrieval-guided narrowing + observation compression + loop-aware control

### 8.2 Evaluation Metrics

- `resolve rate`
- `avg total tokens`
- `avg input tokens`
- `avg output tokens`
- `runtime`
- `tokens per resolved instance`
- `understand-stage token reduction`
- `read-stage token reduction`

### 8.3 Additional Analysis

- success vs failure phase-distribution comparison
- token reduction by phase
- model-specific gains across DPSK / GLM / MINIMAX
- impact on long-tail failed trajectories

## 9. Expected Contribution

This proposal aims to contribute:

1. A trajectory-grounded diagnosis of where token cost is actually spent in SWE-bench code agents
2. A retrieval-first cost-reduction strategy aligned with the measured cost structure
3. A combined framework for narrowing repository context and compressing accumulated observations
4. A cleaner cost-performance tradeoff for code-agent patch generation

## 10. Current Recommendation

The next implementation step should not be generic full-context compression.

Instead, the first concrete method to build and test should be:

`Retrieval-Guided Context Narrowing`

with the following design goal:

- reduce what the agent reads
- reduce what gets carried forward from early repository exploration
- preserve the original issue statement and local code-edit fidelity

After that, `Observation / History Compression` should be layered on top.

## 11. Next Step For Literature And Design Review

Before implementation, the next survey phase should focus on:

- repository-level retrieval for bug fixing
- snippet selection for code agents
- prompt compression methods that preserve code semantics
- memory compression for multi-step agents
- loop detection or trajectory control in agentic systems

This literature review will determine which concrete retrieval and compression mechanism is the most defensible implementation choice for the proposal.
