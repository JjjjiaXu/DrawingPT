# FloorPlanCAD 工程量 proxy 报告

生成日期：2026-09-01
脚本：`scripts/floorplancad_quantity_proxy.py`
数据：FloorPlanCAD 公开 11,602 SVG baseline split。

## 一句话结论

FloorPlanCAD 可以支持一个“工程量 proxy”任务：从 SVG 标注里统计门窗、墙体、栏杆、楼梯、电梯、车位和厨卫设备等可计量对象。但这些数字仍是 **图纸语义/几何 proxy**，不是带真实单位、材料、定额和单价的工程造价。

## 全局文件级统计

| 指标 | 数值 |
|---|---:|
| SVG 文件数 | 11,602 |
| train / val / test | 6,965 / 810 / 3,827 |
| 每图核心语义元素中位数 | 186 |
| 每图核心语义元素均值 | 373.07 |
| 每图核心非负实例数中位数 | 7 |
| 每图核心非负实例数均值 | 12.37 |
| 每图核心近似 SVG 长度中位数 | 1,812 |
| 每图核心近似 SVG 长度均值 | 2,158.85 |

这里的“核心”指工程量相关类：墙体/围护、开口/门窗、垂直交通、车位、厨卫/设备点位、柜体/固定家具。

## 按角色聚合

| split | 角色 | 语义元素数 | 非负实例数 | 覆盖文件数 | 覆盖比例 | 近似 SVG 长度 |
|---|---|---:|---:|---:|---:|---:|
| train | 墙体/围护 | 991,664 | 0 | 6,721 | 96.50% | 9,814,343 |
| train | 开口/门窗 | 421,488 | 50,996 | 5,404 | 77.59% | 2,520,288 |
| train | 垂直交通 | 212,847 | 7,904 | 3,326 | 47.75% | 2,439,014 |
| train | 厨卫/设备点位 | 720,068 | 20,940 | 2,363 | 33.93% | 0 |
| train | 柜体/固定家具 | 187,546 | 7,278 | 865 | 12.42% | 0 |
| train | 车位 | 148,711 | 0 | 637 | 9.15% | 992,790 |
| val | 墙体/围护 | 111,483 | 0 | 786 | 97.04% | 1,175,971 |
| val | 开口/门窗 | 47,427 | 5,905 | 605 | 74.69% | 291,937 |
| test | 墙体/围护 | 445,312 | 0 | 3,599 | 94.04% | 4,338,614 |
| test | 开口/门窗 | 218,033 | 27,637 | 2,933 | 76.64% | 1,354,895 |

注意：墙体、幕墙、栏杆、车位等类别大量使用 `instanceId=-1`，所以它们更适合用元素数和长度 proxy，而不是直接数 instance。

## 最适合做第一版工程量 proxy 的类别

| 类别 | 为什么适合 |
|---|---|
| single door / double door / sliding door | 有非负 instance，可以做门数量统计 |
| window / bay window / blind window | 有非负 instance，可以做窗数量统计 |
| wall / curtain wall / railing | instance 不可靠，但长度 proxy 很有工程含义 |
| stairs / elevator / escalator | 非负 instance 和覆盖文件都较多 |
| parking spot | instance 不可靠，但图元数量和长度 proxy 可作为平面布置指标 |
| sink / toilet / bath / washing machine | 可作为厨卫设备点位清单 proxy |

## 已补齐的每图 pseudo-BoQ 表

已经生成每张图一行的 pseudo-BoQ 表：

```text
reports/next_steps_2026-09-01/floorplancad_pseudo_boq_by_file.csv
```

文件行数：11,602；SHA256：

```text
0060106a229f87606d49f6b4e220ed3eee86bc9ec0f2e406cda945f52e014679
```

主要字段：

- `door_instance_count`
- `window_instance_count`
- `wall_length_proxy_units`
- `stairs_instance_count`
- `elevator_instance_count`
- `parking_spot_semantic_elements`
- `sanitary_fixture_instance_count`
- `cabinet_instance_count`

训练集汇总：

| proxy | train 汇总 |
|---|---:|
| 门 instance | 34,704 |
| 窗 instance | 15,376 |
| 墙体长度 proxy | 8,836,841.492 |
| 楼梯 instance | 4,345 |
| 电梯 instance | 3,206 |
| 车位 semantic primitive | 148,711 |
| 厨卫设备 instance | 16,722 |
| 柜体 instance | 7,278 |

这一步把原先“可以做”的 GT 工程量 proxy 表变成了实际资产。下一步等模型 prediction 导出后，用同一个脚本口径生成预测侧 pseudo-BoQ，再算误差。

## 可以继续做的实验

### 实验 1：预测结果工程量误差

当 CADTransformer 或 DrawingPT 输出 semantic prediction 后，把预测结果转成同样的 proxy 表，再和 GT 表比较：

- count MAE；
- count relative error；
- length proxy relative error；
- per-class error；
- per-building error。

这能把“识别指标”转成更接近造价任务的“工程量误差”。

### 实验 2：合成单价 demo

用人工单价表做演示：

```text
墙体长度 proxy × wall unit price
门数量 × door unit price
窗数量 × window unit price
楼梯数量 × stairs unit price
```

这个 demo 只能叫“合成造价演示”，不能叫真实造价模型。它的价值是证明链路可解释：每一项价格都能追溯到图纸对象。

## 重要 caveat

1. `approx_svg_length_units` 是 SVG 坐标单位，不是米。
2. 当前没有墙高、墙厚、材料、做法、楼层、地区单价和定额。
3. path arc 的长度是近似计算，不用于真实工程量结算。
4. FloorPlanCAD 是语义标注数据，不是完整 DWG/BIM 工程数据。
5. 当前 proxy 只能支持“图纸理解 → 工程量中间层”的研究叙事，不能直接支持“端到端真实造价”结论。

## 输出文件

可提交的 compact 表：

- `reports/next_steps_2026-09-01/floorplancad_quantity_proxy_by_class.csv`
- `reports/next_steps_2026-09-01/floorplancad_quantity_proxy_by_role.csv`
- `reports/next_steps_2026-09-01/floorplancad_pseudo_boq_by_file.csv`
- `reports/next_steps_2026-09-01/floorplancad_quantity_proxy_summary.json`

本地 audit 表：

- `outputs/reports/floorplancad_quantity_proxy_by_file.csv`
- `outputs/reports/floorplancad_pseudo_boq_by_file.csv`
