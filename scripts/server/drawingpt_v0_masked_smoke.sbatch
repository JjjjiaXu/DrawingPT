#!/usr/bin/env bash
#SBATCH --job-name=drawingpt-v0-smoke
#SBATCH --qos=spare
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=00:30:00
#SBATCH --hint=nomultithread
#SBATCH --output=logs/slurm/%x-%j.out
#SBATCH --error=logs/slurm/%x-%j.err
#SBATCH --open-mode=append

set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-$HOME/data/users/$USER/DrawingPT}"
SCRATCH_ROOT="${SCRATCH_ROOT:-$HOME/data/scratch/$USER/DrawingPT}"
VENV_DIR="${VENV_DIR:-$SCRATCH_ROOT/.venv-cadtransformer}"
DATA_ROOT="${DATA_ROOT:-$PROJECT_ROOT/data/raw/FloorPlanCAD}"

if [[ ! -d "$DATA_ROOT/train/train/svg_gt" && -d "$SCRATCH_ROOT/raw/FloorPlanCAD/train/train/svg_gt" ]]; then
  DATA_ROOT="$SCRATCH_ROOT/raw/FloorPlanCAD"
fi

mkdir -p "$PROJECT_ROOT/logs/slurm" "$PROJECT_ROOT/outputs/reports" "$PROJECT_ROOT/outputs/checkpoints"

if [[ -d "$VENV_DIR" ]]; then
  source "$VENV_DIR/bin/activate"
fi

cd "$PROJECT_ROOT"

echo "[drawingpt-v0-smoke] host=$(hostname)"
echo "[drawingpt-v0-smoke] date=$(date)"
echo "[drawingpt-v0-smoke] CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-unset}"
echo "[drawingpt-v0-smoke] data=$DATA_ROOT"
nvidia-smi
python - <<'PY'
import torch
print("torch", torch.__version__)
print("cuda", torch.cuda.is_available())
if torch.cuda.is_available():
    print("device", torch.cuda.get_device_name(0))
PY

python scripts/train_masked_primitive.py \
  --root "$DATA_ROOT" \
  --manifest reports/next_steps_2026-09-01/floorplancad_token_manifest_by_file.csv \
  --split train \
  --label-list configs/label_fractions/floorplancad_train_seed0304_001pct.txt \
  --window-size 512 \
  --limit-windows 256 \
  --batch-size 8 \
  --steps 100 \
  --hidden-dim 128 \
  --layers 2 \
  --heads 4 \
  --mask-ratio 0.30 \
  --seed 304 \
  --device auto \
  --summary-out outputs/reports/drawingpt_v0_masked_smoke_summary.json \
  --checkpoint-out outputs/checkpoints/drawingpt_v0_masked_smoke.pt
