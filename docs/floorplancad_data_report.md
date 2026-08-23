# FloorPlanCAD 数据报告

生成日期：2026-08-15
更新日期：2026-08-23

## 1. 下载状态

当前本地使用的是 CADTransformer / SymPoint / GAT-CADNet 公开脚本可直接使用的 FloorPlanCAD 11,602 张版本。

| split | SVG 文件数 | zip 大小 |
|---|---:|---:|
| train | 6,965 | 84.9 MB |
| val | 810 | 10.2 MB |
| test | 3,827 | 40.4 MB |
| total | 11,602 | 135.5 MB |

注意：FloorPlanCAD 官网后续提到过 15,663 张更新版。本轮 baseline 为了和公开复现脚本对齐，使用的是 11,602 张版本；如果切换数据版本，所有 baseline 都要一起切换并重新冻结 hash。

## 2. 文件结构

每个 zip 解压后是嵌套 split 目录：

```text
data/raw/FloorPlanCAD/
  train/train/svg_gt/*.svg
  val/val/svg_gt/*.svg
  test/test/svg_gt/*.svg
```

## 3. SVG 标注字段

SVG 图元上主要使用这些字段：

- `semanticId`：语义类别 id。
- `instanceId`：对象实例 id；`-1` 出现在 stuff/background-like 图元上。
- 几何字段：例如 `d`、`cx`、`cy`、`r`、`rx`、`ry`。
- 绘图样式字段：例如 `stroke`、`fill`、`stroke-width`。

本轮样本和全量统计中实际出现的 raw SVG primitive tag 主要是 `path`、`circle`、`ellipse`。这说明 FloorPlanCAD 是 SVG 矢量标注，但不是完整 DWG-native 结构：目前没有在这一版本里观察到可直接复用的 DWG block reference 层级。

## 4. 图元类型与数量分布

完整统计已补齐在 [floorplancad_distribution_report.md](floorplancad_distribution_report.md)。核心结论如下：

| 指标 | 数值 |
|---|---:|
| SVG 文件总数 | 11,602 |
| raw SVG primitive 总数 | 12,621,288 |
| 单图 primitive 中位数 | 544 |
| 单图 primitive 均值 | 1,087.85 |
| 单图 primitive p95 | 3,541 |
| 单图 primitive 最大值 | 53,919 |
| 带 `semanticId` 的元素总数 | 5,828,994 |

| SVG tag | 数量 | 占 raw primitive 比例 |
|---|---:|---:|
| path | 12,454,181 | 98.68% |
| circle | 157,009 | 1.24% |
| ellipse | 10,098 | 0.08% |

## 5. 每 split 统计

| split | 文件数 | raw primitive 总数 | 单图中位数 | 单图均值 | 单图最大值 | instance 均值 |
|---|---:|---:|---:|---:|---:|---:|
| train | 6,965 | 7,764,513 | 540 | 1,114.79 | 32,416 | 14.93 |
| val | 810 | 904,517 | 571 | 1,116.69 | 53,919 | 14.76 |
| test | 3,827 | 3,952,258 | 551 | 1,032.73 | 27,993 | 14.28 |

## 6. 语义类别分布

全量 train+val+test 中 35 类均出现，但分布高度不均衡：

- 最大类：`wall`，1,362,387 个带 `semanticId` 元素，占 23.37%。
- 其次：`bed`、`row chairs`、`sink`、`toilet`、`parking spot`。
- 极少类：`rolling door` 只有 98 个，`revolving door` 只有 1,036 个。
- val split 只覆盖 33/35 类，缺少极少见的 `revolving door` 和 `rolling door`。

这会影响后续实验设计：少样本设置、低标注比例实验和 small-val 指标都要特别警惕 rare class 方差，不能只看总体 F1。

## 7. 生成产物

本地原始统计产物位于 `outputs/reports/`，不提交到 GitHub：

- `floorplancad_scan_all.json`
- `floorplancad_train_stats.json`
- `floorplancad_val_stats.json`
- `floorplancad_test_stats.json`
- `floorplancad_*_file_stats.csv`

可提交的公开汇总产物：

- `docs/floorplancad_distribution_report.md`
- `reports/group_meeting_2026-08-18/floorplancad_tag_distribution.csv`
- `reports/group_meeting_2026-08-18/floorplancad_primitive_count_bins.csv`
- `reports/group_meeting_2026-08-18/floorplancad_semantic_distribution.csv`
