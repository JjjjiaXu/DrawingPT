#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-$HOME/data/users/$USER/DrawingPT}"
SCRATCH_ROOT="${SCRATCH_ROOT:-$HOME/data/scratch/$USER/DrawingPT}"
VENV_DIR="${VENV_DIR:-$SCRATCH_ROOT/.venv-cadtransformer}"

echo "[bootstrap] user=$USER"
echo "[bootstrap] project=$PROJECT_ROOT"
echo "[bootstrap] scratch=$SCRATCH_ROOT"

mkdir -p "$PROJECT_ROOT" "$SCRATCH_ROOT" "$SCRATCH_ROOT/cache" "$SCRATCH_ROOT/logs"
cd "$PROJECT_ROOT"

echo "[bootstrap] server status"
command -v labctl >/dev/null 2>&1 && labctl status storage || true
command -v labctl >/dev/null 2>&1 && labctl status network || true
command -v lab-help >/dev/null 2>&1 && lab-help overview | head -n 80 || true

echo "[bootstrap] patch CADTransformer release compatibility"
python3 scripts/server/cadtransformer_compat_patch.py

echo "[bootstrap] uv/python environment"
if ! command -v uv >/dev/null 2>&1; then
  echo "ERROR: uv is not available on this server. Check lab-help env." >&2
  exit 1
fi

if [ ! -d "$VENV_DIR" ]; then
  uv venv "$VENV_DIR" --python 3.11
fi

# Activate explicitly because some old research code expects plain python/pip.
source "$VENV_DIR/bin/activate"
python -V

echo "[bootstrap] install PyTorch and CADTransformer dependencies"
# RTX 5090/Blackwell should use a recent CUDA wheel. Fall back to the server's configured default if cu128 is unavailable.
uv pip install --python "$VENV_DIR/bin/python" torch torchvision --index-url https://download.pytorch.org/whl/cu128 || \
  uv pip install --python "$VENV_DIR/bin/python" torch torchvision

uv pip install --python "$VENV_DIR/bin/python" \
  "numpy<2" pillow opencv-python-headless matplotlib scipy tqdm gdown svgpathtools CairoSVG \
  beautifulsoup4 lxml pandas scikit-learn yacs "timm==0.6.13"

python - <<'PY'
import importlib
mods = ["torch", "torchvision", "cv2", "numpy", "PIL", "svgpathtools", "cairosvg", "sklearn", "yacs", "timm"]
for m in mods:
    mod = importlib.import_module(m)
    print(m, getattr(mod, "__version__", "ok"))
print("torch cuda available outside Slurm:", __import__("torch").cuda.is_available())
PY

echo "[bootstrap] done"
