# Related-Work Search Plan

Use this plan when the user wants recent literature or citation-ready related work.

## Bucket 1: LLM-based automated program repair

Questions to answer:

- What are the representative LLM-based APR works?
- Which of them use single-pass generation and which use agentic interaction?
- Do they optimize success rate only, or also cost/efficiency?

Suggested queries:

- `LLM automated program repair`
- `large language models program repair repository`
- `agentic program repair SWE-bench`

## Bucket 2: Software engineering agents and code agents

Questions to answer:

- What are representative software engineering agents?
- How do they use tools, repository context, and environment feedback?
- Is cost structure explicitly analyzed?

Suggested queries:

- `software engineering agents large language models`
- `code agent repository repair`
- `SWE-agent SWE-bench paper`

## Bucket 3: Repository-level retrieval and codebase context

Questions to answer:

- How do prior methods retrieve relevant repository context?
- What granularity is used: file, function, chunk, graph, or hybrid?
- Are these methods designed for completion, repair, or general code tasks?

Suggested queries:

- `repository-level code retrieval large language models`
- `repo-level code completion retrieval`
- `codebase context retrieval software engineering`

## Bucket 4: Long-context compression in code tasks

Questions to answer:

- What compression methods exist for long-context code tasks?
- Are they code-aware or generic-text methods adapted to code?
- Do they report trade-offs between compression and task quality?

Suggested queries:

- `long context compression code large language models`
- `context compression code generation`
- `LLMLingua code repository context`

## Bucket 5: Cost and efficiency optimization

Questions to answer:

- Are there papers on token efficiency, budgeted inference, or agent-cost optimization?
- Do any works analyze stage-level or trajectory-level agent cost?
- How is trade-off with success rate discussed?

Suggested queries:

- `token efficiency LLM agents`
- `cost optimization software engineering agents`
- `inference cost code agents`
- `trajectory cost analysis LLM agents`

## Expected output format after search

For each bucket, collect:

- 3 to 8 representative papers or systems
- one-sentence problem statement
- one-sentence method summary
- one-sentence relevance to this thesis
- whether the work studies accuracy only, or also efficiency/cost
