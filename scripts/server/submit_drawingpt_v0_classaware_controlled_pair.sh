#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-$DEFAULT_PROJECT_ROOT}"
SCRATCH_ROOT="${SCRATCH_ROOT:-$HOME/data/scratch/$USER/DrawingPT}"
LEGACY_ROOT="${LEGACY_ROOT:-$HOME/data/users/$USER/DrawingPT}"
cd "$PROJECT_ROOT"

mkdir -p "$PROJECT_ROOT/logs/slurm" "$PROJECT_ROOT/outputs/reports" "$PROJECT_ROOT/outputs/checkpoints"

STEPS="${STEPS:-1000}"
WINDOW_SIZE="${WINDOW_SIZE:-2048}"
VAL_LIMIT_WINDOWS="${VAL_LIMIT_WINDOWS:-0}"
BATCH_SIZE="${BATCH_SIZE:-2}"
EVAL_BATCH_SIZE="${EVAL_BATCH_SIZE:-4}"
SEED="${SEED:-304}"
SAMPLER="${SAMPLER:-class_aware}"
CLASS_WEIGHTING="${CLASS_WEIGHTING:-inverse_sqrt}"
MAX_CLASS_WEIGHT="${MAX_CLASS_WEIGHT:-8.0}"
MAX_WINDOW_SAMPLE_WEIGHT="${MAX_WINDOW_SAMPLE_WEIGHT:-8.0}"
PRETRAINED_CHECKPOINT="${PRETRAINED_CHECKPOINT:-}"

DATA_ROOT="${DATA_ROOT:-}"
if [ -z "$DATA_ROOT" ]; then
  for candidate in \
    "$PROJECT_ROOT/data/raw/FloorPlanCAD" \
    "$LEGACY_ROOT/data/raw/FloorPlanCAD" \
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
  echo "[controlled-pair] ERROR: Could not locate FloorPlanCAD data root."
  echo "[controlled-pair] Checked project, legacy, and scratch data locations."
  exit 4
fi

if [ -z "$PRETRAINED_CHECKPOINT" ]; then
  for candidate in \
    "$PROJECT_ROOT/outputs/checkpoints/drawingpt_v0_pretrain_2048_seed0304_short.pt" \
    "$LEGACY_ROOT/outputs/checkpoints/drawingpt_v0_pretrain_2048_seed0304_short.pt" \
    "$SCRATCH_ROOT/outputs/checkpoints/drawingpt_v0_pretrain_2048_seed0304_short.pt"
  do
    if [ -f "$candidate" ]; then
      PRETRAINED_CHECKPOINT="$candidate"
      break
    fi
  done
fi

SCRATCH_RUN_NAME="${SCRATCH_RUN_NAME:-drawingpt_v0_semantic_classaware_weighted_scratch_1pct_seed0304_${STEPS}step}"
PRETRAIN_RUN_NAME="${PRETRAIN_RUN_NAME:-drawingpt_v0_semantic_classaware_weighted_pretrained_1pct_seed0304_${STEPS}step}"

echo "[controlled-pair] project=$PROJECT_ROOT"
echo "[controlled-pair] data=$DATA_ROOT"
echo "[controlled-pair] steps=$STEPS window=$WINDOW_SIZE val_limit=$VAL_LIMIT_WINDOWS batch=$BATCH_SIZE eval_batch=$EVAL_BATCH_SIZE"
echo "[controlled-pair] sampler=$SAMPLER class_weighting=$CLASS_WEIGHTING seed=$SEED"
if [ -n "$PRETRAINED_CHECKPOINT" ]; then
  echo "[controlled-pair] pretrained_checkpoint=$PRETRAINED_CHECKPOINT"
else
  echo "[controlled-pair] WARNING: pretrained checkpoint not found; submitting scratch run only."
fi

COMMON_EXPORT="ALL,PROJECT_ROOT=$PROJECT_ROOT,SCRATCH_ROOT=$SCRATCH_ROOT,DATA_ROOT=$DATA_ROOT,STEPS=$STEPS,WINDOW_SIZE=$WINDOW_SIZE,VAL_LIMIT_WINDOWS=$VAL_LIMIT_WINDOWS,BATCH_SIZE=$BATCH_SIZE,EVAL_BATCH_SIZE=$EVAL_BATCH_SIZE,SEED=$SEED,SAMPLER=$SAMPLER,CLASS_WEIGHTING=$CLASS_WEIGHTING,MAX_CLASS_WEIGHT=$MAX_CLASS_WEIGHT,MAX_WINDOW_SAMPLE_WEIGHT=$MAX_WINDOW_SAMPLE_WEIGHT"

scratch_job="$(
  sbatch --parsable \
    --export="$COMMON_EXPORT,MODE=scratch,RUN_NAME=$SCRATCH_RUN_NAME" \
    scripts/server/drawingpt_v0_semantic_controlled.sbatch
)"

echo "[controlled-pair] scratch_job=$scratch_job run=$SCRATCH_RUN_NAME"
echo "[controlled-pair] summary files:"
echo "  outputs/reports/${SCRATCH_RUN_NAME}_summary.json"

if [ -n "$PRETRAINED_CHECKPOINT" ]; then
  pretrain_job="$(
    sbatch --parsable \
      --dependency=afterok:"$scratch_job" \
      --export="$COMMON_EXPORT,MODE=pretrained,RUN_NAME=$PRETRAIN_RUN_NAME,PRETRAINED_CHECKPOINT=$PRETRAINED_CHECKPOINT" \
      scripts/server/drawingpt_v0_semantic_controlled.sbatch
  )"
  echo "[controlled-pair] pretrained_job=$pretrain_job run=$PRETRAIN_RUN_NAME dependency=afterok:$scratch_job"
  echo "  outputs/reports/${PRETRAIN_RUN_NAME}_summary.json"
  squeue -j "$scratch_job","$pretrain_job" -o "%.18i %.9P %.32j %.8u %.2t %.10M %.6D %R"
else
  squeue -j "$scratch_job" -o "%.18i %.9P %.32j %.8u %.2t %.10M %.6D %R"
fi
