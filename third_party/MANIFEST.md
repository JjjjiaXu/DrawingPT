# Third-party baseline manifest

Fill this after cloning:

| Name | Repository | Local path | Commit | Notes |
|---|---|---|---|---|
| CADTransformer | https://github.com/VITA-Group/CADTransformer | `third_party/CADTransformer` | `4cf9375` | CVPR 2022; official implementation; needs FloorPlanCAD, HRNet-W48 pretrained checkpoint, PyTorch/CUDA. |
| SymPoint | https://github.com/nicehuster/SymPoint | `third_party/SymPoint` | `e3205a6` | ICLR 2024; point-based baseline; needs PyTorch, Detectron2, mmcv, custom pointops. |
| GAT-CADNet | https://github.com/Liberation-happy/GAT-CADNet | `third_party/GAT-CADNet` | `e840830` | Unofficial reproduction; simpler sanity baseline; README says Ubuntu22.04/Python3.11. |
