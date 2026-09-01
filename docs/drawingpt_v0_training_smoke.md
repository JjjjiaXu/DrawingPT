# DrawingPT v0 最小训练闭环 smoke

生成日期：2026-09-01

## 一句话结论

DrawingPT v0 已经从“数据资产冻结”推进到“最小训练闭环跑通”：Dataset 可以读取 FloorPlanCAD token manifest 和低标注清单，masked primitive modeling 与 semantic primitive classification 都能正常前向、反向、更新并保存 checkpoint。

这不是正式实验结果，只是证明训练链路已经通了；同时它暴露了一个后续必须解决的问题：语义分类短跑会偏向高频类别，尤其是 background/wall/sink。

## 新增代码

| 文件 | 作用 |
|---|---|
| `scripts/drawingpt_v0_dataset.py` | 读取 FloorPlanCAD SVG、token manifest、label fraction 清单，输出 fixed-size primitive window |
| `scripts/train_masked_primitive.py` | 最小 Transformer encoder，自监督预测被 mask 的 primitive type 和 geometry feature |
| `scripts/train_semantic_primitive.py` | 最小 semantic head，做 0/1..35 primitive 语义分类 smoke，默认只在前景语义类上计算 loss |
| `scripts/server/drawingpt_v0_masked_smoke.sbatch` | 服务器低资源 GPU smoke 提交脚本，默认 1 GPU、30 分钟 |
| `scripts/server/drawingpt_v0_pretrain_short.sbatch` | 2048-token masked pretrain 短跑脚本 |
| `scripts/server/drawingpt_v0_semantic_scratch_smoke.sbatch` | 1% 标注 semantic scratch smoke 脚本 |
| `scripts/server/drawingpt_v0_semantic_pretrained_smoke.sbatch` | 加载自监督 checkpoint 后的 1% 标注 semantic fine-tune smoke 脚本 |
| `scripts/server/drawingpt_v0_semantic_weighted_smoke.sbatch` | inverse-sqrt class weighting 的 1% 标注 semantic smoke 脚本 |

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

## 2048-token pretrain short

服务器上新增完成 2048-token window 的 masked primitive pretrain 短跑。

| 项目 | 数值 |
|---|---|
| job id | 1405 |
| device | CUDA |
| torch | 2.11.0+cu128 |
| window size | 2048 |
| batch size | 2 |
| steps | 100 |
| runtime | 11.141 秒 |
| loss | 1.642630 → 0.107217 |
| checkpoint SHA256 | `ceb52ad65ae94c69a9b0409fb2404b875f33a2de6975d5190862efb09d50317e` |

这一步把 prereg 里设想的 2048-token window 训练入口跑通了，说明不是只能在小 window 上 smoke。

## 语义分类 smoke：发现并修正 background shortcut

第一个语义 scratch 诊断把 `0=background/unlabeled` 也纳入 loss，结果出现误导性现象：

| job | loss target | all accuracy | foreground accuracy | macro F1 foreground | 结论 |
|---:|---|---:|---:|---:|---|
| 1406 | all valid tokens including background | 0.521718 | 0.000000 | 0.000000 | 模型学成了 background shortcut，不能当有效结果 |
| 1407 | foreground semantic IDs 1..35 | 0.162173 | 0.339074 | 0.016764 | 不再全猜 background，但短跑偏向 wall/sink |
| 1409 | pretrained + foreground semantic IDs 1..35 | 0.163208 | 0.341238 | 0.017662 | pretrained 略高于 scratch，但差异太小，不能宣称有效 |
| 1411 | inverse-sqrt weighted + foreground semantic IDs 1..35 | 0.120133 | 0.251176 | 0.020923 | scratch macro F1 略升，但 foreground accuracy 下降 |
| 1412 | pretrained + inverse-sqrt weighted + foreground semantic IDs 1..35 | 0.140208 | 0.293149 | 0.014104 | weighted pretrained 没有优于 weighted scratch |

pretrained job 加载了自监督 checkpoint 中 30 个 encoder 参数键，跳过 4 个 pretrain head 参数键，并重新初始化 semantic head。

这组结果的真正价值不是“模型已经好了”，而是把下一步问题钉清楚了：

- 如果 class 0 参与 loss，overall accuracy 会虚高，但 foreground 完全没学到；
- 改成 foreground-only loss 后，模型能开始预测前景，但 100 step / 1% 标注下主要塌到高频 `wall` 和少量 `sink`；
- inverse-sqrt class weighting 能把预测从纯高频类里稍微打散，scratch macro F1 从 0.0168 到 0.0209，但还没解决 rare class；
- 下一个技术门禁应是 class-aware window sampling 或 focal loss，再谈 1%/5%/10% label-efficiency curve。

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

建议接下来不要马上大规模跑，而是先过类别均衡门禁：

1. 在 semantic loader 中加入 class-aware window sampling，避免每个 batch 仍被 wall/window 等高频窗口主导；
2. 对同一 1% seed0304 跑 scratch vs pretrained，检查 foreground macro F1 是否明显高于当前 0.0209；
3. 如果 1% 不再塌到 wall/window/sink，再扩到 5%、10% 和 3 个 seed；
4. semantic prediction 稳定后，再把预测结果转成 pseudo-BoQ，计算 count MAE / length relative error。

组会口径：

> DrawingPT v0 已经跑通最小训练闭环。现在不是只有设计草案了，Dataset 能读取低标注清单和 primitive window，masked primitive modeling 与 semantic classification 都可以正常前向/反向/保存 checkpoint。服务器上 2048-token pretrain 和 1% semantic scratch/pretrained/weighted smoke 都已完成；目前发现的主要问题不是能不能跑，而是语义短跑会偏向 wall/window/sink 高频类。class weighting 有一点改善，但还不够，下一步要做 class-aware window sampling。
