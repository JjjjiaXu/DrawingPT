from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import random
from pathlib import Path

from floorplancad_quantity_proxy import split_roots


DEFAULT_FRACTIONS = (1, 5, 10, 25, 50, 100)
DEFAULT_SEEDS = (304, 1004, 2026)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fraction_label(percent: int) -> str:
    return f"{percent:03d}pct"


def write_file_list(path: Path, rows: list[str]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "".join(f"{row}\n" for row in rows)
    path.write_text(text, encoding="utf-8")
    return sha256_text(text)


def parse_int_list(value: str) -> list[int]:
    result: list[int] = []
    for part in value.split(","):
        part = part.strip()
        if not part:
            continue
        result.append(int(part))
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Freeze deterministic FloorPlanCAD low-label file lists.")
    parser.add_argument("--root", type=Path, default=Path("data/raw/FloorPlanCAD"))
    parser.add_argument("--out-dir", type=Path, default=Path("configs/label_fractions"))
    parser.add_argument("--report-dir", type=Path, default=Path("reports/next_steps_2026-09-01"))
    parser.add_argument("--fractions", default=",".join(str(x) for x in DEFAULT_FRACTIONS))
    parser.add_argument("--seeds", default=",".join(str(x) for x in DEFAULT_SEEDS))
    args = parser.parse_args()

    train_root = split_roots(args.root)["train"]
    if not train_root.exists():
        raise SystemExit(f"Missing FloorPlanCAD train SVG directory: {train_root}")

    fractions = parse_int_list(args.fractions)
    seeds = parse_int_list(args.seeds)
    if any(percent <= 0 or percent > 100 for percent in fractions):
        raise SystemExit("--fractions must be in the range 1..100")

    train_files = sorted(path.relative_to(args.root).as_posix() for path in train_root.glob("*.svg"))
    if not train_files:
        raise SystemExit(f"No train SVG files found under: {train_root}")

    manifest_rows: list[dict[str, object]] = []
    for seed in seeds:
        shuffled = train_files[:]
        random.Random(seed).shuffle(shuffled)
        for percent in fractions:
            count = len(shuffled) if percent == 100 else max(1, math.ceil(len(shuffled) * percent / 100))
            selected = shuffled[:count]
            out_path = args.out_dir / f"floorplancad_train_seed{seed:04d}_{fraction_label(percent)}.txt"
            file_hash = write_file_list(out_path, selected)
            manifest_rows.append(
                {
                    "dataset": "FloorPlanCAD",
                    "split": "train",
                    "seed": seed,
                    "fraction_percent": percent,
                    "file_count": count,
                    "total_train_files": len(train_files),
                    "list_path": out_path.as_posix(),
                    "sha256": file_hash,
                    "sampling_rule": "random shuffle with fixed seed; subset is the first ceil(N * fraction) files",
                }
            )

    manifest_fields = [
        "dataset",
        "split",
        "seed",
        "fraction_percent",
        "file_count",
        "total_train_files",
        "list_path",
        "sha256",
        "sampling_rule",
    ]
    for target in [args.out_dir / "manifest.csv", args.report_dir / "label_fraction_manifest.csv"]:
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=manifest_fields)
            writer.writeheader()
            writer.writerows(manifest_rows)

    summary = {
        "generated_at": "2026-09-01",
        "dataset": "FloorPlanCAD",
        "source_root": str(args.root),
        "split": "train",
        "total_train_files": len(train_files),
        "fractions_percent": fractions,
        "seeds": seeds,
        "counts_by_fraction": {
            str(percent): (len(train_files) if percent == 100 else max(1, math.ceil(len(train_files) * percent / 100)))
            for percent in fractions
        },
        "output_dir": str(args.out_dir),
        "manifest_path": str(args.out_dir / "manifest.csv"),
        "manifest_sha256": sha256_file(args.out_dir / "manifest.csv"),
        "caveats": [
            "These lists freeze which labeled train files are visible during low-label fine-tuning.",
            "The lists do not change validation/test usage; val remains for model selection and test remains for final evaluation.",
            "Class-balance diagnostics are not baked into the sampler yet; inspect coverage before interpreting rare-class failures.",
        ],
    }

    (args.out_dir / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (args.report_dir / "label_fraction_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
