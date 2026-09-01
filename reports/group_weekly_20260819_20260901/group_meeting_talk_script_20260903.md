# 2026-09-03 组会说稿：DrawingPT 周报

## 0. 一句话主线

这两周我主要做的不是追一个单点分数，而是把 DrawingPT 从“想法”推进到一个可核验的 v0 实验闭环：先明确文献定位，再冻结 FloorPlanCAD 数据资产，然后跑通矢量 primitive 的预训练和低标注语义实验，最后把它和工程量 / 造价方向连接成一个后续可以验证的应用链路。

如果时间很短，我建议只讲三件事：

1. **新冻结资产：** 11,602 张 SVG，12,621,288 个 primitive token，14,117 个 2048-token windows，18 组低标注 split；关键证据文件都有 SHA-256。
2. **新增实验数字：** 1% seed0304 下，1000-step controlled run 中 pretrained 的 foreground macro F1=0.0320，高于 scratch 的 0.0270；rare macro F1=0.0083，高于 scratch 的 0.0022。
3. **下周门禁：** 把 1% 扩到 5%、10% 和多 seed，形成 label-efficiency curve；同时做预测侧 pseudo-BoQ 误差评估。

## 1. 开场，约 40 秒

老师、同学们好。
我这次汇报的主题是 DrawingPT 的第一版实验闭环。

上一阶段我们讨论过，FloorPlanCAD 这个任务如果只沿着强监督检测器去做，很容易变成复现已有 CAD spotting 方法。所以这两周我把问题重新收窄了一下：**DrawingPT 要回答的是，矢量原生的 primitive token 自监督预训练，能不能在低标注比例下提升 CAD / 平面图理解。**

所以这次我会按三个层次讲：

第一，数据资产和数据画像现在冻结到了什么程度；
第二，DrawingPT v0 的训练闭环和 1% controlled run 结果；
第三，后续如何把这个表示学习结果接到工程量和造价方向上。

## 2. 新冻结资产，约 1 分钟

本期首先把 FloorPlanCAD 的数据资产整理成了后续实验可以直接复用的形式。

目前公开 baseline 口径下，我处理了 **11,602 张 SVG**，抽取出 **12,621,288 个 primitive token**。按照 2048 token 一个 window 切分后，一共得到 **14,117 个 2048-token windows**。

同时我冻结了低标注训练清单：比例包括 **1%、5%、10%、25%、50%、100%**，seed 是 **304、1004、2026**，总共 **18 组 split**。这里有一个细节是，同一个 seed 下，小比例是大比例的前缀，这样后面做 label-efficiency curve 时，不会因为不同抽样带来额外噪声。

关键资产也已经有 hash：

| 资产 | 数字 | SHA-256 短指纹 |
| :--- | :--- | :--- |
| token summary | 12,621,288 primitive tokens | `358b22e4` |
| per-file token manifest | 11,602 SVG / 14,117 windows | `b6dd60a4` |
| low-label split manifest | 18 组 split | `7c9e55fd` |
| pseudo-BoQ by file | 11,602 行 | `0060106a` |
| controlled run summary | 2 组正式 run | `a0c97c98` |

所以这一部分我想强调的是：后面实验不是临时读一批文件，而是已经有固定资产、固定 split 和固定证据指纹。

## 3. FloorPlanCAD 数据画像，约 1 分钟

第二部分是数据画像。这个统计解释了为什么后面的实验不能只看 overall accuracy。

从 SVG primitive 类型看，**path 占 98.68%**，circle 约 1.24%，ellipse 约 0.08%。也就是说，v0 阶段最核心的不是把很多复杂图元类型都做进去，而是先把 path 这种最主要的矢量几何表达学稳。

从单图规模看，单张图的 primitive 数中位数是 **544**，但是最大值达到 **53,919**，还有 79 张图超过 10,000 个 primitive。这说明整图直接训练不太稳定，所以我采用 2048-token window 是必要的。

从语义类别看，带 semanticId 的元素有 **5,828,994 个**，35 类都出现了，但是非常长尾。比如 wall 占 **23.37%**，而 rolling door 只有 **98 个**。这会天然鼓励模型预测高频类，所以后续必须看 foreground macro F1、rare F1 和 per-class support，而不是只看 accuracy。

这部分对实验设计的影响是：**窗口化、class-aware sampling、rare-class F1 不是附加项，而是这个数据集上低标注实验的基本门槛。**

## 4. DrawingPT v0 训练闭环和实验结果，约 2 分钟

第三部分是模型和实验。

DrawingPT v0 现在的输入是 SVG primitive token。每个 token 主要包含 type、bbox、长度 proxy、面积 proxy、semanticId、instanceId 和一些弱样式特征。预训练目标目前是 masked primitive pretraining，微调目标是 primitive-level semantic classification。

本期先跑通了 masked primitive pretrain 的入口。2048-token 设置下，一个 short pretrain 的 loss 从 **1.642630 降到 0.107217**，并保存了 checkpoint。这个结果本身不表示下游一定有效，但它说明预训练入口、数据读取和 checkpoint 链路已经通了。

然后我做了 semantic 训练的诊断。最开始如果把 background/unlabeled 也放进 loss，会出现一个问题：all accuracy 看起来不差，但 foreground F1 会塌掉。也就是说模型学会了背景捷径，没有真正学前景符号。因此后续我改成 foreground-only loss，并加入 inverse-sqrt class weighting。

在此基础上，我做了一组正式的 1000-step controlled run。设置是：

- 同一个 1% split：seed0304；
- 同样 2048-token window；
- 同样 class-aware sampler；
- 同样 inverse-sqrt class weighting；
- scratch 和 pretrained 两组对照；
- 两组都在 full validation 上评估，共 1001 个 validation windows。

结果如下：

| 设置 | foreground accuracy | foreground macro F1 | rare macro F1 | runtime |
| :--- | ---: | ---: | ---: | ---: |
| scratch, 1000 step | 0.2048 | 0.0270 | 0.0022 | 约 124s |
| pretrained, 1000 step | 0.2178 | 0.0320 | 0.0083 | 约 125s |

我的解读比较谨慎：**pretrained 是正向的，但还不是充分结论。**
正向在于 foreground accuracy、macro F1、rare macro F1 都比 scratch 高；谨慎在于这只是 1% 单 seed、v0 小模型和 1000 step，还不能说预训练稳定有效。

所以这组实验的意义不是“已经做出很好结果”，而是证明现在可以进入真正的 label-efficiency 验证：接下来要看 1%、5%、10% 甚至多 seed 下，pretrained 是否持续优于 scratch。

## 5. 工程造价方向，约 1 分钟

第四部分是应用方向。我调研后觉得，工程造价不应该在当前阶段直接做“2D 图纸到总价”的黑箱预测。

更稳的路线是：**图纸理解 → 构件/符号/工程量 proxy → pseudo-BoQ → 真实 BoQ 或造价。**

因此我先基于 FloorPlanCAD 的 semantic 和 instance 标注，构造了一个 per-file pseudo-BoQ 表，共 **11,602 行**。字段包括门窗数量、墙体长度 proxy、楼梯、电梯、扶梯、车位、厨卫设备等。

训练集上的一些可讲数字是：

- door instances：**34,704**
- window instances：**15,376**
- wall length proxy：**8,836,841.492**
- stair instances：**4,345**
- elevator instances：**3,206**
- sanitary fixture instances：**16,722**

这里我会明确边界：这些不是实际工程造价，也不是米、平方米意义上的真实工程量。它们是从图纸语义和几何里抽出来的研究 proxy。下一步等 semantic prediction 稳定后，就可以把预测结果也转成同字段 pseudo-BoQ，然后计算 count MAE、relative error 和 length proxy error。这样会比只报 F1 更接近应用。

## 6. 下周计划和希望组会确认的问题，约 1 分钟

下一步我建议主线是 **DrawingPT 低标注预训练收益曲线**。

具体门禁有三个：

第一，扩展 controlled run。
从当前 1% seed0304 扩到 **1%、5%、10% × scratch/pretrained × 多 seed**，输出 label-efficiency curve。每组都记录 foreground accuracy、macro F1、rare F1、per-class support、dominant predictions 和 runtime。

第二，处理高频类塌缩。
如果 5% 和 10% 仍然被 wall、window、toilet 这类高频类主导，就比较 focal loss、更强 class-aware sampler、longer schedule 或更大模型。

第三，把模型输出接到 pseudo-BoQ。
不是立刻做真实造价，而是先验证：semantic prediction 转成工程量 proxy 后，门窗数量、墙体长度 proxy 等误差能不能下降。

我希望组会上确认三个问题：

1. 近期主问题是否就定为：**矢量原生自监督预训练能否提升低标注 CAD primitive 理解？**
2. v0 是否先坚持 SVG primitive，不急着加入 text、layer、block 和 DWG 原生结构？
3. 是否需要同步做一个小型 VLM prompt baseline，用来回答“直接拿视觉模型看渲染图能不能解决计数、测量和空间关系”的问题？

## 7. 结尾，约 20 秒

总结一下，本期已经完成的是：数据资产冻结、数据分布画像、v0 预训练和语义训练闭环、1% controlled run、以及 pseudo-BoQ 应用中间层。

当前最重要的结论是：**预训练出现了正向信号，但还需要 label-efficiency curve 才能变成可信研究结论。**
所以下一周我会优先把多比例、多 seed 的受控实验补齐，同时把预测侧 pseudo-BoQ 作为应用验证支线推进。

## 8. 可能被问到的问题和回答

### Q1：现在 macro F1 这么低，为什么还值得讲？

可以回答：
是的，绝对值还很低，所以我不会把它表述成模型已经有效。它值得讲的原因是，这组实验已经从 smoke 变成了同口径 controlled run，而且 pretrained 相比 scratch 在 foreground accuracy、macro F1 和 rare macro F1 上都有一致正向信号。下一步要验证的是这个信号在 5%、10% 和多 seed 下是否稳定。

### Q2：为什么不直接追更大的模型或更长训练？

可以回答：
可以做，但在此之前我想先确认变量。现在先用 v0 小模型把数据、loss、sampler、split 和评估口径固定住。否则直接上大模型，很难判断提升来自预训练、训练时长、模型容量还是采样变化。

### Q3：class-aware sampler 已经有效了吗？

可以回答：
目前只能说 sampler 改变了暴露分布，不能说它已经提升模型效果。真正效果要看 full-val controlled run。当前 1000-step 的结果里 pretrained 有提升，但还没有单独拆出 sampler 消融，所以后续会把 sampler、loss 和 schedule 分开比较。

### Q4：这个工作和已有 CAD spotting 方法有什么区别？

可以回答：
已有方法更偏强监督检测或识别。DrawingPT 想回答的是表示学习问题：能否用矢量 primitive 做自监督预训练，并在低标注比例下带来稳定收益。因此我的评估重点会放在 scratch vs pretrained 的 label-efficiency curve，而不是只追一个全监督单点指标。

### Q5：为什么工程造价不直接端到端预测总价？

可以回答：
因为真实造价依赖比例尺、材料、做法、地区定额、单价、楼层和 BoQ 标签。仅靠当前 FloorPlanCAD 的 SVG/semantic 标注，直接预测总价会缺少监督信号和可解释性。更合理的是先做 quantity takeoff / pseudo-BoQ 中间层，等构件和工程量 proxy 稳定后再接真实 BoQ 或单价模型。

### Q6：下周最小可交付是什么？

可以回答：
最小可交付是 1%、5%、10% 三档下 scratch vs pretrained 的 label-efficiency 表，至少包括 foreground accuracy、macro F1、rare F1、per-class support 和 runtime。如果资源允许，再加多 seed；如果资源紧张，先把 5% 和 10% 的单 seed 跑完。
