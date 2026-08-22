# CADTransformer conservative baseline run

## Date

Submitted 2026-08-18; completed 2026-08-19.

## Git commit

Local code state at submission: `5b545dc` (`Use normal QoS for conservative CADTransformer training`).

## Dataset version and split

FloorPlanCAD public 11,602-file baseline version:

- train: 6,965 SVG/PNG/NPY files; CADTransformer training filter kept 6,962
- val: 810
- test: 3,827

This is the version distributed through the public Google Drive IDs used by CADTransformer/SymPoint/GAT-CADNet, not the later 15,663-file website update.

## Hardware

YaoGroup Slurm server, one NVIDIA GeForce RTX 5090.

## Command

Submitted through `scripts/server/cadtransformer_train.sbatch`.

Key settings:

- epochs: 10
- image size: 384
- batch size: 1
- test batch size: 1
- workers: 0
- `rgb_dim=0`
- ViT online pretrained download disabled
- HRNet-W48 ImageNet checkpoint loaded from local file

## Runtime

Slurm job 969:

- state: `COMPLETED`
- exit code: `0:0`
- start: 2026-08-18 19:27:38 CST
- end: 2026-08-19 05:49:06 CST
- elapsed: 10:21:28

## Metrics

Validation metrics reported during training:

| Epoch marker | Total FG Precision | Total FG Recall | Total FG F1 |
|---|---:|---:|---:|
| Epoch 1 | 0.750009 | 0.713377 | 0.731184 |
| Epoch 2 | 0.793087 | 0.768256 | 0.780424 |
| Epoch 6 / Best Epoch 5 | 0.832457 | 0.822702 | 0.827501 |

Best model selected by validation Total FG F1:

`0.827501118183136`

## Frozen artifacts

| Artifact | Size | SHA-256 |
|---|---:|---|
| train log | 64,635 bytes | `fe88160d0a83a5f0aa9b517d39901ce186f2682d9577e9376a05753267c917a4` |
| best model | 1,085,562,061 bytes | `642da46678d5f8d76cdeb958df4e6c77d5d9e3462a640467d9d83c6283a35530` |
| last model | 1,085,562,061 bytes | `d29a4da0e541f1faf827fcdd41a612ba7ef1c0fa6ddbb69a1d7d9196db9df5db` |
| Slurm stdout | - | `61fe8aab418f82659b9b6dc4c2c18bdcb1b33b8d1946b5ffdf1d6e57d9f65d9f` |
| Slurm stderr | - | `200b84a634f5c01233da19b23986357b863ed74803bf017225dbe62f95675ac8` |

The large model files are intentionally not committed to git.

## Gap from reported paper number

Not computed yet. This run is not paper-faithful because it uses conservative settings (`img_size=384`, `rgb_dim=0`) rather than the original-style feature path.

## Failure notes

Earlier failures were environment/compatibility issues: missing `lxml`, CairoSVG CLI permission, NumPy alias removal, timm ViT API mismatch, optional `npy_rgb` missing, and Slurm QoS adjustment. The final job completed with Python multiprocessing/NCCL cleanup warnings, but Slurm exit code was `0:0` and both best/last checkpoints were saved.
