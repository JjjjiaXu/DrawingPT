#!/usr/bin/env bash
#SBATCH --job-name=drawingpt-v0-sem-w
#SBATCH --partition=compute
#SBATCH --qos=normal
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=00:45:00
#SBATCH --output=logs/slurm/%x-%j.out
#SBATCH --error=logs/slurm/%x-%j.err

set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-$HOME/data/users/$USER/DrawingPT}"
SCRATCH_ROOT="${SCRATCH_ROOT:-$HOME/data/scratch/$USER/DrawingPT}"
VENV_DIR="${VENV_DIR:-$SCRATCH_ROOT/.venv-cadtransformer}"
RUN_NAME="${RUN_NAME:-drawingpt_v0_semantic_weighted_1pct_seed0304_smoke}"
MANIFEST="${MANIFEST:-reports/next_steps_2026-09-01/floorplancad_token_manifest_by_file.csv}"
LABEL_LIST="${LABEL_LIST:-configs/label_fractions/floorplancad_train_seed0304_001pct.txt}"
PRETRAINED_CHECKPOINT="${PRETRAINED_CHECKPOINT:-}"
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
CLASS_WEIGHTING="${CLASS_WEIGHTING:-inverse_sqrt}"
MAX_CLASS_WEIGHT="${MAX_CLASS_WEIGHT:-8.0}"

mkdir -p "$PROJECT_ROOT/logs/slurm" "$PROJECT_ROOT/outputs/reports" "$PROJECT_ROOT/outputs/checkpoints"
cd "$PROJECT_ROOT"

if [ ! -x "$VENV_DIR/bin/python" ]; then
  echo "Missing Python environment: $VENV_DIR"
  exit 2
fi

DATA_ROOT="${DATA_ROOT:-}"
if [ -z "$DATA_ROOT" ]; then
  for candidate in \
    "$PROJECT_ROOT/data/raw/FloorPlanCAD" \
    "$SCRATCH_ROOT/raw/FloorPlanCAD" \
    "$SCRATCH_ROOT/processed/FloorPlanCAD"
  do
    if [ -d "$candidate" ]; then
      DATA_ROOT="$candidate"
      break
    fi
  done
fi

if [ -z "$DATA_ROOT" ] || [ ! -d "$DATA_ROOT" ]; then
  echo "Could not locate FloorPlanCAD data root."
  exit 4
fi

EXTRA_ARGS=()
if [ -n "$PRETRAINED_CHECKPOINT" ]; then
  if [ ! -f "$PRETRAINED_CHECKPOINT" ]; then
    echo "Missing pretrained checkpoint: $PRETRAINED_CHECKPOINT"
    exit 3
  fi
  EXTRA_ARGS+=(--pretrained-checkpoint "$PRETRAINED_CHECKPOINT" --trust-pretrained-checkpoint)
fi

echo "JOB_ID=${SLURM_JOB_ID:-manual}"
echo "HOST=$(hostname)"
echo "PROJECT_ROOT=$PROJECT_ROOT"
echo "DATA_ROOT=$DATA_ROOT"
echo "VENV_DIR=$VENV_DIR"
echo "RUN_NAME=$RUN_NAME"
echo "PRETRAINED_CHECKPOINT=${PRETRAINED_CHECKPOINT:-none}"
echo "WINDOW_SIZE=$WINDOW_SIZE LIMIT_WINDOWS=$LIMIT_WINDOWS VAL_LIMIT_WINDOWS=$VAL_LIMIT_WINDOWS"
echo "BATCH_SIZE=$BATCH_SIZE EVAL_BATCH_SIZE=$EVAL_BATCH_SIZE STEPS=$STEPS"
echo "CLASS_WEIGHTING=$CLASS_WEIGHTING MAX_CLASS_WEIGHT=$MAX_CLASS_WEIGHT"

"$VENV_DIR/bin/python" scripts/train_semantic_primitive.py \
  --root "$DATA_ROOT" \
  --manifest "$MANIFEST" \
  --label-list "$LABEL_LIST" \
  "${EXTRA_ARGS[@]}" \
  --window-size "$WINDOW_SIZE" \
  --limit-windows "$LIMIT_WINDOWS" \
  --val-limit-windows "$VAL_LIMIT_WINDOWS" \
  --batch-size "$BATCH_SIZE" \
  --eval-batch-size "$EVAL_BATCH_SIZE" \
  --steps "$STEPS" \
  --hidden-dim "$HIDDEN_DIM" \
  --layers "$LAYERS" \
  --heads "$HEADS" \
  --lr "$LR" \
  --seed "$SEED" \
  --class-weighting "$CLASS_WEIGHTING" \
  --max-class-weight "$MAX_CLASS_WEIGHT" \
  --log-every 20 \
  --summary-out "outputs/reports/${RUN_NAME}_summary.json" \
  --checkpoint-out "outputs/checkpoints/${RUN_NAME}.pt"
