# DrawingPT v0 正式 controlled run 计划

生成日期：2026-09-01

## 目标

把当前 100-step smoke 推进到一组更像正式实验的低标注 controlled run：固定 1% seed0304、2048-token window、class-aware sampler、inverse-sqrt class weighting，对比 scratch 和 pretrained 初始化。

这组实验的目的不是刷 SOTA，而是回答一个更基础的问题：

> 在类别长尾已经暴露的情况下，class-aware sampler + 自监督初始化是否能比当前 100-step smoke 更稳定地提升 foreground macro F1？

## 实验设置

| 项目 | 设置 |
|---|---|
| 数据 | FloorPlanCAD 公开 11,602 张 baseline split |
| train label-list | `configs/label_fractions/floorplancad_train_seed0304_001pct.txt` |
| 训练窗口 | 1% train label-list 下的 2048-token windows |
| 验证集 | val split full windows，默认不截断 |
| 对照 A | scratch + class-aware sampler + inverse-sqrt class weighting |
| 对照 B | pretrained + class-aware sampler + inverse-sqrt class weighting |
| pretrained checkpoint | `outputs/checkpoints/drawingpt_v0_pretrain_2048_seed0304_short.pt` |
| steps | 1000 |
| GPU | 1 张 |
| Slurm 策略 | scratch 先跑，pretrained 通过 `afterok` 依赖串行排队 |

## 主要指标

| 指标 | 解释 |
|---|---|
| foreground accuracy | 只看 semanticId 1..35 的 token accuracy |
| foreground macro F1 | 每个有 support 的前景类先算 F1，再做平均 |
| rare macro F1 | 预先定义 rare classes 的 macro F1 |
| per-class support | 验证每个类是否真的在 validation subset 中出现 |
| dominant predictions | 检查模型是否仍塌到 wall/window/sink 或某个新高频类 |

## 提交命令

在服务器项目目录下运行：

```bash
git pull
bash scripts/server/submit_drawingpt_v0_classaware_controlled_pair.sh
```

默认会生成两个 summary：

```text
outputs/reports/drawingpt_v0_semantic_classaware_weighted_scratch_1pct_seed0304_1000step_summary.json
outputs/reports/drawingpt_v0_semantic_classaware_weighted_pretrained_1pct_seed0304_1000step_summary.json
```

跑完后可用：

```bash
python scripts/summarize_semantic_controlled_results.py \
  outputs/reports/drawingpt_v0_semantic_classaware_weighted_scratch_1pct_seed0304_1000step_summary.json \
  outputs/reports/drawingpt_v0_semantic_classaware_weighted_pretrained_1pct_seed0304_1000step_summary.json
```

## 汇报边界

- 如果作业已提交但未完成：汇报为 controlled run 已排队/运行，不能写成已完成结果。
- 如果只完成 scratch、pretrained 还没跑：只汇报 scratch 结果，pretrained 写成依赖队列。
- 如果 macro F1 不升：重点讲 dominant predictions 和 rare-class support，说明下一步需要更强 sampler 或 focal loss。
- 如果 pretrained 优于 scratch：再扩到 5%、10% 和多个 seed，才形成低标注曲线结论。
