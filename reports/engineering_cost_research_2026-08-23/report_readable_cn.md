# 工程造价自动估算调研汇报

生成日期：2026-08-23

## 1. 一句话结论

工程造价自动估算已经有较多 AI/BIM/机器学习研究，但成熟路线主要是 **BIM/结构化工程量 → 造价** 或 **项目特征/历史数据 → 造价预测**。真正从 **2D CAD/施工图原始图元 → 完整工程造价** 的端到端学术路线还不成熟。

对 DrawingPT 最稳的定位不是直接做“CAD 图纸一键出总价”，而是做造价链路前端的图纸理解与表示学习模块：先把 2D 图纸里的构件、符号、尺寸、数量和文本关系抽出来，再服务 quantity takeoff、BoQ/BoM 生成和造价估算。

## 2. 领域链路：造价不是只看图纸

工程造价通常不是单一视觉任务，而是一条多阶段链路：

| 阶段 | 需要的信息 | AI 可以做什么 |
|---|---|---|
| 图纸理解 | 构件、符号、尺寸、房间/系统关系 | CAD/图纸解析、符号检测、文字识别、实例分组 |
| 工程量计算 | 长度、面积、体积、个数、材料规格 | quantity takeoff、BoQ/BoM 生成 |
| 计价规则 | 清单编码、定额、地区、时间、施工方法 | 规则匹配、知识库检索、LLM 辅助解释 |
| 价格估算 | 材料价、人工价、机械价、历史项目数据 | 价格预测、成本回归、风险/不确定性估计 |
| 审核输出 | 总价、分项价、置信度、可追溯证据 | 可解释报告、差异检查、人工复核提示 |

这意味着：只靠 DrawingPT 直接输出总造价风险很大；更合理的研究闭环是先做“图纸 → 可计量结构”，再接造价规则和价格模型。

## 3. 文献现状分成三类

### 3.1 BIM / 结构化模型到造价：相对成熟

BIM 路线最接近工程造价实际流程，因为 BIM 模型已经包含构件、尺寸、材料、工程量等结构化信息。近期研究包括：

| 代表工作 | 输入 | 输出 | 启发 |
|---|---|---|---|
| BIM-based quantity takeoff 综述 | BIM 模型 | 工程量、QTO 流程总结 | 说明 BIM 自动算量是主流成熟路线 |
| BIM + LLM cost estimation | BIM 数据、价格数据库、地区修正 | 造价估算报告 | 说明 LLM 更适合规则/数据库/解释层，不是单独读图 |
| BIM + SSA-PGNN | BIM5D 工程量、材料价格序列 | 水利工程造价预测 | 说明结构化工程量 + 价格预测是可行路线 |

这类工作的共性是：输入已经比较结构化，AI 主要做工程量抽取、成本映射、价格预测或报告生成。

### 3.2 2D 施工图到工程量/BoM：和 DrawingPT 最相关

这一类研究更接近 DrawingPT，但多数还停在“图纸识别 / 自动算量前置步骤”，没有直接做到完整造价。

| 代表工作 | 输入 | 输出 | 启发 |
|---|---|---|---|
| AI-powered symbol detection for construction diagrams | 高分辨率施工图 | 设备/符号检测结果 | 证明施工图自动理解可以服务 material takeoff |
| Mask R-CNN 生成 Bill of Materials | 2D 图纸图像/模板 | BoM / 材料清单 | 说明视觉模型能把图纸转为清单结构 |
| Work descriptions 信息抽取 | 工程描述文本 | QTO 相关实体/关系 | 说明造价还依赖文本、规则和清单语言 |

这一类的共同限制是：常依赖特定图纸类型、特定行业符号或图片检测模型；距离“任意 CAD 图纸直接出最终造价”还有一段工程链路。

### 3.3 2D 工程图直接到成本：制造业已有相近案例

制造成本方向已有很接近 DrawingPT 想法的工作。2025 年 arXiv 文章提出从 13,684 张 2D DWG 工程图中抽取约 200 个几何/统计特征，用 XGBoost/CatBoost/LightGBM 预测汽车零部件制造成本，报告约 10% MAPE，并强调这是 end-to-end CAD-to-cost pipeline。

这不是建筑工程造价，但技术启发很强：

1. 从 DWG/DXF 抽几何特征比单纯 raster vision 更可解释。
2. 成本预测需要历史成本标签，而不仅是图纸。
3. 可解释性很重要，例如用 SHAP 找成本驱动几何因素。
4. “图纸表示 + 成本模型”比“端到端黑箱总价”更容易被工程人员接受。

## 4. 成熟度判断

| 路线 | 是否已有研究 | 成熟度 | DrawingPT 的机会 |
|---|---|---|---|
| BIM → 工程量 → 造价 | 很多 | 高 | 可作为后端流程参考 |
| 项目特征/历史数据 → 总造价预测 | 很多 | 中高 | 偏早期估算，不直接读图 |
| 2D 图纸 → 符号/构件/BoM/QTO | 有增长 | 中 | DrawingPT 可提供更强图纸表示 |
| 2D CAD 原始图元 → 完整工程造价 | 少 | 低到中 | 可能是创新空间，但需要真实造价标签 |

因此，如果老板问“有没有端到端输出工程造价估算”，可以答：有端到端造价预测研究，但大多不是直接从 2D CAD 图纸输入；直接从 2D CAD/施工图到完整造价的成熟工作还少。

## 5. DrawingPT 可以怎么切入

DrawingPT 不应第一步承诺“自动造价”，而应切成三个可验证子任务：

1. **图纸表示学习**
   用 SVG/DXF primitives 预训练，学习构件、符号、空间关系、文本关系。

2. **工程量代理任务**
   在 FloorPlanCAD 上先做符号/构件识别、实例分组、计数、长度/面积估计。这里可以把 `wall`、`door`、`window`、`stairs`、`parking spot` 等类别转成“可计量对象”。

3. **造价估算模拟或真实接入**
   如果没有真实清单/成本标签，先用公开规则或合成单价做 proof-of-concept；如果有真实项目 BoQ/成本数据，再训练从“图纸表示 + 工程量 + 文本”到分项造价的模型。

推荐路线：

```text
FloorPlanCAD / DXF
  → DrawingPT primitive representation
  → symbol / component / dimension extraction
  → quantity takeoff proxy
  → BoQ/BoM or cost-rule table
  → cost estimate with evidence
```

## 6. 需要的数据和资源

要真正做“工程造价估算”，至少需要以下数据之一：

| 数据类型 | 是否当前已有 | 用途 |
|---|---|---|
| 公开 CAD/SVG/DXF 图纸 | 部分已有，FloorPlanCAD | 图纸理解和预训练 |
| 构件/符号标注 | 已有，FloorPlanCAD | 下游识别任务 |
| 尺寸/材料/文本标注 | 不完整 | 工程量计算 |
| BoQ/BoM 清单 | 暂无 | 把图纸对象转成清单项 |
| 单价/定额/地区价格库 | 暂无 | 造价计算 |
| 项目总价或分项造价标签 | 暂无 | 训练真实 cost prediction |

所以当前阶段最现实的产出不是最终造价模型，而是“面向工程量提取的图纸表示学习与解析”。

## 7. 下次组会建议表述

可以这样汇报：

> 工程造价自动估算已有 BIM 和机器学习相关研究，但从 2D CAD 图纸直接端到端输出完整造价的路线还不成熟。现有文献更常见的是 BIM 自动算量、施工图符号检测、BoM/BoQ 自动生成、以及结构化成本预测。DrawingPT 的机会是作为前端图纸表示学习模块，把 2D CAD/SVG/DXF 图元转成可计量、可解释的构件和符号表示，再接工程量清单和价格模型。短期建议先做 quantity takeoff proxy，而不是直接做最终造价。

## 8. 可以立刻设计的实验

| 实验 | 输入 | 输出 | 成功标准 |
|---|---|---|---|
| FloorPlanCAD 构件计数 | SVG primitives | 每类实例数量 | 与 `instanceId` 统计接近 |
| 墙/门/窗工程量 proxy | SVG primitives + 语义预测 | 长度/数量/类别 | 与 GT 标注统计误差可控 |
| DrawingPT 预训练增益 | train split 自监督 + 少标注 fine-tune | 低标注 F1/PQ | 1%-10% 标注区间优于从零训练 |
| 合成单价造价 demo | 识别结果 + 手工单价表 | 分项估算表 | 能解释每个价格来自哪些图纸对象 |

这组实验可以形成一条很清楚的故事线：不是一步到位做造价，而是先证明 DrawingPT 能把图纸变成造价所需的结构化中间层。

## 9. 公开来源

| 来源 | 关键信息 |
|---|---|
| [AI-Driven Automation of Construction Cost Estimation: Integrating BIM with Large Language Models](https://www.mdpi.com/2075-5309/16/3/485) | BIM + LLM + cost database 的端到端造价系统方向 |
| [Artificial Intelligence in Preconstruction Cost Estimation: A Systematic Review](https://www.mdpi.com/2075-5309/16/15/3050) | AI 造价估算综述，适合作为 related work 入口 |
| [BIM-based quantity takeoff: Current state and future opportunities](https://www.sciencedirect.com/science/article/pii/S0926580524002851) | BIM 自动算量综述 |
| [Construction cost prediction model for agricultural water conservancy engineering based on BIM and neural network](https://www.nature.com/articles/s41598-025-10153-4) | BIM5D 工程量 + 神经网络价格预测 |
| [Towards fully automated processing and analysis of construction diagrams: AI-powered symbol detection](https://link.springer.com/article/10.1007/s10032-024-00492-9) | 施工图符号检测服务 material takeoff |
| [Generating integrated bill of materials using Mask R-CNN artificial intelligence model](https://www.sciencedirect.com/science/article/pii/S0926580522005143) | 图纸/视觉模型生成 BoM |
| [Towards Automated Construction Quantity Take-Off: An Integrated Approach to Information Extraction from Work Descriptions](https://www.mdpi.com/2075-5309/12/3/354) | 从工程描述文本抽取 QTO 信息 |
| [Machine Learning-Based Manufacturing Cost Prediction from 2D Engineering Drawings via Geometric Features](https://arxiv.org/abs/2508.12440) | 2D DWG 工程图到制造成本预测，是最接近 DrawingPT 的技术类比 |
