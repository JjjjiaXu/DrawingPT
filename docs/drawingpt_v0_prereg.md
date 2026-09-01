# DrawingPT v0 正式 prereg

生成日期：2026-09-01
状态：实验前协议草案，用于组会确认后冻结。
范围：公开 FloorPlanCAD 11,602 SVG baseline split；不使用私有图纸、服务器账号信息、真实项目造价数据。

## 1. 研究问题

DrawingPT v0 要回答的最小问题是：

> 2D CAD/SVG/DXF 的矢量 primitive 自监督预训练，能否在 FloorPlanCAD 少标注 fine-tuning 场景下带来稳定收益？

这版暂时不承诺直接输出真实工程造价。工程造价只作为应用牵引；主线任务仍是图纸表示学习。

## 2. 主要假设

### H1：自监督预训练提升低标注识别

在 1%、5%、10% 标注比例下，DrawingPT v0 预训练后 fine-tune 相比同结构从零训练：

- 绝对 F1 或 PQ 提升 ≥ 0.02；或
- relative improvement ≥ 5%。

如果没有达到，需要诊断 token 化、预训练目标、数据规模和 downstream 对齐问题。

### H2：矢量 token 比纯 raster 更适合低标注

在相近参数量和训练预算下，primitive token encoder 应该在门窗、墙体、楼梯、车位等结构化类别上优于仅图像输入的小模型，尤其是 rare class 和低标注设置。

### H3：工程量 proxy 能体现表示学习价值

如果 semantic/instance 预测更准，那么由预测结果生成的门窗数量、墙体长度 proxy、楼梯/电梯/车位统计也应该更接近 GT 标注。

## 3. 数据协议

| 用途 | 数据 | 约束 |
|---|---|---|
| 自监督预训练 | FloorPlanCAD train split，无标注或仅用图元结构 | 不使用 val/test |
| 模型选择 | FloorPlanCAD val split | 不反复调到 test |
| 最终评估 | FloorPlanCAD test split | 只在方案冻结后使用 |
| 工程量 proxy | FloorPlanCAD GT semantic/instance 标注 | 仅作为 proxy，不声称真实工程量 |
| 额外公开 DXF | 暂不纳入 v0 主实验 | 若加入需另写 prereg |

当前 train split 有 6,965 张 SVG、7,764,513 个 raw primitives。按 2,048 primitive/window 估计约 8,568 个窗口；每个窗口 4-8 种 mask/augmentation 时，等效自监督样本约 3.4 万到 6.9 万。

## 4. Token 化方案

v0 每个 primitive 是一个 token。

| 字段组 | 内容 |
|---|---|
| primitive type | `path` / `circle` / `ellipse` |
| geometry | bbox、中心点、端点/采样点、长度 proxy、面积 proxy、角度 proxy |
| style/layer | stroke/fill、stroke width、颜色、group/layer 弱信息 |
| relation | 空间邻近、bbox overlap、同 group、近邻图 |
| optional text | FloorPlanCAD v0 暂不作为主输入，DXF 扩展时再启用 |

长图纸按 primitive 数或空间窗口切分，默认窗口大小 2,048 primitives；长尾图纸需要记录被切成几个窗口。

## 5. 模型和训练

最小模型：

- geometry MLP + type embedding + style embedding；
- 4-6 层 Transformer encoder；
- hidden dim 128 或 256；
- 4 attention heads；
- 参数量目标 1M-5M；
- 训练时固定 seed，至少使用 3 个 seed：304、1004、2026。

第一版不做大模型堆参数，优先证明路线是否有效。

## 6. 自监督目标

优先级：

1. **Masked primitive modeling**：遮住 primitive type / geometry / style，预测被遮内容。
2. **Vector-to-raster alignment**：让 vector window 表示对齐局部 raster crop 或 occupancy map。
3. **Text-geometry binding**：有可用文字/尺寸标注后再加入。

v0 首先只冻结 masked primitive modeling；其他目标作为 ablation 或 v1 扩展。

## 7. 下游任务和指标

### 主任务

- primitive semantic classification；
- 如果 PQ 链路打通，再加入 panoptic symbol spotting。

### 辅助任务

- 门/窗/楼梯/电梯/车位 instance count；
- 墙体/幕墙/栏杆 SVG 坐标长度 proxy；
- 工程量 proxy 表误差。

### 指标

| 指标 | 用途 |
|---|---|
| micro F1 | 总体 semantic 识别 |
| macro F1 | 类别均衡表现 |
| rare-class F1 | 小类鲁棒性 |
| PQ/SQ/RQ | paper-faithful symbol spotting，取决于评估链路是否恢复 |
| count MAE / relative error | 工程量 proxy |
| length proxy relative error | 墙体/幕墙/栏杆等线性对象 |

## 8. Baseline

必须比较：

1. 同结构从零训练；
2. CADTransformer 当前 semantic baseline；
3. 如果可行，CADTransformer paper-faithful PQ/SQ/RQ；
4. hand-crafted feature + shallow classifier，用作低成本 sanity baseline。

所有 baseline 要记录：

- 数据版本；
- split；
- seed；
- epoch；
- image size / primitive window size；
- batch size；
- GPU 型号和 runtime；
- checkpoint/hash；
- 是否使用 `npy_rgb` 或额外特征。

## 9. Label fractions

标注比例：

- 1%；
- 5%；
- 10%；
- 25%；
- 50%；
- 100%。

每个比例用固定 seed 从 train split 采样。采样后记录文件列表 hash，避免后续“换了一批样本”导致不可比。

## 10. 成功与失败判据

### 成功

低标注 1%-10% 区间至少满足一个：

- 绝对 F1/PQ 提升超过 0.02；
- relative improvement 超过 5%；
- rare-class macro F1 有稳定提升，且不是单个 seed 偶然。

### 失败但有价值

如果总体指标没提升，但工程量 proxy 明显改善，可以说明 primitive 表示对“可计量对象”更有帮助。

### 失败诊断

按顺序检查：

1. token 是否过粗，path 内部几何丢失；
2. masked objective 是否太容易；
3. train-only 自监督语料是否太小；
4. 下游模型是否过弱或过强；
5. label fraction 采样是否类别失衡；
6. CADTransformer baseline 是否未对齐。

## 11. 汇报口径

组会上可以这样说：

> 下一阶段我把 DrawingPT v0 冻结成一个低标注表示学习实验：只用 FloorPlanCAD train split 做 primitive-level 自监督预训练，再在 1%、5%、10%、25%、50%、100% 标注比例上 fine-tune，并和从零训练、CADTransformer semantic baseline 比较。工程造价方向暂时不直接预测总价，而是用门窗计数、墙体长度、楼梯/电梯/车位统计作为 quantity-takeoff proxy，证明图纸表示能产生可计量中间层。
