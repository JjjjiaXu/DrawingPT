from __future__ import annotations

import importlib
import platform
import sys
from pathlib import Path


PACKAGES = [
    "ezdxf",
    "gdown",
    "lxml",
    "matplotlib",
    "numpy",
    "pandas",
    "PIL",
    "svgpathtools",
    "tqdm",
    "yaml",
]


def package_status(name: str) -> str:
    try:
        module = importlib.import_module(name)
    except Exception as exc:  # pragma: no cover - diagnostics only
        return f"missing ({exc.__class__.__name__}: {exc})"

    version = getattr(module, "__version__", None)
    if version is None and name == "PIL":
        version = getattr(module, "PILLOW_VERSION", None)
    return f"ok{f' {version}' if version else ''}"


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    print(f"Python: {sys.version.split()[0]}")
    print(f"Platform: {platform.platform()}")
    print(f"Project root: {root}")
    print()
    print("Packages:")
    for pkg in PACKAGES:
        print(f"  {pkg:12s} {package_status(pkg)}")

    try:
        import torch
    except Exception as exc:
        print(f"  torch        optional missing ({exc.__class__.__name__}: {exc})")
    else:
        cuda = torch.cuda.is_available()
        device_count = torch.cuda.device_count() if cuda else 0
        print(f"  torch        ok {torch.__version__}; cuda={cuda}; devices={device_count}")

    print()
    print("Expected local paths:")
    for rel in [
        "data/raw/FloorPlanCAD",
        "data/processed/FloorPlanCAD",
        "third_party/CADTransformer",
        "third_party/SymPoint",
        "third_party/GAT-CADNet",
    ]:
        path = root / rel
        print(f"  {rel:36s} {'exists' if path.exists() else 'missing'}")


if __name__ == "__main__":
    main()

