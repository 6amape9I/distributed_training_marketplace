# Extra Plan: Real Dataset Experiment and Baseline

This document defines an additional implementation task on top of the current MVP.

The purpose of this task is not to redesign the marketplace.
The purpose is to produce one honest, reproducible, article-ready experiment showing that the current MVP can train a real model on a real dataset across multiple trainer nodes and compare that result to a non-distributed baseline.

## Objective

Add a reproducible real-dataset experiment pack for the MVP.

The experiment must:

- use a real tabular binary-classification dataset checked into the repository;
- run the existing distributed off-chain training flow with at least 2 trainer nodes and 1 evaluator;
- produce real runtime and quality metrics;
- produce a comparable single-process baseline run on the same dataset split;
- save outputs in a form suitable for a short article or report.

## Selected dataset

Canonical dataset:
- `Breast Cancer Wisconsin Diagnostic (WDBC)`

Repository input location:
- `data/external/wdbc/wdbc.csv`

Expected dataset shape:
- one CSV file with headers;
- one binary target column (`diagnosis` or `target`);
- optional `id` column;
- numeric feature columns.

This task should not require network download at runtime.
The dataset must be read from the repository working tree.

---

## Why this task exists

The current MVP already proves the architecture and a demo training flow.
However, the current protocol plugin still uses embedded demo samples and an embedded evaluation sample set.
That is enough for internal MVP validation, but not strong enough as the main experimental result for an article.

This extra task must produce:

- one real distributed training run;
- one fair baseline run;
- one compact experimental artifact set:
  - metrics
  - timings
  - plots
  - summary tables

---

## Guardrails

- Do not redesign the Stage 1 smart-contract model.
- Do not turn this task into Stage 8+ research work.
- Do not widen the task into malicious-node defense, trustless verification, or reputation.
- Do not make Sepolia/public-chain setup a dependency for the experiment.
- Keep all training and evaluation off-chain.
- Reuse the current trainer/evaluator logic as much as possible.
- Prefer one clean reproducible experiment over a broad but fragile benchmark suite.
- Baseline and distributed runs must be comparable.

---

## Boundaries

### This task includes

- reading a real CSV dataset from the repository;
- deterministic preprocessing for the current logistic-style trainer/evaluator flow;
- deterministic train/eval split;
- deterministic trainer partition generation for distributed training;
- one distributed experiment path using the current orchestrator + trainers + evaluator;
- one non-distributed baseline path using the same model family and the same data split;
- timing measurement;
- metric collection;
- article-ready output artifacts;
- experiment documentation.

### This task explicitly does NOT include

- public testnet integration;
- UI/dashboard work;
- large-model support;
- GPU optimization work;
- hyperparameter search;
- many-dataset benchmark suites;
- protocol redesign;
- Byzantine robustness;
- tokenomics or settlement redesign.

---

## Target result

At the end of this task, the repository must provide a single reproducible experiment in which a developer can:

1. prepare the real dataset from `data/external/wdbc/wdbc.csv`;
2. materialize deterministic train/eval splits and trainer partitions;
3. run the distributed training path with 2 trainer nodes and 1 evaluator;
4. run a single-process baseline on the same train/eval split;
5. collect runtime, loss, and accuracy metrics for both paths;
6. generate a compact comparison summary and at least 2 simple plots;
7. use those outputs directly in a short article.

---

## Tracks

### Track 1. Real dataset ingestion and canonical preprocessing

Add a canonical ingestion path for the WDBC CSV.

Tasks:
- read `data/external/wdbc/wdbc.csv`;
- detect the target column:
  - `diagnosis` with `M/B`, or
  - `target` with `0/1`;
- ignore optional `id` column if present;
- validate that all selected feature columns are numeric;
- convert labels to `0/1`;
- write a canonical processed artifact used by the experiment.

Requirements:
- preprocessing must be deterministic;
- no runtime network download is allowed;
- the code must fail clearly on malformed CSV shape.

Recommended output:
- `data/processed/wdbc/processed.json` or `processed.csv`

Deliverables:
- dataset loader / parser;
- validation errors;
- canonical processed dataset artifact.

Done when:
- the repository can transform the checked-in raw CSV into one canonical processed representation.

---

### Track 2. Deterministic split and partition generation

Create one canonical split for the experiment.

Tasks:
- define deterministic train/eval split logic;
- define deterministic partitioning of the training split across 2 trainer nodes;
- persist the resulting manifests/artifacts;
- ensure the eval split is never used for local trainer updates.

Requirements:
- the same input CSV must produce the same split and partitions every time;
- trainer partitions must be distinct;
- the experiment must remain reproducible.

Recommended outputs:
- `data/processed/wdbc/train.json`
- `data/processed/wdbc/eval.json`
- `data/processed/wdbc/partition-trainer-1.json`
- `data/processed/wdbc/partition-trainer-2.json`
- optional metadata file describing feature count and split sizes

Deliverables:
- split generator;
- partition generator;
- split metadata.

Done when:
- the dataset is reproducibly converted into one train split, one eval split, and trainer-specific partitions.

---

### Track 3. Real-data protocol path for distributed training

Add one canonical distributed experiment path using the existing architecture.

Tasks:
- keep the current demo protocol intact;
- add a real-data experiment path that uses processed dataset artifacts rather than embedded sample lists;
- ensure trainer tasks point to real trainer partition artifacts;
- ensure evaluator task points to the real eval artifact;
- keep the same model family currently used by the trainer/evaluator logic.

Requirements:
- the experiment must use at least 2 trainer nodes and 1 evaluator;
- the final off-chain state must still reach `ready_for_attestation` or `evaluation_failed`;
- the implementation must not break the existing Stage 6 demo path.

Recommended implementation bias:
- reuse the current logistic-style training/evaluation behavior;
- add a separate experiment mode / experiment helper flow rather than replacing the demo path.

Deliverables:
- real-data experiment orchestration path;
- experiment-specific manifests/artifacts;
- docs for starting the distributed experiment.

Done when:
- the orchestrator can run one full distributed experiment from the real dataset artifacts.

---

### Track 4. Single-process baseline implementation

Add one baseline path for fair comparison.

This baseline is required.
The article should not show only the distributed run.

Tasks:
- implement a single-process training path on the same train split;
- use the same model family as the distributed path;
- evaluate on the same eval split;
- record runtime and evaluation metrics.

Requirements:
- baseline and distributed runs must use the same dataset split;
- baseline and distributed runs must use the same feature set;
- baseline and distributed runs should be as comparable as possible in optimization logic.

Strong recommendation:
- reuse the same training math or a shared training core, rather than introducing a completely different model stack.

Deliverables:
- baseline runner script or module;
- baseline metrics artifact;
- baseline timing artifact.

Done when:
- the repository can run one non-distributed baseline and produce metrics on the same eval split.

---

### Track 5. Timing and metric capture

The experiment must be article-ready, not just operational.

Tasks:
- record wall-clock runtime for:
  - distributed full run
  - each trainer local fit
  - evaluator step
  - baseline run
- record quality metrics:
  - trainer average loss
  - trainer local accuracy
  - final eval accuracy
  - final eval average loss
  - baseline eval accuracy
  - baseline eval average loss
- persist metrics in machine-readable form.

Recommended outputs:
- `artifacts/experiments/real-training/distributed-summary.json`
- `artifacts/experiments/real-training/baseline-summary.json`
- `artifacts/experiments/real-training/comparison.json`

Deliverables:
- timing capture;
- metrics capture;
- summary JSON outputs.

Done when:
- the experiment produces stable timing and metric outputs without manual scraping from logs.

---

### Track 6. Article-ready plots and tables

Generate at least minimal visual outputs.

Required visuals:
- one chart comparing trainer local loss and baseline/distributed eval loss;
- one chart or table comparing runtime between distributed and baseline runs.

Recommended visual set:
- `trainer_loss_comparison.png`
- `runtime_comparison.png`
- optional `metrics_table.csv` or `summary_table.md`

Requirements:
- plots must be generated from saved experiment outputs;
- visuals must be simple and reproducible;
- avoid over-design.

Deliverables:
- at least 2 plot files;
- one compact tabular summary.

Done when:
- the repository produces outputs that can be inserted directly into a short report.

---

### Track 7. CLI / helper commands

Expose one simple experiment path.

Recommended helper commands:
- `make experiment-prepare-data`
- `make experiment-run-distributed`
- `make experiment-run-baseline`
- `make experiment-report`

Tasks:
- add readable helper scripts or Make targets;
- keep the canonical path short;
- document expected outputs.

Deliverables:
- canonical experiment command sequence.

Done when:
- another developer can run the experiment from documented commands alone.

---

### Track 8. Documentation

Add one short experiment runbook.

Recommended docs:
- `docs/setup/real-training-experiment.md`
- update `README.md`
- commit this file as `docs/mvp/extra-plan.md`

The runbook should include:
- dataset prerequisite
- preprocessing step
- distributed run
- baseline run
- generated outputs
- where to find plots/JSON summaries

Deliverables:
- one article-oriented runbook.

Done when:
- another developer can reproduce the experiment without consulting chat history.

---

### Track 9. Tests

Add focused tests for the new experiment functionality.

Required test areas:
- dataset parsing and label conversion;
- deterministic split generation;
- partition generation;
- baseline runner output shape;
- comparison summary generation.

This task does not require a huge integration suite.
It does require enough tests to trust the experiment pipeline.

Deliverables:
- focused pytest coverage for preprocessing and experiment output generation.

Done when:
- the experiment pipeline is not validated only by ad hoc manual runs.

---

## File and module expectations

This task is expected to create or significantly expand files in these areas.

### Data
- `data/external/wdbc/wdbc.csv`
- `data/external/wdbc/README.md`
- `data/processed/wdbc/*`

### Orchestrator / experiment code
- experiment helper modules under orchestrator and/or shared utilities
- optional experiment runner scripts under `infra/scripts/`

### Shared
- shared dataset parsing / experiment summary helpers if appropriate

### Docs
- `docs/mvp/extra-plan.md`
- `docs/codex/AGENTS-EXTRA-REAL-TRAINING-ADDENDUM.md`
- `docs/setup/real-training-experiment.md`
- README updates

---

## Recommended order of implementation

1. add raw dataset and parser;
2. add deterministic processed split/partition generation;
3. add distributed real-data experiment path;
4. add single-process baseline path;
5. add timing/metric capture;
6. add plots and summary outputs;
7. add helper commands;
8. add tests;
9. update docs.

Do not start redesigning protocol internals before the experiment path works.

---

## Explicit non-goals

Do NOT implement in this task:
- public Sepolia dependency;
- malicious-node research;
- contribution scoring;
- advanced FL algorithms;
- many-dataset benchmarking;
- UI;
- protocol redesign.

This is an experiment-pack task, not a new project stage.

---

## Acceptance criteria

This task is complete only if all of the following are true:

1. a real CSV dataset is read from the repository;
2. train/eval splits and trainer partitions are generated deterministically;
3. the distributed path runs with at least 2 trainer nodes and 1 evaluator on the real dataset;
4. the baseline path runs on the same split;
5. runtime and quality metrics are persisted for both paths;
6. at least 2 article-ready visuals are generated;
7. the experiment is documented and reproducible;
8. the existing Stage 6 demo path still works;
9. the implementation does not depend on Sepolia being configured;
10. the result is strong enough to support a short article about the current MVP.

---

## Completion summary format

When this task is done, update this file with:

## Extra task implementation status
- Dataset ingestion: complete
- Deterministic split and partition generation: complete
- Distributed real-data experiment path: complete
- Single-process baseline: complete
- Timing and metric capture: complete
- Plots and summary artifacts: complete
- Helper commands: complete
- Tests: complete
- Documentation: complete

## Delivered behavior
This extra task delivers one reproducible real-dataset experiment for the current MVP. The repository can ingest a checked-in WDBC dataset, produce deterministic train/eval splits and trainer partitions, run the existing distributed training architecture on that real data, run a comparable non-distributed baseline on the same split, and generate article-ready metrics, timings, and simple visuals.