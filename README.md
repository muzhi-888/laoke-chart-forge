# laoke-chart-forge · 数据可视化图表生成器

> 局内人·老K · 专注实体老板 AI 落地实战

零依赖把结构化数据（CSV / JSON）渲染成可直接用的 SVG 柱状图 / 折线图 / 饼图。不依赖任何第三方库，脚本只用 Python 标准库，纯本地运行、不联网、可审计、开箱即用。

## 这个工具解决什么

- 想画图但工具门槛高（装 matplotlib 要配环境、中文乱码）。
- 图做出来了但看不懂（坐标轴没刻度、图例错位、配色瞎搭）。
- 图能用但没法用（只能导出像素图，放大就糊）。
- 数据没洗就画（空值、单位不统一、异常值直接上图，结论被带偏）。

本工具：**先教你怎么把数据理顺、把图选对、把视觉做干净，再给你一个随时能跑的脚本把活干完。**

## 快速上手

```bash
# 跑内置示例，先看效果
python scripts/chart_forge.py --demo

# 柱状图（默认）
python scripts/chart_forge.py --input 数据.csv --type bar --output 销售图.svg

# 折线图
python scripts/chart_forge.py --input 数据.csv --type line --output 趋势图.svg

# 饼图（只取第一个系列）
python scripts/chart_forge.py --input 数据.csv --type pie --output 占比图.svg
```

数据格式见 `SKILL.md` 第六、七节，方法论见 `references/`（图表选型、数据预处理、配色规范、误导防范、嵌入集成）。

## 能力边界（说实话）

- ✅ 静态矢量图（柱 / 折 / 饼），适合汇报、文档、网页。
- ✅ 零依赖、可审计、可嵌入。
- ❌ 不含散点 / 雷达 / 热力 / 地图等复杂图（规划中）。
- ❌ 不含实时交互 / 大屏联动（那是 BI 范畴）。
- ❌ 不自动洗数据（数据质量由你把关）。

## 相关资源

- ima 知识库《局内人·老K 投资工具箱》：数据驱动的经营分析与图表实战案例
- SkillHub 作者主页：在 SkillHub 搜索 `laoke-chart-forge`
- 作者落地页（更多 AI 落地实战与工具合集）：https://muzhi-888.github.io/ju-nei-ren-lao-k/

## 许可证与免责声明

MIT License。本工具仅供学习与研究使用，不构成任何投资建议或收益承诺；使用者须对输入数据的合规性与图表呈现的真实性负责，禁止用于伪造数据、误导性呈现或任何违法用途。
