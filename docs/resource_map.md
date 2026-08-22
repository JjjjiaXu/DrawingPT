# DrawingPT resource map

Last checked: 2026-08-15.

## Dataset

### FloorPlanCAD

- Official site: https://floorplancad.github.io/
- Official paper: https://arxiv.org/abs/2105.07147
- Format according to official site: SVG drawings with annotation fields, PNG drawing images, and COCO visualization folders.
- Official news: initial 11,602 drawings in 2021-08; updated 15,663 drawings in 2021-11; project shutdown notice in 2023-01.
- Download actually completed here through the Drive IDs used by CADTransformer/SymPoint/GAT-CADNet: 11,602 SVG drawings split as train 6,965 / val 810 / test 3,827. This matches the baseline scripts, not the later 15,663-drawing website update.
- License note: annotations and website are CC BY-NC 4.0; authors say they do not own the copyright of the drawings.

Action:

1. Download the official dataset manually if Google Drive confirmation is required.
2. Place extracted files under `data/raw/FloorPlanCAD/`.
3. Run `python scripts/scan_floorplancad.py --root data/raw/FloorPlanCAD`.

Current local status:

- `data/raw/FloorPlanCAD/train.zip`: downloaded.
- `data/raw/FloorPlanCAD/val.zip`: downloaded.
- `data/raw/FloorPlanCAD/test.zip`: downloaded.
- All three splits extracted.
- Reports written under `outputs/reports/`.

## Baseline candidates

### CADTransformer

- Repo: https://github.com/VITA-Group/CADTransformer
- Paper: CVPR 2022.
- Why useful: official-ish, has sample data, preprocessing scripts, and reported FloorPlanCAD pipeline.
- Caveat: recommended stack is old: Python 3.7.7, CUDA 11.1, PyTorch 1.9.0, HRNet pretrained checkpoint.
- HRNet checkpoint status: downloaded to `third_party/CADTransformer/pretrained_models/hrnetv2_w48_imagenet_pretrained.pth`; SHA256 verified as `0efec102d97f2ef58f0e258b2c3076b3704b93ffc2b73f64c8da5462c0037ef8`.
- Baseline status: conservative full-data run completed as Slurm job 969, best validation Total FG F1 `0.827501118183136`; see `experiments/cadtransformer_baseline_2026-08-18.md`.
- Caveat: job 969 used `img_size=384` and `rgb_dim=0`, so it is a runnable baseline anchor rather than a paper-faithful reproduction.

### DXF / DWG-to-vector inspection

- Primary local utility: `scripts/inspect_dxf.py`.
- DXF parsing dependency: `ezdxf`.
- Current capability: entity counts, layer counts, block references, text examples, and geometry previews for common DXF entities.
- Discipline: no private DWG/DXF files are committed; raw converted drawings must stay under ignored data directories.
- Next gate: run a real public DXF smoke sample and freeze the JSON summary hash before adding public DXF drawings to pre-training.
- Details: `docs/dxf_toolchain_report.md`.

### SymPoint

- Repo: https://github.com/nicehuster/SymPoint
- Paper: ICLR 2024 / arXiv 2401.10556.
- Why useful: point-based primitive baseline; closer to DrawingPT's vector-native direction than raster methods.
- Caveat: depends on PyTorch + Detectron2 + CUDA; likely easier on Linux/WSL than native Windows.

### GAT-CADNet

- Repo: https://github.com/Liberation-happy/GAT-CADNet
- Paper: CVPR 2022; repo is an unofficial reproduction.
- Why useful: simpler graph baseline for sanity checks.
- Caveat: fewer commits and less mature than CADTransformer/SymPoint.

### CADSpotting

- Paper: https://arxiv.org/abs/2412.07377
- Why useful: dense point sampling + sliding-window aggregation is directly relevant to scalability.
- Caveat: I did not find a public official code repository; treat as paper baseline unless code appears.

## Collision / adjacent work to watch

- Text-Enhanced Panoptic Symbol Spotting in CAD Drawings: https://arxiv.org/abs/2510.11091
  - Important because DrawingPT's proposed second stream is text/annotation. This paper should be read before making novelty claims.
- SymPoint-V2: https://github.com/nicehuster/SymPointV2
  - Important because it adds layer feature enhancement and faster convergence.
- VecFormer: https://github.com/WesKwong/VecFormer
  - Important as a newer vector/line-based baseline.

## Resources I still need from you

- A GitHub account/organization destination if you want me to create or push a remote repository.
- FloorPlanCAD download access if the official link requires browser login or manual confirmation.
- GPU environment for baseline training. Native Windows may be awkward for Detectron2/CUDA; Linux or WSL2 is preferable.
- Disk budget. The raw SVG zip files are small here, but converted PNG/NPY files, checkpoints, and baseline outputs can still require tens of GB.
