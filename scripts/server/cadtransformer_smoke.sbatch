#!/usr/bin/env bash
#SBATCH --job-name=cadtrans-smoke
#SBATCH --qos=spare
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=00:45:00
#SBATCH --hint=nomultithread
#SBATCH --output=logs/slurm/%x-%j.out
#SBATCH --error=logs/slurm/%x-%j.err
#SBATCH --open-mode=append

set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-$HOME/data/users/$USER/DrawingPT}"
SCRATCH_ROOT="${SCRATCH_ROOT:-$HOME/data/scratch/$USER/DrawingPT}"
VENV_DIR="${VENV_DIR:-$SCRATCH_ROOT/.venv-cadtransformer}"
DATA_ROOT="${DATA_ROOT:-$SCRATCH_ROOT/processed/FloorPlanCAD}"

mkdir -p "$PROJECT_ROOT/logs/slurm"
source "$VENV_DIR/bin/activate"
export CADTRANSFORMER_VIT_PRETRAINED=0

echo "[smoke] host=$(hostname)"
echo "[smoke] date=$(date)"
echo "[smoke] CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-unset}"
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
  --log_dir cadtransformer_smoke \
  --debug \
  --img_size 384 \
  --max_prim 2500 \
  epoch 1 WORKERS 0 rgb_dim 0
