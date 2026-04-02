from __future__ import annotations

import csv
import json
import random
from dataclasses import dataclass
from math import floor
from pathlib import Path

from shared.python.schemas.experiment import PreparedDatasetMetadata

DEFAULT_SPLIT_SEED = 20260402
DEFAULT_TRAIN_RATIO = 0.8
DEFAULT_EPOCHS = 12
DEFAULT_LEARNING_RATE = 0.5
DEFAULT_TRAINER_PARTITIONS = 2
_LABEL_MAPPING = {"B": 0, "M": 1}


class DatasetPreparationError(ValueError):
    pass


@dataclass(slots=True, frozen=True)
class PreparedManifests:
    metadata: PreparedDatasetMetadata
    train_manifest: dict[str, object]
    eval_manifest: dict[str, object]
    trainer_partition_manifests: list[dict[str, object]]



def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]



def prepared_wdbc_dir() -> Path:
    return repo_root() / "data" / "processed" / "wdbc"



def experiments_output_dir() -> Path:
    return repo_root() / "artifacts" / "experiments" / "real-training"



def _source_csv_path() -> Path:
    return repo_root() / "data" / "external" / "wdbc" / "wdbc.csv"



def _load_raw_rows(source_path: Path) -> tuple[list[str], list[dict[str, object]]]:
    if not source_path.exists():
        raise DatasetPreparationError(f"source dataset not found: {source_path}")

    with source_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise DatasetPreparationError("dataset is missing CSV headers")
        headers = list(reader.fieldnames)
        label_column = next((name for name in headers if name.lower() in {"diagnosis", "target"}), None)
        if label_column is None:
            raise DatasetPreparationError("dataset must contain a diagnosis or target column")
        id_column = next((name for name in headers if name.lower() == "id"), None)
        feature_names = [name for name in headers if name not in {label_column, id_column}]
        if not feature_names:
            raise DatasetPreparationError("dataset must contain numeric feature columns")

        rows: list[dict[str, object]] = []
        for raw_index, row in enumerate(reader):
            label_raw = str(row[label_column]).strip().upper()
            if label_raw not in _LABEL_MAPPING:
                raise DatasetPreparationError(f"unexpected label '{label_raw}' at row {raw_index + 2}")
            try:
                features = [float(row[name]) for name in feature_names]
            except ValueError as exc:
                raise DatasetPreparationError(f"non-numeric feature value at row {raw_index + 2}") from exc
            record: dict[str, object] = {
                "row_index": raw_index,
                "label": _LABEL_MAPPING[label_raw],
                "label_name": label_raw,
                "features": features,
            }
            if id_column and row[id_column] != "":
                record["sample_id"] = str(row[id_column]).strip()
            rows.append(record)

    return feature_names, rows



def _allocate_counts(total: int, groups: dict[int, list[dict[str, object]]], target_ratio: float) -> dict[int, int]:
    target_eval_total = total - int(round(total * target_ratio))
    exact = {label: len(rows) * (1 - target_ratio) for label, rows in groups.items()}
    counts = {label: floor(value) for label, value in exact.items()}
    remainder = target_eval_total - sum(counts.values())
    if remainder > 0:
        ranked = sorted(groups, key=lambda label: (exact[label] - counts[label], len(groups[label]), label), reverse=True)
        for label in ranked[:remainder]:
            counts[label] += 1
    return counts



def _stratified_split(rows: list[dict[str, object]], *, train_ratio: float, seed: int) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    grouped: dict[int, list[dict[str, object]]] = {}
    for row in rows:
        grouped.setdefault(int(row["label"]), []).append(row)

    eval_counts = _allocate_counts(len(rows), grouped, train_ratio)
    train_rows: list[dict[str, object]] = []
    eval_rows: list[dict[str, object]] = []
    for label in sorted(grouped):
        rng = random.Random(seed + label)
        items = list(grouped[label])
        rng.shuffle(items)
        eval_count = eval_counts[label]
        eval_rows.extend(items[:eval_count])
        train_rows.extend(items[eval_count:])

    train_rows.sort(key=lambda item: int(item["row_index"]))
    eval_rows.sort(key=lambda item: int(item["row_index"]))
    return train_rows, eval_rows



def _partition_train_rows(rows: list[dict[str, object]], *, partition_count: int, seed: int) -> list[list[dict[str, object]]]:
    grouped: dict[int, list[dict[str, object]]] = {}
    for row in rows:
        grouped.setdefault(int(row["label"]), []).append(row)

    partitions = [[] for _ in range(partition_count)]
    for label in sorted(grouped):
        rng = random.Random(seed + 100 + label)
        items = list(grouped[label])
        rng.shuffle(items)
        for index, item in enumerate(items):
            partitions[index % partition_count].append(item)

    for partition in partitions:
        partition.sort(key=lambda item: int(item["row_index"]))
    return partitions



def _feature_scales(rows: list[dict[str, object]], feature_count: int) -> list[float]:
    scales = [1.0] * feature_count
    for index in range(feature_count):
        max_value = max(abs(float(row["features"][index])) for row in rows)
        scales[index] = max(max_value, 1.0)
    return scales



def _manifest(*, partition_id: str, dataset_name: str, feature_names: list[str], feature_scales: list[float], rows: list[dict[str, object]]) -> dict[str, object]:
    samples: list[dict[str, object]] = []
    for row in rows:
        sample = {
            "features": [float(value) for value in row["features"]],
            "label": int(row["label"]),
        }
        if "sample_id" in row:
            sample["sample_id"] = row["sample_id"]
        samples.append(sample)
    return {
        "dataset_name": dataset_name,
        "partition_id": partition_id,
        "feature_names": feature_names,
        "feature_count": len(feature_names),
        "feature_scales": feature_scales,
        "label_mapping": _LABEL_MAPPING,
        "samples": samples,
    }



def build_prepared_wdbc_manifests(
    *,
    source_path: Path | None = None,
    train_ratio: float = DEFAULT_TRAIN_RATIO,
    seed: int = DEFAULT_SPLIT_SEED,
    trainer_partition_count: int = DEFAULT_TRAINER_PARTITIONS,
) -> PreparedManifests:
    source = source_path or _source_csv_path()
    feature_names, rows = _load_raw_rows(source)
    train_rows, eval_rows = _stratified_split(rows, train_ratio=train_ratio, seed=seed)
    feature_scales = _feature_scales(train_rows, len(feature_names))
    partitions = _partition_train_rows(train_rows, partition_count=trainer_partition_count, seed=seed)

    metadata = PreparedDatasetMetadata(
        dataset_name="wdbc",
        source_path=str(source.relative_to(repo_root())),
        source_record_count=len(rows),
        feature_names=feature_names,
        feature_count=len(feature_names),
        label_mapping=_LABEL_MAPPING,
        feature_scales=feature_scales,
        split_seed=seed,
        train_ratio=train_ratio,
        train_count=len(train_rows),
        eval_count=len(eval_rows),
        trainer_partition_count=trainer_partition_count,
    )
    train_manifest = _manifest(
        partition_id="wdbc-train",
        dataset_name=metadata.dataset_name,
        feature_names=feature_names,
        feature_scales=feature_scales,
        rows=train_rows,
    )
    eval_manifest = _manifest(
        partition_id="wdbc-eval",
        dataset_name=metadata.dataset_name,
        feature_names=feature_names,
        feature_scales=feature_scales,
        rows=eval_rows,
    )
    partition_manifests = [
        _manifest(
            partition_id=f"wdbc-trainer-{index + 1}",
            dataset_name=metadata.dataset_name,
            feature_names=feature_names,
            feature_scales=feature_scales,
            rows=partition_rows,
        )
        for index, partition_rows in enumerate(partitions)
    ]
    return PreparedManifests(
        metadata=metadata,
        train_manifest=train_manifest,
        eval_manifest=eval_manifest,
        trainer_partition_manifests=partition_manifests,
    )



def ensure_prepared_wdbc_dataset(output_dir: Path | None = None) -> PreparedManifests:
    manifests = build_prepared_wdbc_manifests()
    target_dir = output_dir or prepared_wdbc_dir()
    target_dir.mkdir(parents=True, exist_ok=True)

    (target_dir / "processed.json").write_text(manifests.metadata.model_dump_json(indent=2), encoding="utf-8")
    (target_dir / "train.json").write_text(json.dumps(manifests.train_manifest, indent=2, sort_keys=True), encoding="utf-8")
    (target_dir / "eval.json").write_text(json.dumps(manifests.eval_manifest, indent=2, sort_keys=True), encoding="utf-8")
    for index, manifest in enumerate(manifests.trainer_partition_manifests, start=1):
        (target_dir / f"partition-trainer-{index}.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True),
            encoding="utf-8",
        )
    return manifests
