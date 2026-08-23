# DrawingPT v0 设计草案（一页纸）

生成日期：2026-08-23
用途：下次组会讨论，不作为最终实验协议。

## 1. 一句话假设

DrawingPT v0 的目标是验证一个最小命题：**2D 工程图纸里的矢量图元可以通过自监督预训练学到可迁移表示，从而在 FloorPlanCAD 少标注 fine-tuning 时优于从零训练。**

这版先不追求大模型，而是做一个可控、可复现的小模型，重点回答“矢量图元预训练是否有用”。

## 2. Token 化方案

v0 以 SVG/DXF primitive 为基本 token。每个 token 至少包含三类信息：

| 信息类型 | 字段 |
|---|---|
| 几何参数 | 图元类型、归一化坐标、bbox、长度/面积、角度、端点/中心点、采样点序列 |
| 样式/结构 | layer、stroke/fill、line width、是否闭合、同层邻居、空间近邻 |
| 可选文本 | text 内容 embedding、位置、字号、旋转角、最近 primitive/group |

FloorPlanCAD v0 先支持 `path`、`circle`、`ellipse`。DXF 扩展时再加入 `line`、`polyline`、`arc`、`block reference` 和文本标注。长图纸按空间窗口或 primitive 数切成局部窗口，初始窗口大小建议 2,048 primitives，超过则分块。

## 3. 模型结构

建议先做轻量 Transformer encoder：

- token embedding：几何 MLP + 类型 embedding + layer/style embedding；
- attention bias：加入空间距离、同层关系、bbox overlap / intersection；
- backbone：4-6 层 Transformer，hidden dim 128 或 256，4 heads；
- 输出：每个 token 的上下文表示，以及窗口级 pooled 表示。

模型规模目标控制在 1M-5M 参数，方便快速跑 label-efficiency 曲线。

## 4. 自监督目标

v0 不做复杂 generative pretraining，先做三类简单但可检验的目标：

1. **Masked primitive modeling**
   随机遮住图元类型、部分几何参数或 style/layer，要求模型根据上下文恢复。这个目标直接测试模型是否理解图元之间的局部结构。

2. **Vector-to-raster reconstruction / alignment**
   给定局部 primitive token，预测对应局部 raster occupancy 或 distance transform；也可以用对比学习让 vector window embedding 对齐 raster crop embedding。这个目标把精确矢量结构和图像空间联系起来。

3. **Text-geometry binding**
   如果有文字或尺寸标注，则预测某段文本是否属于某个 primitive/group。FloorPlanCAD 文本弱时先不开启，等 DXF 公共样例验证后再加。

第一版优先级：Masked primitive modeling > Vector-to-raster alignment > Text-geometry binding。

## 5. 预训练语料量估计

当前只使用公开 FloorPlanCAD，不使用私有图纸。

| 语料口径 | 图纸数 | raw primitive 数 | 2,048 primitive/window 估计 | 4,096 primitive/window 估计 |
|---|---:|---:|---:|---:|
| train | 6,965 | 7,764,513 | 8,568 windows | 7,444 windows |
| val | 810 | 904,517 | 1,001 windows | 868 windows |
| test | 3,827 | 3,952,258 | 4,548 windows | 4,024 windows |
| 全量仅供统计 | 11,602 | 12,621,288 | 14,117 windows | 12,336 windows |

实验纪律建议：**预训练只用 train split**，val/test 只用于模型选择和最终评估，避免泄漏。按 2,048 primitive/window 估计，第一版自监督预训练约 8.6k 个窗口；如果每个窗口做 4-8 种 mask/augmentation，等效训练样本约 3.4 万到 6.9 万个。

## 6. 下游验证

主验证任务：FloorPlanCAD panoptic symbol spotting / primitive semantic prediction。

核心比较：

- 从零训练 CADTransformer-style 小模型；
- DrawingPT v0 预训练后 fine-tune；
- 标注比例：1%、5%、10%、25%、50%、100%。

成功门槛建议：在 1%-10% 低标注区间，预训练模型相对从零训练至少提升 5% relative，或者绝对 F1/PQ 提升超过 0.02；否则需要诊断预训练目标是否太容易、token 化是否丢结构、或者数据规模是否不足。

## 7. 组会需要讨论的问题

1. v0 是否先只做 SVG primitive，还是一开始就纳入 DXF block/text？
2. 自监督主目标选 masked primitive，还是 vector-to-raster alignment？
3. paper-faithful baseline 尚未完成前，DrawingPT v0 是否先做 toy model sanity check？
4. 预训练是否严格只用 train split，还是允许额外公开无标注图纸作为 unsupervised corpus？
