"""
Milestone 3C1 — Meltome Tm v1 Dataset Materialization
=========================================================
Builds the canonical training table for Neolysis-Tm-v1 from the FLIP
"mixed" meltome split (the only maintainer-recommended split for this task).

Uses only Python standard library (csv, hashlib, json, statistics) — no
pandas/scikit-learn/numpy dependency added for this step.

Target correction (per explicit instruction): uses ONLY the FLIP `target`
column, which corresponds to the standard Meltome melting-point value. Does
NOT fall back to any normalized/human-specific variant. Rows without a valid
target are excluded, not imputed.

Input:  data/raw/mixed_split.csv        (FLIP mixed split, extracted from
                                          splits.zip, commit-pinned download)
Output: data/processed/meltome_tm_v1.csv
        data/processed/meltome_tm_v1_manifest.json

This script does NOT call ESM2, does NOT call the Hugging Face Space, and
does NOT train any model. It only materializes and validates the dataset.
"""
import csv
import hashlib
import json
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_CSV = BASE_DIR / "data" / "raw" / "mixed_split.csv"
RAW_ZIP = BASE_DIR / "data" / "raw" / "meltome_splits.zip"
OUT_CSV = BASE_DIR / "data" / "processed" / "meltome_tm_v1.csv"
OUT_MANIFEST = BASE_DIR / "data" / "processed" / "meltome_tm_v1_manifest.json"

CANONICAL_AMINO_ACIDS = set("ACDEFGHIKLMNPQRSTVWY")
SOURCE_REPOSITORY = "https://github.com/J-SNACKKB/FLIP"
SOURCE_COMMIT_SHA = "62cace8735f5610e2743cf06ce0f944b37fffaa6"
SOURCE_FILE = "splits/meltome/splits.zip -> splits/mixed_split.csv"


def canonical_sequence(raw_sequence: str) -> str:
    """Same canonicalization Neolysis applies elsewhere: uppercase, strip whitespace only."""
    return "".join(raw_sequence.split()).upper()


def sha256_of(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_of_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    raw_rows = 0
    missing_target_rows = 0
    empty_sequence_rows = 0

    # split -> list of (sequence_sha256, canonical_sequence, tm_c, source_row_id)
    per_split_records: dict[str, list[tuple[str, str, float, int]]] = defaultdict(list)

    noncanonical_rows = 0
    noncanonical_residue_counter: Counter = Counter()

    with open(RAW_CSV, "r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        assert reader.fieldnames == ["sequence", "target", "set", "validation"], (
            f"Unexpected columns: {reader.fieldnames}"
        )

        for row_id, row in enumerate(reader):
            raw_rows += 1

            raw_sequence = row["sequence"]
            target_text = row["target"]
            set_label = row["set"].strip().lower()
            is_validation = row["validation"].strip() == "True"

            if not raw_sequence or not raw_sequence.strip():
                empty_sequence_rows += 1
                continue

            # Target correction: only the standard `target` column. No fallback
            # to any normalized/human-specific value — there is no such column
            # in this file anyway, but this check guards the intent explicitly.
            if target_text is None or target_text.strip() == "":
                missing_target_rows += 1
                continue
            try:
                tm_c = float(target_text)
            except ValueError:
                missing_target_rows += 1
                continue

            seq = canonical_sequence(raw_sequence)
            residues = set(seq)
            noncanonical_residues = residues - CANONICAL_AMINO_ACIDS
            if noncanonical_residues:
                noncanonical_rows += 1
                for residue in noncanonical_residues:
                    noncanonical_residue_counter[residue] += seq.count(residue)
                # Excluded from the canonical training table per instructions
                # (exclude noncanonical sequences unless justified otherwise).
                continue

            split_name = "validation" if (set_label == "train" and is_validation) else set_label
            seq_hash = sha256_of(seq)
            per_split_records[split_name].append((seq_hash, seq, tm_c, row_id))

    # ── Duplicate detection (within canonical, valid-target, canonical-residue rows) ──
    all_hashes_flat = [rec[0] for records in per_split_records.values() for rec in records]
    hash_counts = Counter(all_hashes_flat)
    duplicate_hashes = {h for h, count in hash_counts.items() if count > 1}
    duplicate_rows = sum(count - 1 for count in hash_counts.values() if count > 1)

    # ── Cross-split leakage check ──────────────────────────────────────────────
    hash_to_splits: dict[str, set[str]] = defaultdict(set)
    for split_name, records in per_split_records.items():
        for seq_hash, _seq, _tm, _rid in records:
            hash_to_splits[seq_hash].add(split_name)
    leaking_hashes = {h: splits for h, splits in hash_to_splits.items() if len(splits) > 1}

    # ── Deduplicate for the final canonical table: keep first occurrence per hash,
    #    per split-assignment priority test > validation > train (test protected first) ──
    split_priority = {"test": 0, "validation": 1, "train": 2}
    seen_hashes: dict[str, tuple[str, str, float, str, int]] = {}
    for split_name, records in per_split_records.items():
        for seq_hash, seq, tm_c, row_id in records:
            candidate = (seq_hash, seq, tm_c, split_name, row_id)
            if seq_hash not in seen_hashes:
                seen_hashes[seq_hash] = candidate
            else:
                existing = seen_hashes[seq_hash]
                if split_priority[split_name] < split_priority[existing[3]]:
                    seen_hashes[seq_hash] = candidate

    final_rows = sorted(seen_hashes.values(), key=lambda r: r[4])

    # ── Write canonical training table ──────────────────────────────────────────
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_CSV, "w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["sequence", "sequence_sha256", "tm_c", "split", "source_row_id"])
        for seq_hash, seq, tm_c, split_name, row_id in final_rows:
            writer.writerow([seq, seq_hash, tm_c, split_name, row_id])

    # ── Statistics ───────────────────────────────────────────────────────────────
    split_counts = {name: len(records) for name, records in per_split_records.items()}
    unique_seq_per_split = {name: len({r[0] for r in records}) for name, records in per_split_records.items()}

    all_valid_canonical_tms = [rec[2] for records in per_split_records.values() for rec in records]

    manifest = {
        "dataset_name": "meltome_tm_v1",
        "source_repository": SOURCE_REPOSITORY,
        "source_commit_sha": SOURCE_COMMIT_SHA,
        "source_file": SOURCE_FILE,
        "source_zip_sha256": sha256_of_file(RAW_ZIP) if RAW_ZIP.exists() else None,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "measurement_method": "thermal_proteome_profiling",
        "target": "melting_temperature_c",
        "target_source_column": "target",  # FLIP standard column, NOT quantNormMeltingPoint
        "units": "degC",
        "raw_rows": raw_rows,
        "empty_sequence_rows": empty_sequence_rows,
        "missing_target_rows": missing_target_rows,
        "valid_target_rows": raw_rows - empty_sequence_rows - missing_target_rows,
        "excluded_noncanonical_rows": noncanonical_rows,
        "noncanonical_residue_counts": dict(noncanonical_residue_counter),
        "canonical_sequence_rows": sum(split_counts.values()),
        "duplicate_rows_before_dedup": duplicate_rows,
        "cross_split_leaking_hashes_count": len(leaking_hashes),
        "final_deduplicated_rows": len(final_rows),
        "train_rows": split_counts.get("train", 0),
        "validation_rows": split_counts.get("validation", 0),
        "test_rows": split_counts.get("test", 0),
        "unique_sequences_train": unique_seq_per_split.get("train", 0),
        "unique_sequences_validation": unique_seq_per_split.get("validation", 0),
        "unique_sequences_test": unique_seq_per_split.get("test", 0),
        "target_min_c": min(all_valid_canonical_tms) if all_valid_canonical_tms else None,
        "target_max_c": max(all_valid_canonical_tms) if all_valid_canonical_tms else None,
        "target_mean_c": statistics.fmean(all_valid_canonical_tms) if all_valid_canonical_tms else None,
        "target_median_c": statistics.median(all_valid_canonical_tms) if all_valid_canonical_tms else None,
        "target_stdev_c": statistics.stdev(all_valid_canonical_tms) if len(all_valid_canonical_tms) > 1 else None,
        "split_method": "flip_mixed_split_v1 (MMSeqs2 20% identity clustering, 80/20 cluster-level train/test; "
                          "mixed = cluster components for train, cluster representative for test)",
        "license": "AFL-3.0 (FLIP-processed splits); original Meltome Atlas raw data released free-to-use "
                     "without formal written license by manuscript authors (flagged for legal review "
                     "regarding commercial redistribution)",
        "attribution": "Jarzab, A., Kurzawa, N., Hopf, T. et al. Meltome atlas-thermal proteome stability "
                        "across the tree of life. Nat Methods 17, 495-503 (2020).",
    }

    with open(OUT_MANIFEST, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)

    print(json.dumps(manifest, indent=2))
    print()
    print("=== LEAKING HASHES (cross-split duplicates) ===")
    if leaking_hashes:
        for h, splits in list(leaking_hashes.items())[:20]:
            print(f"  {h[:16]}...  splits={sorted(splits)}")
        if len(leaking_hashes) > 20:
            print(f"  ... and {len(leaking_hashes) - 20} more")
    else:
        print("  none found")


if __name__ == "__main__":
    main()
