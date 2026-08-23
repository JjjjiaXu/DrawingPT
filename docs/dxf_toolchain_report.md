# DXF / DWG→矢量解析工具链记录

生成日期：2026-08-22

## 纪律边界

- 当前阶段只使用公开数据集和公开/合成样例。
- 在数据协议落地之前，不碰业务方真实图纸。
- 原始 DXF/DWG 文件应放在 `data/raw/` 或其他被 `.gitignore` 忽略的目录里，不能提交到 GitHub。
- 本仓库目前不直接解析原生 DWG；安全路线是先用外部工具把 DWG 转成 DXF，再用 `ezdxf` 读取 DXF。

## 当前实现

脚本位置：

```powershell
python scripts/inspect_dxf.py --input path\to\drawing.dxf --json-out outputs/reports/dxf_summary.json
```

依赖：

- `ezdxf`

脚本会记录：

- entity 类型统计；
- layer 统计；
- `INSERT` 块引用统计；
- `TEXT` / `MTEXT` 文字样例；
- 常见 DXF entity 的几何参数预览。

## 当前可解析字段

| DXF entity | 已导出字段 |
|---|---|
| `LINE` | 起点、终点 |
| `ARC` | 圆心、半径、起止角 |
| `CIRCLE` | 圆心、半径 |
| `ELLIPSE` | 圆心、major axis、ratio、起止参数 |
| `LWPOLYLINE` / `POLYLINE` | 是否闭合、前若干点 |
| `SPLINE` | degree、前若干控制点 |
| `INSERT` | block 名、插入点、缩放、旋转 |
| `TEXT` / `MTEXT` | 文本、插入点、高度、旋转 |
| `DIMENSION` | dimension type 和文本字段 |

## 这说明了什么

从 DXF 文件里，当前脚本已经可以拿到第一周清单要求的核心信息：

1. 图元/entity 类型；
2. 几何参数；
3. 图层属性；
4. 块引用；
5. 文字标注。

这对 DrawingPT v0 很重要，因为它决定了“图元流 + 文字流 + 图层/块结构先验”是否能从公开 DXF 数据里构造出来。

## 还没有完成的验证

- 还没有用真实公开 DXF 样例跑出冻结 JSON 摘要。
- 还没有验证 DWG→DXF 转换会不会丢失文字、图层、块引用或尺寸标注。
- 还没有比较不同转换工具的保真度。

候选转换工具包括 AutoCAD 导出、ODA File Converter、LibreDWG 或实验室认可的其他转换器。

## 下一步门禁

在把 FloorPlanCAD 之外的公开 DXF 图纸纳入预训练前，需要冻结一个公开 DXF smoke sample，并记录：

- 来源 URL 或生成脚本；
- 如果从 DWG 转来，记录转换工具和版本；
- `inspect_dxf.py` 输出 JSON 的 SHA-256；
- 文字、图层、块引用、尺寸标注是否保留。
