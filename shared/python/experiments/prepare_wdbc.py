from __future__ import annotations

from shared.python.experiments.wdbc import ensure_prepared_wdbc_dataset, prepared_wdbc_dir



def main() -> None:
    manifests = ensure_prepared_wdbc_dataset()
    print(f"prepared dataset written to {prepared_wdbc_dir()}")
    print(f"train_count={manifests.metadata.train_count} eval_count={manifests.metadata.eval_count}")


if __name__ == "__main__":
    main()
