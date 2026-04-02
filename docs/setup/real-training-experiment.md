# Real Training Experiment

All commands below are written from the repository root.

This flow adds one article-ready experiment on top of the existing Stage 6 local stand. It does not replace the canonical demo path and it does not touch the public Stage 7 path.

## Goal
Run one deterministic WDBC experiment with:
- the real dataset at `data/external/wdbc/wdbc.csv`
- the distributed runtime (`2` trainers + `1` evaluator)
- one fair single-process baseline on the same split
- JSON summaries plus comparison plots under `artifacts/experiments/real-training/`

## Prerequisites
- `make bootstrap-dev`
- a fresh local stand for the distributed run:

```bash
make demo-clean
make demo-up
make demo-init
```

The distributed experiment assumes job `1` is already in `scheduling` and has no existing rounds yet.

## 1. Prepare deterministic manifests
```bash
make experiment-prepare-data
```

This writes:
- `data/processed/wdbc/processed.json`
- `data/processed/wdbc/train.json`
- `data/processed/wdbc/eval.json`
- `data/processed/wdbc/partition-trainer-1.json`
- `data/processed/wdbc/partition-trainer-2.json`

Defaults:
- split seed: `20260402`
- train/eval split: `80/20`
- label mapping: `M -> 1`, `B -> 0`
- shared feature scaling derived from the train split

## 2. Run the distributed experiment
```bash
make experiment-run-distributed
```

This starts a protocol run with `fedavg_like_wdbc_v1`, waits for both trainer tasks, reconciles aggregation/evaluation, and writes:
- `artifacts/experiments/real-training/distributed-summary.json`
- `tmp/experiment-state/current-run.json`

## 3. Run the baseline
```bash
make experiment-run-baseline
```

This reuses the same model family, train/eval split, optimizer settings, and feature scales, then writes:
- `artifacts/experiments/real-training/baseline-summary.json`
- `artifacts/experiments/real-training/baseline-model.json`
- `artifacts/experiments/real-training/baseline-trainer-report.json`
- `artifacts/experiments/real-training/baseline-evaluation-report.json`

## 4. Build the comparison report
```bash
make experiment-report
```

This writes:
- `artifacts/experiments/real-training/comparison.json`
- `artifacts/experiments/real-training/runtime_comparison.png`
- `artifacts/experiments/real-training/accuracy_comparison.png`
- `artifacts/experiments/real-training/trainer_loss_comparison.png`
- `artifacts/experiments/real-training/report.md`

## Notes
- `fedavg_like_v1` remains the canonical Stage 6 demo protocol with embedded demo samples.
- `fedavg_like_wdbc_v1` is an experiment-only protocol that reads prepared manifests from `data/processed/wdbc/`.
- If `make experiment-run-distributed` says the job already has rounds, reset the stand and re-run `make demo-init`.
