# Week 1 completion report

Generated on 2026-08-22, against `20260812_DrawingPT_Kickoff_Student_Shareable.md` and `docs/week1_plan.md`.

## Verdict

Week 1 is complete on the main experimental track and slightly ahead on baseline reproduction.

The remaining caveat is that native/public DXF smoke testing is documented but not yet quantitatively validated on a real public DXF file. That is not blocking FloorPlanCAD or CADTransformer work, but it should be closed before expanding pre-training beyond FloorPlanCAD.

## Checklist

| Requirement | Status | Evidence |
|---|---|---|
| Independent academic repo | Done | Local git repo with `origin` set to `https://github.com/JjjjiaXu/DrawingPT.git`; repo discipline in `README.md`. |
| Public data only | Done | FloorPlanCAD public data only; no private/customer drawings committed. |
| FloorPlanCAD downloaded | Done | 11,602-file public baseline version: train 6,965 / val 810 / test 3,827. |
| Data loading / scan works | Done | `scripts/scan_floorplancad.py`, `scripts/floorplancad_stats.py`, and reports under `outputs/reports/` locally. |
| SVG annotation fields understood | Done | `docs/floorplancad_data_report.md` records `semanticId`, `instanceId`, geometry/style fields, and split statistics. |
| 35-class spotting path confirmed | Done | CADTransformer preprocessing and training consumed the 35-class FloorPlanCAD task. |
| DWG -> vector parsing investigated | Mostly done | `scripts/inspect_dxf.py` extracts DXF entities, geometry, layers, blocks, and text; see `docs/dxf_toolchain_report.md`. Real public DXF smoke sample remains a next gate. |
| Baseline repos investigated | Done | `third_party/MANIFEST.md` records CADTransformer, SymPoint, and GAT-CADNet references. |
| One executable baseline selected | Done | CADTransformer selected first because it ships FloorPlanCAD preprocessing and baseline scripts. |
| Baseline smoke run | Done | Slurm job 968 completed; smoke Total FG F1 = 0.256508. |
| Full baseline run plan | Done | `docs/baseline_reproduction_plan.md` and `experiments/cadtransformer_baseline_2026-08-18.md`. |
| Baseline run with runtime/hardware/metric | Done | Slurm job 969 completed on one RTX 5090; best validation Total FG F1 = 0.827501; elapsed 10:21:28. |
| Required 10-line notes | Done | Notes exist for FloorPlanCAD, CADSpotting, Brep2Shape, GeoPT, HouseMind, Text-Enhanced CAD, and ArchPlanVQA. |
| DrawingPT v0 design draft | Done | `docs/drawingpt_v0_design_draft.md`. |
| First label-efficiency protocol sketch | Done | Drafted in `docs/drawingpt_v0_design_draft.md`; needs full experiment matrix before week 4. |

## New frozen assets

| Asset | SHA-256 |
|---|---|
| HRNet-W48 ImageNet checkpoint | `0efec102d97f2ef58f0e258b2c3076b3704b93ffc2b73f64c8da5462c0037ef8` |
| CADTransformer smoke train log | `99a5f8a2bac787ec59336fc0562c27176b6e3f758e31de7126a0aa82f126ce57` |
| CADTransformer smoke best checkpoint | `86c534ef8d1bdec0efb37fecda5b3304dcd82ebf8a9ccdc16a5d062cae233302` |
| CADTransformer job 969 train log | `fe88160d0a83a5f0aa9b517d39901ce186f2682d9577e9376a05753267c917a4` |
| CADTransformer job 969 best checkpoint | `642da46678d5f8d76cdeb958df4e6c77d5d9e3462a640467d9d83c6283a35530` |
| CADTransformer job 969 last checkpoint | `d29a4da0e541f1faf827fcdd41a612ba7ef1c0fa6ddbb69a1d7d9196db9df5db` |

## New numbers

| Run | Metric | Value |
|---|---|---:|
| CADTransformer smoke, job 968 | Total FG Precision | 0.437268 |
| CADTransformer smoke, job 968 | Total FG Recall | 0.181527 |
| CADTransformer smoke, job 968 | Total FG F1 | 0.256508 |
| CADTransformer conservative baseline, job 969 | Best validation Total FG Precision | 0.832457 |
| CADTransformer conservative baseline, job 969 | Best validation Total FG Recall | 0.822702 |
| CADTransformer conservative baseline, job 969 | Best validation Total FG F1 | 0.827501 |
| CADTransformer conservative baseline, job 969 | Runtime | 10:21:28 |

## Caveats

- The job 969 run is a conservative baseline sanity run, not a paper-faithful CADTransformer reproduction.
- It used `img_size=384`, `rgb_dim=0`, `batch_size=1`, and `workers=0`.
- The original-style `img_size=700` / `rgb_dim=32` / `npy_rgb` path is the next reproduction gate.
- Do not compare the F1 directly to paper numbers without matching preprocessing and evaluation settings.

## Week 2 gate

1. Restore or justify the original CADTransformer feature setting (`rgb_dim=32` with `npy_rgb`) and image size.
2. Run a paper-faithful evaluation or document why the conservative run is the accepted baseline.
3. Add a public DXF smoke sample and freeze its `inspect_dxf.py` JSON summary.
4. Prepare the label-efficiency matrix for DrawingPT v0.
