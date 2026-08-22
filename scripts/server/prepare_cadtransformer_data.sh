#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-$HOME/data/users/$USER/DrawingPT}"
SCRATCH_ROOT="${SCRATCH_ROOT:-$HOME/data/scratch/$USER/DrawingPT}"
VENV_DIR="${VENV_DIR:-$SCRATCH_ROOT/.venv-cadtransformer}"
RAW_DIR="${RAW_DIR:-$PROJECT_ROOT/data/raw/FloorPlanCAD}"
PROCESSED_DIR="${PROCESSED_DIR:-$SCRATCH_ROOT/processed/FloorPlanCAD}"
THREADS="${THREADS:-4}"
SCALE="${SCALE:-7}"

source "$VENV_DIR/bin/activate"
cd "$PROJECT_ROOT/third_party/CADTransformer"

echo "[data] raw=$RAW_DIR"
echo "[data] processed=$PROCESSED_DIR"
mkdir -p "$PROCESSED_DIR"

if [ ! -d "$RAW_DIR/train/train/svg_gt" ] || [ ! -d "$RAW_DIR/val/val/svg_gt" ] || [ ! -d "$RAW_DIR/test/test/svg_gt" ]; then
  echo "ERROR: FloorPlanCAD raw split directories not found under $RAW_DIR" >&2
  exit 1
fi

if [ ! -d "$PROCESSED_DIR/png/train" ] || [ -z "$(find "$PROCESSED_DIR/png/train" -name '*.png' -print -quit 2>/dev/null)" ]; then
  echo "[data] svg -> png and scaled copied svg"
  # The upstream release script writes generated svg/png folders under RAW_DIR
  # before we move them to scratch. If a previous run was interrupted, remove
  # only those generated folders and regenerate them from raw split/svg_gt.
  case "$RAW_DIR" in
    */FloorPlanCAD) ;;
    *)
      echo "ERROR: refusing to clean generated folders for unexpected RAW_DIR=$RAW_DIR" >&2
      exit 1
      ;;
  esac
  rm -rf "$RAW_DIR/svg" "$RAW_DIR/png"
  python preprocess/svg2png.py --data_save_dir "$RAW_DIR" --scale "$SCALE" --cvt_color --thread_num "$THREADS"
  # The release script writes processed svg/png back under data_save_dir. Move the generated copies to scratch.
  mkdir -p "$PROCESSED_DIR"
  if [ -d "$RAW_DIR/svg" ]; then mv "$RAW_DIR/svg" "$PROCESSED_DIR/svg"; fi
  if [ -d "$RAW_DIR/png" ]; then mv "$RAW_DIR/png" "$PROCESSED_DIR/png"; fi
else
  echo "[data] png already exists; skipping svg2png"
fi

mkdir -p "$PROCESSED_DIR/npy/train" "$PROCESSED_DIR/npy/val" "$PROCESSED_DIR/npy/test"

RESUME_INPUT_ROOT="$SCRATCH_ROOT/work/cadtransformer_missing_svg"
case "$RESUME_INPUT_ROOT" in
  "$SCRATCH_ROOT"/work/cadtransformer_missing_svg) ;;
  *)
    echo "ERROR: refusing to use unexpected resume input root: $RESUME_INPUT_ROOT" >&2
    exit 1
    ;;
esac

for split in train val test; do
  svg_count=$(find "$PROCESSED_DIR/svg/$split" -maxdepth 1 -name '*.svg' -type f 2>/dev/null | wc -l)
  npy_count=$(find "$PROCESSED_DIR/npy/$split" -maxdepth 1 -name '*.npy' -type f 2>/dev/null | wc -l)
  echo "[data] split=$split svg=$svg_count npy=$npy_count"

  if [ "$svg_count" -eq 0 ]; then
    echo "ERROR: no SVG files found for split=$split under $PROCESSED_DIR/svg/$split" >&2
    exit 1
  fi

  if [ "$npy_count" -lt "$svg_count" ]; then
    missing_dir="$RESUME_INPUT_ROOT/$split"
    rm -rf "$missing_dir"
    mkdir -p "$missing_dir"
    missing_count=0
    for svg_path in "$PROCESSED_DIR/svg/$split"/*.svg; do
      [ -e "$svg_path" ] || continue
      base=$(basename "$svg_path" .svg)
      npy_path="$PROCESSED_DIR/npy/$split/$base.npy"
      if [ ! -s "$npy_path" ]; then
        ln -s "$svg_path" "$missing_dir/$(basename "$svg_path")"
        missing_count=$((missing_count + 1))
      fi
    done
    echo "[data] preprocess_svg $split missing=$missing_count"
    if [ "$missing_count" -eq 0 ]; then
      echo "[data] npy/$split count mismatch but no missing non-empty outputs were found; skipping"
      continue
    fi
    python preprocess/preprocess_svg.py \
      -i "$missing_dir" \
      -o "$PROCESSED_DIR/npy/$split" \
      --thread_num "$THREADS"
  else
    echo "[data] npy/$split complete; skipping"
  fi
done

echo "[data] summary"
find "$PROCESSED_DIR" -maxdepth 3 -type f | sed "s#^$PROCESSED_DIR/##" | awk -F. '{ext=$NF; count[ext]++} END {for (e in count) print e, count[e]}' | sort
