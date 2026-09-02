#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
chart_forge.py — 零依赖 SVG 图表生成器（纯标准库）
================================================

把结构化数据（CSV / JSON）渲染成可直接用的 SVG 图表，不依赖任何第三方包。
支持三种图表类型：
  - bar   柱状图（单系列 / 多系列分组）
  - line  折线图（单系列 / 多系列，带网格与标记点）
  - pie   饼图（带图例与百分比标签）

设计目标：
  - 零依赖：仅用 csv / json / math / sys / os / html / random，开箱即跑。
  - 可控：尺寸、配色、标题、坐标轴全部参数化。
  - 可用：输出标准 SVG 1.1，浏览器 / PPT / 文档直接内嵌。
  - 安全：不联网、不读外部脚本、不执行任何动态代码。

数据格式
--------
CSV（首行表头，UTF-8）：
  单系列 bar / line / pie：两列  label,value
    月份,销售额
    1月,120
    2月,150
  多系列 line / bar：首列 x 轴标签，其余每列一个系列
    月份,A产品,B产品
    1月,120,80
    2月,150,95

JSON（UTF-8）：
  {"title":"示例","type":"bar","series":[{"name":"销售额","points":[["1月",120],["2月",150]]}]}
  或简写单系列：{"type":"pie","points":[["A",30],["B",70]]}

用法
----
  python chart_forge.py --demo                 # 跑内置示例，生成 demo 图表
  python chart_forge.py --input data.csv --type bar --output out.svg
  python chart_forge.py --input data.json --type line --output out.svg --title "销售趋势"
  python chart_forge.py --input d.csv --type pie --width 640 --height 480

退出码：0 = 成功；非 0 = 参数或数据错误（详见 stderr）。
"""

import argparse
import csv
import json
import math
import os
import sys
import html
import random

# 默认配色：深蓝 + 金 + 青 + 橙 + 灰蓝 + 紫 + 棕 + 绿
PALETTE = [
    "#1f3a5f", "#c9a227", "#2a9d8f", "#e76f51",
    "#5e548e", "#8d99ae", "#bc6c25", "#4a7c59",
]

WIDTH_DEFAULT = 800
HEIGHT_DEFAULT = 520
MARGIN = {"top": 64, "right": 32, "bottom": 72, "left": 72}


def esc(text):
    """转义 SVG / XML 文本，防止注入与解析错误。"""
    return html.escape(str(text), quote=True)


def read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))
    if not rows:
        raise ValueError("CSV 为空")
    header = [c.strip() for c in rows[0]]
    body = [[c.strip() for c in r] for r in rows[1:] if any(c.strip() for c in r)]
    if len(header) < 2:
        raise ValueError("CSV 至少需要两列：label,value")
    series_names = header[1:]
    series = []
    for i, name in enumerate(series_names, start=1):
        pts = []
        for r in body:
            if i < len(r) and r[i] != "":
                try:
                    val = float(r[i])
                except ValueError:
                    raise ValueError("第 %d 行第 %d 列不是数字: %r" % (body.index(r) + 2, i + 1, r[i]))
                pts.append((r[0], val))
        series.append({"name": name, "points": pts})
    return series


def read_json(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if "series" in data:
        return data["series"]
    if "points" in data:
        return [{"name": data.get("name", "series"), "points": [tuple(p) for p in data["points"]]}]
    raise ValueError("JSON 需包含 series 或 points 字段")


def load_data(path, chart_type):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".json":
        series = read_json(path)
    else:
        series = read_csv(path)
    if not series:
        raise ValueError("未解析到任何数据系列")
    # 饼图只取第一个系列
    if chart_type == "pie":
        return series[:1]
    return series


def _fmt_val(v):
    if abs(v - round(v)) < 1e-9:
        return str(int(round(v)))
    return ("%.2f" % v).rstrip("0").rstrip(".")


def render_bar(series, W, H, title):
    left, right = MARGIN["left"], W - MARGIN["right"]
    top, bottom = MARGIN["top"], H - MARGIN["bottom"]
    plot_w, plot_h = right - left, bottom - top
    n_series = len(series)
    groups = [p[0] for p in series[0]["points"]]
    n_groups = len(groups)
    max_v = max((p[1] for s in series for p in s["points"]), default=0)
    max_v = max(max_v, 1e-9)
    # 向上取整到友好刻度
    nice_max = _nice_ceiling(max_v)
    parts = []
    parts.append('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" font-family="-apple-system,Segoe UI,Microsoft YaHei,sans-serif">' % (W, H, W, H))
    parts.append(_bg(W, H))
    if title:
        parts.append('<text x="%d" y="34" font-size="20" font-weight="700" fill="#1f2d3d">%s</text>' % (left, esc(title)))
    # y 轴网格 + 刻度
    ticks = 5
    for t in range(ticks + 1):
        yv = nice_max * t / ticks
        y = bottom - plot_h * t / ticks
        parts.append('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="#e2e8f0" stroke-width="1"/>' % (left, y, right, y))
        parts.append('<text x="%d" y="%.1f" font-size="11" fill="#64748b" text-anchor="end">%s</text>' % (left - 8, y + 4, _fmt_val(yv)))
    parts.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#94a3b8" stroke-width="1.5"/>' % (left, top, left, bottom))
    parts.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#94a3b8" stroke-width="1.5"/>' % (left, bottom, right, bottom))
    # 柱体
    group_gap = plot_w / n_groups
    inner_pad = group_gap * 0.18
    bar_area = group_gap - inner_pad * 2
    bar_w = bar_area / n_series if n_series > 1 else bar_area * 0.6
    for gi, g in enumerate(groups):
        gx = left + gi * group_gap + inner_pad
        for si, s in enumerate(series):
            val = s["points"][gi][1] if gi < len(s["points"]) else 0
            h = plot_h * (val / nice_max) if nice_max else 0
            x = gx + si * bar_w if n_series > 1 else gx + (group_gap - bar_w) / 2
            y = bottom - h
            color = PALETTE[si % len(PALETTE)]
            parts.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="2" fill="%s"><title>%s: %s</title></rect>' % (x, y, bar_w - 1, h, color, esc(g), _fmt_val(val)))
            if h > 14:
                parts.append('<text x="%.1f" y="%.1f" font-size="10" fill="#ffffff" text-anchor="middle">%s</text>' % (x + bar_w / 2, y + 12, _fmt_val(val)))
        parts.append('<text x="%.1f" y="%.1f" font-size="11" fill="#334155" text-anchor="middle">%s</text>' % (gx + group_gap / 2 - inner_pad, bottom + 18, esc(g)))
    parts.append(_legend(series, W, top))
    parts.append('</svg>')
    return "\n".join(parts)


def render_line(series, W, H, title):
    left, right = MARGIN["left"], W - MARGIN["right"]
    top, bottom = MARGIN["top"], H - MARGIN["bottom"]
    plot_w, plot_h = right - left, bottom - top
    labels = [p[0] for p in series[0]["points"]]
    n = len(labels)
    max_v = max((p[1] for s in series for p in s["points"]), default=0)
    max_v = max(max_v, 1e-9)
    nice_max = _nice_ceiling(max_v)
    parts = []
    parts.append('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" font-family="-apple-system,Segoe UI,Microsoft YaHei,sans-serif">' % (W, H, W, H))
    parts.append(_bg(W, H))
    if title:
        parts.append('<text x="%d" y="34" font-size="20" font-weight="700" fill="#1f2d3d">%s</text>' % (left, esc(title)))
    ticks = 5
    for t in range(ticks + 1):
        yv = nice_max * t / ticks
        y = bottom - plot_h * t / ticks
        parts.append('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="#e2e8f0" stroke-width="1"/>' % (left, y, right, y))
        parts.append('<text x="%d" y="%.1f" font-size="11" fill="#64748b" text-anchor="end">%s</text>' % (left - 8, y + 4, _fmt_val(yv)))
    parts.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#94a3b8" stroke-width="1.5"/>' % (left, top, left, bottom))
    parts.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#94a3b8" stroke-width="1.5"/>' % (left, bottom, right, bottom))
    if n > 1:
        step = plot_w / (n - 1)
    else:
        step = 0
    for si, s in enumerate(series):
        color = PALETTE[si % len(PALETTE)]
        pts = []
        for i, (lab, val) in enumerate(s["points"]):
            x = left + (i * step if n > 1 else plot_w / 2)
            y = bottom - plot_h * (val / nice_max) if nice_max else bottom
            pts.append((x, y))
        d = "M " + " L ".join("%.1f,%.1f" % (x, y) for x, y in pts)
        parts.append('<path d="%s" fill="none" stroke="%s" stroke-width="2.4" stroke-linejoin="round"/>' % (d, color))
        for idx, (x, y) in enumerate(pts):
            parts.append('<circle cx="%.1f" cy="%.1f" r="3.2" fill="%s"><title>%s</title></circle>' % (x, y, color, _fmt_val(s["points"][idx][1])))
        # x 轴标签
    for i, lab in enumerate(labels):
        x = left + (i * step if n > 1 else plot_w / 2)
        parts.append('<text x="%.1f" y="%.1f" font-size="11" fill="#334155" text-anchor="middle">%s</text>' % (x, bottom + 18, esc(lab)))
    parts.append(_legend(series, W, top))
    parts.append('</svg>')
    return "\n".join(parts)


def render_pie(series, W, H, title):
    s = series[0]
    pts = [(lab, max(val, 0)) for lab, val in s["points"] if val > 0]
    total = sum(v for _, v in pts) or 1
    cx, cy = W * 0.38, H / 2 + 10
    r = min(W * 0.30, H * 0.36)
    parts = []
    parts.append('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" font-family="-apple-system,Segoe UI,Microsoft YaHei,sans-serif">' % (W, H, W, H))
    parts.append(_bg(W, H))
    if title:
        parts.append('<text x="%d" y="34" font-size="20" font-weight="700" fill="#1f2d3d">%s</text>' % (MARGIN["left"], esc(title)))
    start = -math.pi / 2
    for i, (lab, val) in enumerate(pts):
        frac = val / total
        end = start + frac * 2 * math.pi
        large = 1 if (end - start) > math.pi else 0
        x1 = cx + r * math.cos(start)
        y1 = cy + r * math.sin(start)
        x2 = cx + r * math.cos(end)
        y2 = cy + r * math.sin(end)
        color = PALETTE[i % len(PALETTE)]
        parts.append('<path d="M %.1f,%.1f L %.1f,%.1f A %.1f,%.1f 0 %d 1 %.1f,%.1f Z" fill="%s"><title>%s: %s (%.1f%%)</title></path>' % (cx, cy, x1, y1, r, r, large, x2, y2, color, esc(lab), _fmt_val(val), frac * 100))
        # 百分比标签
        mid = (start + end) / 2
        lx = cx + (r * 0.62) * math.cos(mid)
        ly = cy + (r * 0.62) * math.sin(mid)
        if frac > 0.04:
            parts.append('<text x="%.1f" y="%.1f" font-size="11" fill="#ffffff" text-anchor="middle">%.1f%%</text>' % (lx, ly + 4, frac * 100))
        start = end
    # 图例
    lx = W * 0.72
    ly = cy - len(pts) * 14
    for i, (lab, val) in enumerate(pts):
        yy = ly + i * 26
        color = PALETTE[i % len(PALETTE)]
        parts.append('<rect x="%.1f" y="%.1f" width="14" height="14" rx="2" fill="%s"/>' % (lx, yy, color))
        parts.append('<text x="%.1f" y="%.1f" font-size="12" fill="#334155">%s  %s (%.1f%%)</text>' % (lx + 22, yy + 12, esc(lab), _fmt_val(val), val / total * 100))
    parts.append('</svg>')
    return "\n".join(parts)


def _bg(W, H):
    return '<rect x="0" y="0" width="%d" height="%d" fill="#ffffff"/>' % (W, H)


def _legend(series, W, top):
    if len(series) <= 1:
        return ""
    x = W - MARGIN["right"] - 180
    y = top + 6
    out = ['<g font-size="12" fill="#334155">']
    for i, s in enumerate(series):
        color = PALETTE[i % len(PALETTE)]
        yy = y + i * 20
        out.append('<rect x="%d" y="%d" width="12" height="12" rx="2" fill="%s"/>' % (x, yy, color))
        out.append('<text x="%d" y="%d" font-size="12">%s</text>' % (x + 18, yy + 11, esc(s["name"])))
    out.append('</g>')
    return "\n".join(out)


def _nice_ceiling(v):
    if v <= 0:
        return 1
    exp = math.floor(math.log10(v))
    base = 10 ** exp
    for m in (1, 2, 2.5, 5, 10):
        if v <= m * base:
            return m * base
    return 10 * base


def build_demo():
    """生成内置示例数据并返回 (path, type, title)。"""
    here = os.path.dirname(os.path.abspath(__file__))
    demo_csv = os.path.join(here, "demo_data.csv")
    with open(demo_csv, "w", encoding="utf-8") as f:
        f.write("月份,销售额,利润\n")
        for i, (m, s, p) in enumerate([("1月", 120, 38), ("2月", 150, 52), ("3月", 135, 41), ("4月", 188, 67), ("5月", 210, 81), ("6月", 176, 59)]):
            f.write("%s,%d,%d\n" % (m, s, p))
    return demo_csv, "bar", "上半年经营概览（示例）"


def main(argv=None):
    ap = argparse.ArgumentParser(description="零依赖 SVG 图表生成器")
    ap.add_argument("--input", help="数据文件 .csv 或 .json")
    ap.add_argument("--type", choices=["bar", "line", "pie"], default="bar")
    ap.add_argument("--output", default="chart.svg", help="输出 SVG 路径")
    ap.add_argument("--title", default="", help="图表标题")
    ap.add_argument("--width", type=int, default=WIDTH_DEFAULT)
    ap.add_argument("--height", type=int, default=HEIGHT_DEFAULT)
    ap.add_argument("--demo", action="store_true", help="生成内置示例图表")
    args = ap.parse_args(argv)

    try:
        if args.demo or not args.input:
            in_path, ctype, title = build_demo()
            out = args.output if args.input else os.path.join(os.path.dirname(os.path.abspath(__file__)), "demo_chart.svg")
            title = title if not args.title else args.title
        else:
            in_path = args.input
            ctype = args.type
            title = args.title
            out = args.output
        series = load_data(in_path, ctype)
        if ctype == "bar":
            svg = render_bar(series, args.width, args.height, title)
        elif ctype == "line":
            svg = render_line(series, args.width, args.height, title)
        else:
            svg = render_pie(series, args.width, args.height, title)
        with open(out, "w", encoding="utf-8") as f:
            f.write(svg)
        print("OK: 图表已生成 -> %s (%d 字节, 类型=%s, 系列数=%d)" % (os.path.abspath(out), len(svg.encode("utf-8")), ctype, len(series)))
        return 0
    except Exception as e:
        sys.stderr.write("ERROR: %s\n" % e)
        return 2


if __name__ == "__main__":
    sys.exit(main())
