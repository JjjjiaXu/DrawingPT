# DrawingPT v0 class-aware sampler audit

生成日期：2026-09-01

## 一句话结论

class-aware sampler 已经能在不增加 GPU 资源的前提下改变 1% 低标注训练窗口的暴露分布：它用 replacement 采样重复包含较少见前景类的窗口，用于对抗普通随机窗口被高频 wall/window/sink 主导的问题。

## 设置

- split：train
- label list：`configs\label_fractions\floorplancad_train_seed0304_001pct.txt`
- window size：2048
- dataset windows：88
- seed：304

## 一轮训练窗口暴露对比

| sampler | sampled windows | unique windows | foreground tokens | classes with support | rare classes with support | rare token share | wall token share |
|---|---:|---:|---:|---:|---:|---:|---:|
| random/no replacement | 88 | 88 | 28800 | 32 | 11 | 0.0848 | 0.2804 |
| class-aware/replacement | 88 | 46 | 37811 | 32 | 11 | 0.0882 | 0.2770 |

## sampler 权重摘要

| 指标 | 数值 |
|---|---:|
| min | 0.050000 |
| median | 0.691331 |
| mean | 0.789194 |
| max | 1.817777 |

## 解释边界

- 这是 sampler exposure audit，不是模型性能结果。
- class-aware 采样会牺牲一部分 unique window 覆盖，换取少见类别窗口的重复暴露；后续必须和 validation macro/rare F1 一起看。
- 如果某个极少类没有出现在 1% label-list 中，sampler 不能凭空创造该类监督信号，只能重分配已有监督窗口。
