# FloorPlanCAD 低标注比例清单

生成日期：2026-09-01

这些文件用于 DrawingPT v0 的低标注 fine-tuning 实验。每个 `.txt` 文件是一组固定的 FloorPlanCAD train split SVG 相对路径；训练代码只应该在对应比例下读取这些 train 文件。`val` 仍用于模型选择，`test` 仍只用于最终评估。

## 采样规则

- 数据源：`data/raw/FloorPlanCAD/train/train/svg_gt/*.svg`
- 总 train 文件数：6,965
- seed：304、1004、2026
- 比例：1%、5%、10%、25%、50%、100%
- 数量：对 `N * fraction` 取 `ceil`
- 同一个 seed 下，小比例清单是大比例清单的前缀，方便做 label-efficiency curve。

| 比例 | 文件数 |
|---:|---:|
| 1% | 70 |
| 5% | 349 |
| 10% | 697 |
| 25% | 1,742 |
| 50% | 3,483 |
| 100% | 6,965 |

## 校验

主清单索引见：

- `configs/label_fractions/manifest.csv`
- `configs/label_fractions/summary.json`

当前 `manifest.csv` 的 SHA256：

```text
7c9e55fdf58d06d9eaf6eb8af51e92e15d9d417920083231ba1e152ec273f603
```

注意：这些清单只冻结“哪些文件被视作有标注”。它们还没有做 class-balance 约束；正式解释 rare class 结果前，需要再检查每个低标注子集的类别覆盖。
