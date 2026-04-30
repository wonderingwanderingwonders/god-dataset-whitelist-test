#!/usr/bin/env python3
"""
Dataset whitelist end-to-end verification script.

Runs inside the training container to verify that miner-requested datasets
were downloaded and mounted correctly. Accepts standard trainer CLI args
(task-id, model, etc.) so the trainer doesn't error, but only cares about
the MINER_DATASETS_DIR and MINER_DATASETS environment variables.

Exit codes:
    0 - All requested datasets found and verified
    1 - Verification failed (missing env vars, missing files, etc.)
"""

import argparse
import json
import os
import sys
from pathlib import Path


SEPARATOR = "=" * 60


def parse_args() -> argparse.Namespace:
    """Accept standard trainer CLI args without requiring them."""
    parser = argparse.ArgumentParser(description="Dataset whitelist verification")
    parser.add_argument("--task-id", default="test")
    parser.add_argument("--model", default="test")
    parser.add_argument("--dataset", default="")
    parser.add_argument("--dataset-type", default="{}")
    parser.add_argument("--task-type", default="EnvTask")
    parser.add_argument("--expected-repo-name", default="test")
    parser.add_argument("--hours-to-complete", default="1", type=str)
    parser.add_argument("--file-format", default="")
    return parser.parse_args()


def verify_env_vars() -> tuple[str | None, list[str]]:
    """Check that MINER_DATASETS_DIR and MINER_DATASETS are set."""
    datasets_dir = os.environ.get("MINER_DATASETS_DIR")
    datasets_csv = os.environ.get("MINER_DATASETS", "")

    print(f"MINER_DATASETS_DIR = {datasets_dir!r}")
    print(f"MINER_DATASETS     = {datasets_csv!r}")
    print()

    if not datasets_dir:
        print("FAIL: MINER_DATASETS_DIR is not set")
        return None, []

    if not datasets_csv:
        print("FAIL: MINER_DATASETS is not set or empty")
        return datasets_dir, []

    dataset_list = [ds.strip() for ds in datasets_csv.split(",") if ds.strip()]
    print(f"Parsed {len(dataset_list)} dataset(s): {dataset_list}")
    return datasets_dir, dataset_list


def verify_dataset_files(datasets_dir: str, dataset_list: list[str]) -> bool:
    """Verify each dataset directory exists and contains files."""
    all_ok = True
    results = []

    for dataset_name in dataset_list:
        dir_name = dataset_name.replace("/", "--")
        dataset_path = Path(datasets_dir) / dir_name
        print(f"\n--- Checking: {dataset_name} ---")
        print(f"  Dir name: {dir_name}")
        print(f"  Path: {dataset_path}")

        if not dataset_path.exists():
            print(f"  FAIL: Directory does not exist")
            results.append({"dataset": dataset_name, "status": "MISSING", "path": str(dataset_path)})
            all_ok = False
            continue

        if not dataset_path.is_dir():
            print(f"  FAIL: Path exists but is not a directory")
            results.append({"dataset": dataset_name, "status": "NOT_A_DIR", "path": str(dataset_path)})
            all_ok = False
            continue

        files = list(dataset_path.rglob("*"))
        file_count = sum(1 for f in files if f.is_file())
        dir_count = sum(1 for f in files if f.is_dir())

        print(f"  OK: Found {file_count} file(s) in {dir_count + 1} director(ies)")

        top_level = sorted([f.name for f in dataset_path.iterdir()])[:20]
        print(f"  Contents (top-level): {top_level}")

        total_size = sum(f.stat().st_size for f in files if f.is_file())
        size_mb = total_size / (1024 * 1024)
        print(f"  Total size: {size_mb:.2f} MB")

        results.append({
            "dataset": dataset_name,
            "status": "OK",
            "path": str(dataset_path),
            "file_count": file_count,
            "size_mb": round(size_mb, 2),
        })

    print(f"\n{SEPARATOR}")
    print("VERIFICATION RESULTS:")
    print(json.dumps(results, indent=2))
    return all_ok


def verify_cache_mount() -> None:
    """Show what's at /cache for debugging."""
    cache = Path("/cache")
    print(f"\n{SEPARATOR}")
    print(f"/cache exists: {cache.exists()}")
    if cache.exists():
        top_level = sorted([f.name for f in cache.iterdir()])
        print(f"/cache contents: {top_level}")

        miner_ds = cache / "miner_datasets"
        if miner_ds.exists():
            ds_contents = sorted([f.name for f in miner_ds.iterdir()])
            print(f"/cache/miner_datasets contents: {ds_contents}")
        else:
            print("/cache/miner_datasets does not exist")


def main() -> None:
    args = parse_args()

    print(SEPARATOR)
    print("MINER DATASET WHITELIST - E2E VERIFICATION")
    print(SEPARATOR)
    print(f"Task ID:   {args.task_id}")
    print(f"Task Type: {args.task_type}")
    print(f"Model:     {args.model}")
    print()

    print(SEPARATOR)
    print("STEP 1: Check environment variables")
    print(SEPARATOR)
    datasets_dir, dataset_list = verify_env_vars()

    print(f"\n{SEPARATOR}")
    print("STEP 2: Inspect /cache mount")
    print(SEPARATOR)
    verify_cache_mount()

    if not datasets_dir or not dataset_list:
        print(f"\n{SEPARATOR}")
        print("RESULT: FAIL - No dataset env vars found")
        print(SEPARATOR)
        sys.exit(1)

    print(f"\n{SEPARATOR}")
    print("STEP 3: Verify dataset files")
    print(SEPARATOR)
    all_ok = verify_dataset_files(datasets_dir, dataset_list)

    print(f"\n{SEPARATOR}")
    if all_ok:
        print("RESULT: PASS - All datasets verified successfully")
    else:
        print("RESULT: FAIL - One or more datasets missing or invalid")
    print(SEPARATOR)

    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
