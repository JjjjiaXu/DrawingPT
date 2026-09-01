# CADTransformer PQ/SQ/RQ 评估门禁记录

生成日期：2026-09-01

## 当前结论

CADTransformer 的训练链路已经跑通，但 **PQ/SQ/RQ 还没有完成**。原因不是 job 969 训练失败，而是当前公开 release 和本地/服务器代码路径里缺少完整的 panoptic evaluation 产物链路：

1. 官方 README 提到 `scripts/evaluate_pq.py`，但当前 `third_party/CADTransformer/scripts/` 下没有该文件。
2. 当前 `train_cad_ddp.py --val_only/--test_only` 只会调用 `eval.py::do_eval` 输出 primitive-level Total FG Precision/Recall/F1，不会保存 `npy_pred` 或 `svg_pred`。
3. 当前 release 模型 `models/model.py` 只返回 semantic logits；代码中虽有 `get_pred_instance(...)` helper，但需要的 offset/instance prediction 在当前训练入口里没有接上。
4. 服务器只读检查显示：job 969 的 `best_model.pth`、`last_model.pth` 和日志仍在，但没有发现 `*pred*` 预测目录。

因此，现阶段不能把 `0.827501` 当成 CADTransformer 论文的 PQ，也不能与论文 Table 1 直接相减。

## 已确认资产状态

| 项目 | 状态 |
|---|---|
| CADTransformer smoke checkpoint | 已存在 |
| CADTransformer full-data conservative checkpoint | 已存在 |
| processed train / val / test NPY | 6965 / 810 / 3827 |
| `scripts/evaluate_pq.py` | 当前 release 缺失 |
| `npy_pred` / `svg_pred` | 当前未产出 |
| 当前可直接得到的指标 | Total FG Precision / Recall / F1 |
| 论文主指标 | PQ / SQ / RQ |

## 和论文指标的关系

CADTransformer 原论文报告的是 panoptic symbol spotting：

| 指标 | 论文 CADTransformer | 论文 CADTransformer + Random Layer | 当前 job 969 |
|---|---:|---:|---:|
| PQ | 0.6732 | 0.6894 | 未产出 |
| SQ | 0.8754 | 0.8832 | 未产出 |
| RQ | 0.7226 | 0.7333 | 未产出 |
| Total FG F1 | 论文未报告 | 论文未报告 | 0.827501 |

当前能汇报的严谨说法是：

> CADTransformer 已经完成保守 full-data baseline，验证集 Total FG F1 为 0.827501；但 release 中缺少 README 所述的 PQ 评估脚本和预测导出链路，因此 paper-faithful PQ/SQ/RQ 仍是未过门禁项。

## 下一步补救方案

### 方案 A：找回官方评估脚本和 prediction export

优先级最高，最 paper-faithful。

需要解决：

- 找到官方 `scripts/evaluate_pq.py`；
- 找到或恢复 `raw_pred_dir → svg_pred_dir` 的转换步骤；
- 确认实例预测是来自 offset head、聚类，还是其他 symbol spotting head；
- 用同一套 val/test split 重新跑 PQ/SQ/RQ。

风险：官方 release 可能确实不完整，需要联系作者或从历史 commit/issue 中追溯。

### 方案 B：实现一个“透明但非官方”的 PQ proxy

如果官方脚本找不到，可以基于 release 中已有的 `utils/utils_dataset.py` 自行实现一个透明版本：

1. 先让模型在 val/test 上输出每个 primitive 的 semantic prediction；
2. 用邻接关系或几何连通性把同类 primitive 聚成实例；
3. 把预测实例写回 SVG；
4. 用长度加权 IoU 计算 TP/FP/FN；
5. 汇报 PQ/SQ/RQ，并明确它是 re-implemented proxy，不是官方脚本复现。

风险：这会引入新的算法假设，不能直接声称与论文 Table 1 完全同口径。

### 方案 C：先把 CADTransformer 定位为 semantic baseline

如果短期目标是推进 DrawingPT v0，可以先把 CADTransformer 的当前结果定位为 semantic primitive baseline，后续 DrawingPT 先比较：

- primitive-level micro F1；
- macro F1；
- rare-class F1；
- low-label fine-tuning curve。

同时保留 PQ/SQ/RQ 作为 paper-faithful 门禁，不把它混进当前结果。

## 建议决策

下次组会建议向老板确认一个选择：

> 我们是否必须严格复现 CADTransformer 的 PQ/SQ/RQ？如果必须，我下一步优先找回官方 evaluation/export 代码；如果允许先推进 DrawingPT v0，则先把 CADTransformer 作为 semantic baseline，同时单独记录 PQ 门禁未过。

我的建议是：**先推进 DrawingPT v0 的低标注曲线，同时并行追官方 PQ 评估链路**。不要为了复刻缺失脚本卡住所有后续工作。

## 可执行检查命令

服务器上可运行：

```bash
bash scripts/server/cadtransformer_pq_readiness.sh
```

这个脚本只做只读检查，不占 GPU，用于确认：

- `evaluate_pq.py` 是否存在；
- checkpoint 和日志是否存在；
- processed split 数量是否完整；
- prediction 目录是否已经生成。

## 来源

- CADTransformer 官方 README：https://github.com/VITA-Group/CADTransformer
- CADTransformer issue #31：https://github.com/VITA-Group/CADTransformer/issues/31
