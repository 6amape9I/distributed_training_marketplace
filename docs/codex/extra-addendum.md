# AGENTS Extra Real-Training Addendum

## Purpose of this task

This task exists to produce one honest experimental result for the current MVP.

The goal is not to redesign the marketplace.
The goal is not to invent a stronger federated-learning protocol.
The goal is not to make Sepolia a dependency.

The goal is to show that the current MVP can already train a real model on a real dataset across multiple trainer nodes, compare that path to a non-distributed baseline, and generate outputs that are useful in a short article.

---

## What must remain true

1. Do not redesign the Stage 1 contract model.
2. Do not break the Stage 6 demo path.
3. Keep all training and evaluation off-chain.
4. Prefer one clean real-data experiment over a broad benchmark suite.
5. Baseline and distributed runs must remain comparable.
6. The experiment must not depend on Sepolia/public-chain completion.

---

## This task is successful only if

- a real checked-in dataset is used;
- the distributed path runs with multiple trainers and one evaluator;
- a baseline run exists on the same split;
- runtime and quality metrics are captured for both paths;
- the repository produces simple visuals and summary artifacts;
- another developer can reproduce the experiment from docs.

If the result is still only “logs from a demo dataset hidden in code”, this task is not complete.

---

## What not to do

Do not:
- turn this into a many-dataset benchmark project;
- replace the current model with a heavy external ML stack unless absolutely necessary;
- add public-chain dependency to the experiment;
- redesign protocol architecture;
- introduce advanced FL research work;
- add UI;
- bury experiment outputs in logs only.

If implementation drifts into benchmark-framework work or research expansion, it has left the task.

---

## Architecture rules

### 1. The experiment must extend the MVP, not replace it
Use the current orchestrator / trainer / evaluator flow as the primary distributed path.

### 2. Keep the model family comparable
The baseline must not use a fundamentally different learning setup unless there is a documented blocker.
Use the same or nearly identical optimization logic where possible.

### 3. Keep the data path explicit
Do not leave dataset assumptions hidden in code.
Document:
- raw input path,
- processed split path,
- trainer partition path,
- eval path.

### 4. Metrics must be saved, not only printed
A good experiment leaves behind JSON/CSV/PNG artifacts that can be reused in the article.

### 5. Simplicity beats breadth
One small real experiment with clear evidence is better than a large unfinished benchmark matrix.

---

## Preferred implementation bias

When choosing between:
- a smaller but reproducible experiment, and
- a broader but fragile research harness,

choose the smaller reproducible experiment.

Examples:
- better: one WDBC experiment with 2 trainers and 1 evaluator
- worse: four datasets with inconsistent preprocessing

- better: one baseline using the same training core
- worse: a fancy external baseline that is not comparable

- better: two simple plots and one clear summary JSON
- worse: many log files with no clean summary

---

## Required implementation style

- Keep helper scripts readable.
- Keep dataset parsing deterministic.
- Keep split generation deterministic.
- Fail clearly on malformed CSV shape.
- Preserve inspectability:
  - split metadata
  - trainer partitions
  - trainer metrics
  - eval metrics
  - baseline metrics
  - timing summaries
  - generated plots
- Keep output locations predictable.

---

## Required testing focus

Tests should prove:
- dataset parsing works;
- labels are converted correctly;
- split generation is deterministic;
- trainer partitions are distinct and reproducible;
- baseline output has the expected metric structure;
- comparison summary generation works.

Do not rely only on manual demo screenshots.

---

## Required delivery discipline

When committing this work:
- keep data-path changes and experiment-path changes reasonably scoped;
- update docs with the real command flow;
- document any fallback assumptions clearly;
- preserve the existing demo flow instead of overwriting it;
- make article-facing outputs easy to find.

If the experiment introduces a new canonical command sequence, the docs must say so clearly.

---

## Escalation rule

If the task appears to require:
- protocol redesign,
- contract redesign,
- public testnet completion,
- large new external dependencies,
- UI work,
- advanced distributed systems work,

stop and document the blocker before proceeding.

Do not quietly widen the task.

---

## Final reminder

This task is about evidence.

A good result lets someone:
- take a real dataset from the repository,
- run one distributed experiment,
- run one baseline experiment,
- compare runtime and quality,
- and place the resulting table/plots into a short article.

That is enough.