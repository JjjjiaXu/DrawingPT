# Week 1 execution plan

## Goal

By the end of week 1:

- FloorPlanCAD is downloaded and structurally understood.
- At least one baseline repo is cloned and its environment requirements are known.
- One data inspection report exists.
- Literature notes exist for the required papers.
- DrawingPT v0 has a one-page design draft.

Completion status as of 2026-08-22 is tracked in `docs/week1_completion_report.md`.

## Day 1-2: environment and data

- Initialize independent academic repo.
- Download FloorPlanCAD.
- Run `scripts/scan_floorplancad.py`.
- Confirm what annotation fields exist in SVG.
- Record SVG element types, primitive counts, text fields, layer-like attributes, and split sizes.

## Day 2-3: baseline selection

Priority order:

1. CADTransformer: first smoke test because it ships samples and preprocessing.
2. SymPoint: stronger vector/point-style baseline, but likely more environment work.
3. GAT-CADNet reproduction: sanity graph baseline if the above is too heavy.

Acceptance:

- A baseline command runs on sample data.
- Full-dataset training plan is documented.
- Reported metric, reproduced metric, runtime, and hardware are recorded.

## Day 3-7: notes and v0 design

- Finish 10-line notes for Brep2Shape, FloorPlanCAD, CADSpotting, GeoPT, HouseMind, ArchPlanVQA, and text-enhanced CAD work.
- Write DrawingPT v0 tokenization and self-supervision draft.
- Define first label-efficiency curve protocol.

## Stop-loss rule

At week 6, if pre-training improves downstream performance by less than 5% relative to from-scratch under the planned low-label setting, pause and diagnose before scaling.
