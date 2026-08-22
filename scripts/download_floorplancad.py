from __future__ import annotations

import argparse
import zipfile
from pathlib import Path

import gdown


GOOGLE_DRIVE_IDS = {
    "train": "16McNNY_-Y2uVnq42ntZTdYKPWgOZxwp3",
    "val": "1xgLqcj91i13_3vhfsUYcRYh3PhFYB9LJ",
    "test": "1Hc4-ggsUMoB_5uqJdqYRn9K73QS8rOgG",
}


def extract_zip(zip_path: Path, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as archive:
        archive.extractall(out_dir)


def main() -> None:
    parser = argparse.ArgumentParser(description="Download FloorPlanCAD splits from the public Google Drive IDs.")
    parser.add_argument(
        "--split",
        choices=["train", "val", "test", "all"],
        default="all",
        help="Dataset split to download.",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("data/raw/FloorPlanCAD"),
        help="Output directory.",
    )
    parser.add_argument("--no-extract", action="store_true", help="Only download zip files.")
    parser.add_argument("--dry-run", action="store_true", help="Print URLs and output paths without downloading.")
    args = parser.parse_args()

    splits = list(GOOGLE_DRIVE_IDS) if args.split == "all" else [args.split]
    args.out_dir.mkdir(parents=True, exist_ok=True)

    for split in splits:
        file_id = GOOGLE_DRIVE_IDS[split]
        url = f"https://drive.google.com/uc?id={file_id}"
        zip_path = args.out_dir / f"{split}.zip"
        extract_dir = args.out_dir / split

        print(f"{split}: {url} -> {zip_path}")
        if args.dry_run:
            continue

        if zip_path.exists() and zip_path.stat().st_size > 0:
            print(f"  using existing zip: {zip_path}")
        else:
            result = gdown.download(url, str(zip_path), quiet=False)
            if result is None:
                raise SystemExit(
                    f"gdown failed for {split}. Try opening the official link in a browser and download manually."
                )

        if not args.no_extract:
            print(f"  extracting to {extract_dir}")
            extract_zip(zip_path, extract_dir)


if __name__ == "__main__":
    main()

