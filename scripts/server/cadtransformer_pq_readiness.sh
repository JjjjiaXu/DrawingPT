#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-$HOME/data/users/$USER/DrawingPT}"
SCRATCH_ROOT="${SCRATCH_ROOT:-$HOME/data/scratch/$USER/DrawingPT}"
CAD_ROOT="${CAD_ROOT:-$PROJECT_ROOT/third_party/CADTransformer}"
DATA_ROOT="${DATA_ROOT:-$SCRATCH_ROOT/processed/FloorPlanCAD}"

echo "[pq-readiness] user=$USER"
echo "[pq-readiness] host=$(hostname)"
echo "[pq-readiness] cad_root=$CAD_ROOT"
echo "[pq-readiness] data_root=$DATA_ROOT"

if [ ! -d "$CAD_ROOT" ]; then
  echo "ERROR: CADTransformer directory not found" >&2
  exit 1
fi

cd "$CAD_ROOT"

if [ -f scripts/evaluate_pq.py ]; then
  echo "[pq-readiness] scripts/evaluate_pq.py: found"
else
  echo "[pq-readiness] scripts/evaluate_pq.py: MISSING"
fi

if grep -R --exclude-dir="__pycache__" "get_pred_instance" -n train_cad_ddp.py eval.py models utils >/dev/null 2>&1; then
  echo "[pq-readiness] prediction helper reference: present in codebase"
else
  echo "[pq-readiness] prediction helper reference: not found"
fi

if grep -R --exclude-dir="__pycache__" "save_pred_dir" -n train_cad_ddp.py eval.py models utils config >/dev/null 2>&1; then
  echo "[pq-readiness] save_pred_dir references:"
  grep -R --exclude-dir="__pycache__" "save_pred_dir" -n train_cad_ddp.py eval.py models utils config || true
else
  echo "[pq-readiness] save_pred_dir references: not found in inference path"
fi

echo "[pq-readiness] processed data counts"
for split in train val test; do
  printf "  %s npy=" "$split"
  find "$DATA_ROOT/npy/$split" -maxdepth 1 -type f -name "*.npy" 2>/dev/null | wc -l
  printf "  %s png=" "$split"
  find "$DATA_ROOT/png/$split" -maxdepth 1 -type f -name "*.png" 2>/dev/null | wc -l
  printf "  %s svg=" "$split"
  find "$DATA_ROOT/svg/$split" -maxdepth 1 -type f -name "*.svg" 2>/dev/null | wc -l
done

echo "[pq-readiness] checkpoints/logs"
find logs -maxdepth 2 -type f \( -name "*.log" -o -name "*.pth" \) -printf "  %P %s\n" 2>/dev/null | sort | tail -40 || true

echo "[pq-readiness] prediction directories"
find logs -maxdepth 3 -type d -name "*pred*" -printf "  %P\n" 2>/dev/null | sort || true

echo "[pq-readiness] done"
