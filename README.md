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

## 当前第一周状态

第一周完成度见 `docs/week1_completion_report.md`，组会可读版中文报告见 `reports/group_meeting_2026-08-18/report.html`。FloorPlanCAD 图元分布与 CADTransformer 指标差距检查见 `docs/floorplancad_distribution_report.md`。

第一版 CADTransformer 保守 full-data baseline 已经完成，Slurm job 969 的 best validation Total FG F1 为 `0.827501118183136`。这个结果是可运行基线锚点，还不是 paper-faithful 论文复现。

目前已补齐 FloorPlanCAD 图元类型/数量分布：11,602 张 SVG 共 12,621,288 个 raw primitive，其中 `path` 占 98.68%。也已补齐论文指标 vs 复现指标 vs runtime 对照：CADTransformer 原论文主指标是 PQ/SQ/RQ，本次 job 969 只产出 Total FG F1，因此不能直接相减；下一门禁是跑出 paper-faithful PQ/SQ/RQ。

面向项目推进和组会的记录默认使用中文；只有论文标题、API/config 名、指标名和命令保留英文。

## 下一阶段三件事

2026-09-01 已把下一阶段推进材料整理到 `reports/next_steps_2026-09-01/report.html`：

1. CADTransformer PQ/SQ/RQ 评估门禁：当前 release 缺少 README 所述 `scripts/evaluate_pq.py` 和 prediction export 链路，因此 PQ/SQ/RQ 尚未产出；详见 `docs/cadtransformer_pq_gate.md`。
2. DrawingPT v0 prereg：已冻结低标注自监督预训练协议草案；详见 `docs/drawingpt_v0_prereg.md`。
3. FloorPlanCAD 工程量 proxy：已从 11,602 张 SVG 统计出门窗、墙体、楼梯、车位、厨卫设备等 proxy 表；详见 `docs/floorplancad_quantity_proxy_report.md`。

2026-09-01 已继续补齐 DrawingPT v0 开训前资产，见 `docs/drawingpt_v0_implementation_assets.md`：

- primitive token manifest：12,621,288 个 token；按 2048 token/window 得到 14,117 个 window；
- 低标注比例清单：1/5/10/25/50/100%，seed 为 304/1004/2026，清单和 hash 已固定在 `configs/label_fractions/`；
- 每图 pseudo-BoQ 表：`reports/next_steps_2026-09-01/floorplancad_pseudo_boq_by_file.csv`，11,602 行。
