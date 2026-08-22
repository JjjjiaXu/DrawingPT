#!/usr/bin/env bash
# Conservative full-data CADTransformer training run for the YaoGroup server.
#
# Defaults are intentionally modest: one GPU, low CPU count, no debug
# subset, and no optional npy_rgb dependency. Override with sbatch --export if
# you want a larger run, e.g.:
#   sbatch --export=ALL,EPOCHS=300,IMG_SIZE=700,RUN_NAME=cadtransformer_full ...

#SBATCH --job-name=cadtrans-train
#SBATCH --qos=normal
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=40G
#SBATCH --time=16:00:00
#SBATCH --hint=nomultithread
#SBATCH --output=logs/slurm/%x-%j.out
#SBATCH --error=logs/slurm/%x-%j.err
#SBATCH --open-mode=append

set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-$HOME/data/users/$USER/DrawingPT}"
SCRATCH_ROOT="${SCRATCH_ROOT:-$HOME/data/scratch/$USER/DrawingPT}"
VENV_DIR="${VENV_DIR:-$SCRATCH_ROOT/.venv-cadtransformer}"
DATA_ROOT="${DATA_ROOT:-$SCRATCH_ROOT/processed/FloorPlanCAD}"

EPOCHS="${EPOCHS:-10}"
IMG_SIZE="${IMG_SIZE:-384}"
WORKERS="${WORKERS:-0}"
BATCH_SIZE="${BATCH_SIZE:-1}"
TEST_BATCH_SIZE="${TEST_BATCH_SIZE:-1}"
RGB_DIM="${RGB_DIM:-0}"
RUN_NAME="${RUN_NAME:-cadtransformer_train_e${EPOCHS}_img${IMG_SIZE}_rgb${RGB_DIM}_$(date +%Y%m%d_%H%M%S)}"

mkdir -p "$PROJECT_ROOT/logs/slurm"
source "$VENV_DIR/bin/activate"

# Avoid unexpected network downloads from timm during unattended training. The
# required HRNet checkpoint is still loaded from --pretrained_model below.
export CADTRANSFORMER_VIT_PRETRAINED="${CADTRANSFORMER_VIT_PRETRAINED:-0}"

echo "[train] host=$(hostname)"
echo "[train] date=$(date)"
echo "[train] CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-unset}"
echo "[train] data=$DATA_ROOT"
echo "[train] run=$RUN_NAME"
echo "[train] epochs=$EPOCHS img_size=$IMG_SIZE workers=$WORKERS batch=$BATCH_SIZE test_batch=$TEST_BATCH_SIZE rgb_dim=$RGB_DIM"
nvidia-smi
python - <<'PY'
import torch
print("torch", torch.__version__)
print("cuda", torch.cuda.is_available())
if torch.cuda.is_available():
    print("device", torch.cuda.get_device_name(0))
PY

cd "$PROJECT_ROOT/third_party/CADTransformer"
torchrun --standalone --nproc_per_node=1 train_cad_ddp.py \
  --data_root "$DATA_ROOT" \
  --pretrained_model "$PROJECT_ROOT/third_party/CADTransformer/pretrained_models/hrnetv2_w48_imagenet_pretrained.pth" \
  --log_dir "$RUN_NAME" \
  --img_size "$IMG_SIZE" \
  epoch "$EPOCHS" \
  WORKERS "$WORKERS" \
  batch_size "$BATCH_SIZE" \
  test_batch_size "$TEST_BATCH_SIZE" \
  rgb_dim "$RGB_DIM"
