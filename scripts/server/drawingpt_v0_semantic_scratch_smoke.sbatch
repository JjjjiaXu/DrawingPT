#!/usr/bin/env bash
#SBATCH --job-name=drawingpt-v0-sem
#SBATCH --qos=normal
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=00:45:00
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
if [[ ! -d "$DATA_ROOT/train/train/svg_gt" && ! -d "$DATA_ROOT/svg/train" && -d "$SCRATCH_ROOT/processed/FloorPlanCAD/svg/train" ]]; then
  DATA_ROOT="$SCRATCH_ROOT/processed/FloorPlanCAD"
fi

RUN_NAME="${RUN_NAME:-drawingpt_v0_semantic_scratch_1pct_seed0304_fg_loss_smoke}"
LABEL_LIST="${LABEL_LIST:-configs/label_fractions/floorplancad_train_seed0304_001pct.txt}"
WINDOW_SIZE="${WINDOW_SIZE:-2048}"
LIMIT_WINDOWS="${LIMIT_WINDOWS:-0}"
VAL_LIMIT_WINDOWS="${VAL_LIMIT_WINDOWS:-128}"
BATCH_SIZE="${BATCH_SIZE:-2}"
EVAL_BATCH_SIZE="${EVAL_BATCH_SIZE:-2}"
STEPS="${STEPS:-100}"
HIDDEN_DIM="${HIDDEN_DIM:-128}"
LAYERS="${LAYERS:-2}"
HEADS="${HEADS:-4}"
SEED="${SEED:-304}"
LR="${LR:-0.001}"

mkdir -p "$PROJECT_ROOT/logs/slurm" "$PROJECT_ROOT/outputs/reports" "$PROJECT_ROOT/outputs/checkpoints"

if [[ -d "$VENV_DIR" ]]; then
  source "$VENV_DIR/bin/activate"
fi

cd "$PROJECT_ROOT"

echo "[drawingpt-v0-semantic] host=$(hostname)"
echo "[drawingpt-v0-semantic] date=$(date)"
echo "[drawingpt-v0-semantic] CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-unset}"
echo "[drawingpt-v0-semantic] data=$DATA_ROOT"
echo "[drawingpt-v0-semantic] run=$RUN_NAME window=$WINDOW_SIZE batch=$BATCH_SIZE steps=$STEPS limit_windows=$LIMIT_WINDOWS val_limit=$VAL_LIMIT_WINDOWS"
nvidia-smi
python - <<'PY'
import torch
print("torch", torch.__version__)
print("cuda", torch.cuda.is_available())
if torch.cuda.is_available():
    print("device", torch.cuda.get_device_name(0))
PY

python scripts/train_semantic_primitive.py \
  --root "$DATA_ROOT" \
  --manifest reports/next_steps_2026-09-01/floorplancad_token_manifest_by_file.csv \
  --label-list "$LABEL_LIST" \
  --window-size "$WINDOW_SIZE" \
  --limit-windows "$LIMIT_WINDOWS" \
  --val-limit-windows "$VAL_LIMIT_WINDOWS" \
  --batch-size "$BATCH_SIZE" \
  --eval-batch-size "$EVAL_BATCH_SIZE" \
  --steps "$STEPS" \
  --hidden-dim "$HIDDEN_DIM" \
  --layers "$LAYERS" \
  --heads "$HEADS" \
  --seed "$SEED" \
  --lr "$LR" \
  --device auto \
  --summary-out "outputs/reports/${RUN_NAME}_summary.json" \
  --checkpoint-out "outputs/checkpoints/${RUN_NAME}.pt"
