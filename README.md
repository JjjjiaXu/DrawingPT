# DrawingPT

Self-supervised pre-training for 2D engineering drawings.

This repository follows the kickoff document in this workspace: reproduce first, then pre-train, then judge the project with a label-efficiency curve.

## Current objective

Build a clean academic research repo for DrawingPT:

1. Download and inspect FloorPlanCAD.
2. Reproduce one or two public baselines on FloorPlanCAD.
3. Prototype DrawingPT v0: vector primitive tokenization plus vector-to-raster self-supervised alignment.
4. Compare pre-training vs training from scratch under limited labels.

## Quick start

Use Python 3.10+ for the local inspection utilities. On this machine, plain `python` currently resolves to Python 3.7.0, which is too old for the modern utility dependencies. I used the bundled Codex Python 3.12 runtime for the smoke test.

```powershell
$py = 'C:\Users\Lenovo\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $py -m venv .venv-codex
.\.venv-codex\Scripts\Activate.ps1
python -m pip install -r requirements.txt --index-url https://pypi.org/simple
python scripts/check_env.py
```

After FloorPlanCAD is downloaded:

```powershell
python scripts/scan_floorplancad.py --root data/raw/FloorPlanCAD
python scripts/floorplancad_stats.py --root data/raw/FloorPlanCAD/val --json-out outputs/reports/floorplancad_val_stats.json
```

To download FloorPlanCAD from the public Google Drive IDs used by CADTransformer/SymPoint:

```powershell
python scripts/download_floorplancad.py --dry-run
python scripts/download_floorplancad.py --split val
```

If Google Drive blocks command-line download, download manually from the official site and extract into `data/raw/FloorPlanCAD/`.

For any DXF/DWG-converted-to-DXF file:

```powershell
python scripts/inspect_dxf.py --input path\to\drawing.dxf
```

## Repository layout

- `configs/`: path/config examples.
- `data/`: local datasets; ignored by git.
- `docs/`: project plan, resource map, and v0 design notes.
- `experiments/`: experiment records and label-efficiency curve logs.
- `notes/literature/`: 10-line paper notes requested by the kickoff.
- `scripts/`: small utilities for environment checks and data inspection.
- `third_party/`: local baseline clones; ignored by git except manifest/readme.

## Discipline

- Public datasets only until a data agreement exists.
- Keep this academic repo separate from product/company code.
- Do not commit raw datasets, private drawings, checkpoints, or customer information.

## Current week-1 status

See `docs/week1_completion_report.md`. The first CADTransformer conservative full-data run completed as Slurm job 969 with best validation Total FG F1 `0.827501118183136`; this is a runnable baseline anchor, not yet a paper-faithful reproduction.
