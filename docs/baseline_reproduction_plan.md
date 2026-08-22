# Baseline reproduction plan

Generated locally on 2026-08-15. Updated on 2026-08-22 after the first CADTransformer full-data run completed.

## Current status

Done:

- FloorPlanCAD 11,602-file version downloaded and extracted.
- Baseline repositories cloned under `third_party/`.
- Local lightweight data inspection environment works with Python 3.12.
- CADTransformer smoke test completed on the YaoGroup GPU server.
- CADTransformer conservative 10-epoch full-data run completed as Slurm job 969.

Not done yet:

- Paper-faithful CADTransformer reproduction is not complete yet because the conservative run used `img_size=384` and `rgb_dim=0`.
- The original-style `img_size=700` / `rgb_dim=32` / `npy_rgb` feature path still needs to be restored or explicitly ruled out.

Downloaded:

- CADTransformer HRNet-W48 checkpoint exists at `third_party/CADTransformer/pretrained_models/hrnetv2_w48_imagenet_pretrained.pth`.
- Size: 310,643,500 bytes.
- SHA256: `0efec102d97f2ef58f0e258b2c3076b3704b93ffc2b73f64c8da5462c0037ef8`.
- Official HRNet README points to OneDrive/Baidu links; OneDrive command-line access was blocked here, so the file was downloaded from a HuggingFace mirror with the same filename and verified by size/hash.

## Baseline priority

### 1. CADTransformer

Why first:

- Official CVPR 2022 implementation.
- Has preprocessing scripts for SVG to PNG/NPY.
- Uses the same FloorPlanCAD Drive IDs already downloaded.

Environment from README:

- CUDA 11.1
- Python 3.7.7
- PyTorch 1.9.0
- torchvision 0.10.0
- scikit-learn 1.0.1
- pillow 8.3.1
- opencv-python, matplotlib, scipy, tqdm, gdown, svgpathtools
- HRNet-W48-C ImageNet pretrained checkpoint

Suggested platform:

- Linux or WSL2 with NVIDIA GPU.
- Avoid native Windows for training unless forced.

Dataset preparation target:

```text
data/FloorPlanCAD/
  svg/train
  svg/val
  svg/test
  png/train
  png/val
  png/test
  npy/train
  npy/val
  npy/test
```

First smoke test:

```bash
python preprocess/preprocess_svg.py \
  -i /path/to/FloorPlanCAD/val/val/svg_gt \
  -o /path/to/processed/npy/val \
  --thread_num 4
```

Then train/eval:

```bash
CUDA_VISIBLE_DEVICES=0 python -m torch.distributed.launch --nproc_per_node=1 \
  train_cad_ddp.py \
  --data_root /path/to/data/FloorPlanCAD \
  --pretrained_model /path/to/hrnetv2_w48_imagenet_pretrained.pth
```

Completed local/server result:

- Slurm job: 969
- State: `COMPLETED`, exit code `0:0`
- Hardware: one NVIDIA GeForce RTX 5090
- Runtime: 10:21:28
- Settings: 10 epochs, `img_size=384`, `rgb_dim=0`, batch size 1, workers 0
- Best validation Total FG F1: `0.827501118183136`
- Best checkpoint SHA-256: `642da46678d5f8d76cdeb958df4e6c77d5d9e3462a640467d9d83c6283a35530`

Caveat: this is a conservative baseline sanity run, not a paper-faithful reproduction. Do not compare it directly to reported paper numbers until preprocessing, image size, RGB feature inputs, and evaluation protocol are matched.

### 2. SymPoint

Why second:

- Stronger point-based baseline.
- Very relevant to DrawingPT because it parses vector primitives into point-like representations.

Environment from README:

- Python 3.8
- PyTorch 1.10.0 + CUDA 11.1
- torchvision 0.11.0
- gdown, mmcv 0.2.14, svgpathtools 1.6.1, munch, tensorboard, tensorboardx
- Detectron2 0.6 or built from GitHub
- custom `modules/pointops` compilation

Risk:

- Detectron2 and pointops compilation are likely painful on native Windows.

First smoke test:

```bash
python parse_svg.py --split val --data_dir /path/to/FloorPlanCAD/val/val/svg_gt
```

### 3. GAT-CADNet reproduction

Why third:

- Simpler graph baseline and useful sanity check.
- Unofficial implementation, so do not treat its numbers as authoritative until verified.

Environment from README:

- Ubuntu 22.04
- Python 3.11
- `pip install -r requirements.txt`

First smoke test:

```bash
python main.py
```

## Resources needed before training

- NVIDIA GPU. CADTransformer ran successfully on one RTX 5090 under conservative settings.
- Linux/WSL2 or the YaoGroup Slurm server remains the preferred training platform.
- Time budget for paper-faithful metric matching. The kickoff target is within 2 points of the paper number, but this has not been evaluated under matched settings yet.
