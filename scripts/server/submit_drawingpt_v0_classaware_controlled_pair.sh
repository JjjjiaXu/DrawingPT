#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-$HOME/data/users/$USER/DrawingPT}"
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
PRETRAINED_CHECKPOINT="${PRETRAINED_CHECKPOINT:-outputs/checkpoints/drawingpt_v0_pretrain_2048_seed0304_short.pt}"

SCRATCH_RUN_NAME="${SCRATCH_RUN_NAME:-drawingpt_v0_semantic_classaware_weighted_scratch_1pct_seed0304_${STEPS}step}"
PRETRAIN_RUN_NAME="${PRETRAIN_RUN_NAME:-drawingpt_v0_semantic_classaware_weighted_pretrained_1pct_seed0304_${STEPS}step}"

echo "[controlled-pair] project=$PROJECT_ROOT"
echo "[controlled-pair] steps=$STEPS window=$WINDOW_SIZE val_limit=$VAL_LIMIT_WINDOWS batch=$BATCH_SIZE eval_batch=$EVAL_BATCH_SIZE"
echo "[controlled-pair] sampler=$SAMPLER class_weighting=$CLASS_WEIGHTING seed=$SEED"

scratch_job="$(
  sbatch --parsable \
    --export=ALL,MODE=scratch,RUN_NAME="$SCRATCH_RUN_NAME",STEPS="$STEPS",WINDOW_SIZE="$WINDOW_SIZE",VAL_LIMIT_WINDOWS="$VAL_LIMIT_WINDOWS",BATCH_SIZE="$BATCH_SIZE",EVAL_BATCH_SIZE="$EVAL_BATCH_SIZE",SEED="$SEED",SAMPLER="$SAMPLER",CLASS_WEIGHTING="$CLASS_WEIGHTING",MAX_CLASS_WEIGHT="$MAX_CLASS_WEIGHT",MAX_WINDOW_SAMPLE_WEIGHT="$MAX_WINDOW_SAMPLE_WEIGHT" \
    scripts/server/drawingpt_v0_semantic_controlled.sbatch
)"

pretrain_job="$(
  sbatch --parsable \
    --dependency=afterok:"$scratch_job" \
    --export=ALL,MODE=pretrained,RUN_NAME="$PRETRAIN_RUN_NAME",STEPS="$STEPS",WINDOW_SIZE="$WINDOW_SIZE",VAL_LIMIT_WINDOWS="$VAL_LIMIT_WINDOWS",BATCH_SIZE="$BATCH_SIZE",EVAL_BATCH_SIZE="$EVAL_BATCH_SIZE",SEED="$SEED",SAMPLER="$SAMPLER",CLASS_WEIGHTING="$CLASS_WEIGHTING",MAX_CLASS_WEIGHT="$MAX_CLASS_WEIGHT",MAX_WINDOW_SAMPLE_WEIGHT="$MAX_WINDOW_SAMPLE_WEIGHT",PRETRAINED_CHECKPOINT="$PRETRAINED_CHECKPOINT" \
    scripts/server/drawingpt_v0_semantic_controlled.sbatch
)"

echo "[controlled-pair] scratch_job=$scratch_job run=$SCRATCH_RUN_NAME"
echo "[controlled-pair] pretrained_job=$pretrain_job run=$PRETRAIN_RUN_NAME dependency=afterok:$scratch_job"
echo "[controlled-pair] summary files:"
echo "  outputs/reports/${SCRATCH_RUN_NAME}_summary.json"
echo "  outputs/reports/${PRETRAIN_RUN_NAME}_summary.json"

squeue -j "$scratch_job","$pretrain_job" -o "%.18i %.9P %.32j %.8u %.2t %.10M %.6D %R"
