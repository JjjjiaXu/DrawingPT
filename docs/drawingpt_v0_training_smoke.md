# DrawingPT v0 最小训练闭环 smoke

生成日期：2026-09-01

## 一句话结论

DrawingPT v0 已经从“数据资产冻结”推进到“最小训练闭环跑通”：Dataset 可以读取 FloorPlanCAD token manifest 和低标注清单，masked primitive modeling 的 5-step CPU smoke 能正常前向、反向、更新并保存 checkpoint。

这不是正式实验结果，只是证明训练链路已经通了。

## 新增代码

| 文件 | 作用 |
|---|---|
| `scripts/drawingpt_v0_dataset.py` | 读取 FloorPlanCAD SVG、token manifest、label fraction 清单，输出 fixed-size primitive window |
| `scripts/train_masked_primitive.py` | 最小 Transformer encoder，自监督预测被 mask 的 primitive type 和 geometry feature |
| `scripts/server/drawingpt_v0_masked_smoke.sbatch` | 服务器低资源 GPU smoke 提交脚本，默认 1 GPU、30 分钟 |

Dataset 同时兼容两种 FloorPlanCAD SVG 布局：

- 本地 raw：`FloorPlanCAD/train/train/svg_gt/*.svg`
- 服务器 processed：`FloorPlanCAD/svg/train/*.svg`

## Dataset smoke

命令：

```powershell
python scripts\drawingpt_v0_dataset.py `
  --root data\raw\FloorPlanCAD `
  --manifest reports\next_steps_2026-09-01\floorplancad_token_manifest_by_file.csv `
  --split train `
  --label-list configs\label_fractions\floorplancad_train_seed0304_001pct.txt `
  --window-size 512 `
  --limit-windows 8 `
  --inspect-windows 8 `
  --summary-out reports\next_steps_2026-09-01\drawingpt_v0_dataset_smoke_summary.json
```

结果：

| 项目 | 数值 |
|---|---:|
| inspected windows | 8 |
| feature dim | 13 |
| finite feature windows | 8 / 8 |
| valid tokens/window mean | 430.12 |
| valid tokens/window median | 512 |

说明：这证明 label-list、manifest、SVG 解析、window padding、feature 数值稳定性都能走通。

## Masked primitive modeling smoke

命令：

```powershell
python scripts\train_masked_primitive.py `
  --root data\raw\FloorPlanCAD `
  --manifest reports\next_steps_2026-09-01\floorplancad_token_manifest_by_file.csv `
  --split train `
  --label-list configs\label_fractions\floorplancad_train_seed0304_001pct.txt `
  --window-size 128 `
  --limit-windows 16 `
  --batch-size 2 `
  --steps 5 `
  --hidden-dim 32 `
  --layers 1 `
  --heads 4 `
  --mask-ratio 0.30 `
  --seed 304 `
  --device cpu `
  --summary-out reports\next_steps_2026-09-01\drawingpt_v0_masked_smoke_summary.json `
  --checkpoint-out outputs\checkpoints\drawingpt_v0_masked_smoke.pt
```

结果：

| step | loss | type loss | feature loss | masked tokens |
|---:|---:|---:|---:|---:|
| 1 | 1.786738 | 1.462767 | 0.323970 | 74 |
| 2 | 1.642764 | 1.303607 | 0.339157 | 86 |
| 3 | 1.520735 | 1.192848 | 0.327887 | 68 |
| 4 | 1.362035 | 1.056409 | 0.305626 | 65 |
| 5 | 1.189145 | 0.895564 | 0.293581 | 33 |

运行环境：

| 项目 | 数值 |
|---|---|
| device | CPU |
| torch | 1.13.1+cpu |
| runtime | 0.43 秒 |
| checkpoint | `outputs/checkpoints/drawingpt_v0_masked_smoke.pt` |
| checkpoint SHA256 | `fe2a8618e4e44435de85f5d1559d9e41f0c3a49d6a435dc336e031da9a75d416` |

注意：5 step loss 下降只能说明训练闭环没有明显 bug，不能说明模型有效。

## 服务器 GPU smoke

服务器上已完成 100-step GPU smoke。

| 项目 | 数值 |
|---|---|
| job id | 1404 |
| remote repo | 隔离 DrawingPT worktree，绝对用户路径不写入 Git |
| data root | 服务器 processed FloorPlanCAD SVG 布局 |
| device | CUDA / NVIDIA GeForce RTX 5090 |
| torch | 2.11.0+cu128 |
| dataset windows | 188 |
| window size | 512 |
| batch size | 8 |
| steps | 100 |
| runtime | 57.583 秒 |
| loss | 2.643315 → 0.103848 |
| checkpoint | `outputs/checkpoints/drawingpt_v0_masked_smoke.pt` |
| checkpoint SHA256 | `10adabe1b4f23f160d1488360bd406e9cd35d8074f1f9fe24ad7a50008077a62` |

日志：

- `logs/slurm/drawingpt-v0-smoke-1404.out`
- `logs/slurm/drawingpt-v0-smoke-1404.err`

这一步证明：服务器 Slurm、CUDA、processed SVG 布局、Dataset、mask、Transformer forward/backward、optimizer 和 checkpoint 保存都能跑通。

## 当前模型定义

最小模型：

- type embedding；
- geometry/style feature projection；
- position embedding；
- Transformer encoder；
- type prediction head；
- geometry feature regression head。

自监督目标：

1. 随机 mask 30% valid primitive；
2. 被 mask 的 primitive type 替换为 `[MASK]`；
3. 被 mask 的 geometry/style feature 置零；
4. 模型同时预测原 type 和原 feature；
5. loss = cross entropy(type) + smooth L1(feature)。

## 下一道门禁

建议接下来不要马上大规模跑，而是按下面顺序推进：

1. 改成 2048-token window，跑 train 1% 的 short epoch；
2. 增加 semantic fine-tuning head，先做 1% seed0304 scratch baseline；
3. 用同一模型加载 smoke pretrain checkpoint，再跑 1% fine-tune；
4. 如果 1% 能出可比数字，再扩到 5%、10% 和 3 个 seed。

组会口径：

> DrawingPT v0 已经跑通最小训练闭环。现在不是只有设计草案了，Dataset 能读取低标注清单和 primitive window，masked primitive modeling 可以正常前向/反向/保存 checkpoint。服务器 100-step GPU smoke 也已经完成，下一步是 2048-token window short epoch 和 1% 低标注 fine-tuning 对照。
