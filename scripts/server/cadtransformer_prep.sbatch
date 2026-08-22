#!/usr/bin/env bash
#SBATCH --job-name=cadtrans-prep
#SBATCH --qos=normal
#SBATCH --cpus-per-task=4
#SBATCH --mem=24G
#SBATCH --time=24:00:00
#SBATCH --hint=nomultithread
#SBATCH --output=logs/slurm/%x-%j.out
#SBATCH --error=logs/slurm/%x-%j.err
#SBATCH --open-mode=append

set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-$HOME/data/users/$USER/DrawingPT}"
SCRATCH_ROOT="${SCRATCH_ROOT:-$HOME/data/scratch/$USER/DrawingPT}"

mkdir -p "$PROJECT_ROOT/logs/slurm"
cd "$PROJECT_ROOT"

echo "[prep-job] host=$(hostname)"
echo "[prep-job] date=$(date)"
echo "[prep-job] cpus=${SLURM_CPUS_PER_TASK:-unset}"
THREADS="${SLURM_CPUS_PER_TASK:-4}" bash scripts/server/prepare_cadtransformer_data.sh
