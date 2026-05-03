#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
render.py — domain.json → 单文件 HTML 渲染器（domain-onboarding skill）

用途
----
读取结构化中间产物 domain.json，注入 HTML 模板，输出单文件离线 HTML。
零三方依赖，纯 stdlib，自实现极简模板引擎。

domain.json schema（节选 / 字段缺失会注入"未提供"占位并告警）
----------------------------------------------------------
domain, domain_slug, tier(flash|medium|deep), preset(tech|business|finance|culture),
cutoff_date, thesis,
skeleton: { concepts[], players[], timeline[], tensions[], learning_path[] },
facts: [{id, text, source, grade(A|B|C|D)}, ...],
mechanisms: [{id, text, fact_refs:[fact_id...]}, ...],
viewpoints: [{id, text, mechanism_refs:[mech_id...], counter_evidence}, ...],
reflexivity: { narrative, self_reinforce, failure_condition },
isomorphisms: [{source, similarity, anti_similarity}, ...],
structure_layer, paradigm_layer (dict),
known_unknowns[], self_check_questions[], experts[{name, context}],
sources[], ai_disclaimer, misreadings[], blind_spots[]

CLI
---
python render.py domain.json -o out.html [--template path/to/template.html]
"""
from __future__ import annotations

import argparse
import datetime
import html
import json
import math
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence


# ---------- 极简模板引擎 ----------

_VAR_RE = re.compile(r"\{\{\s*(@?[a-zA-Z_][\w\.]*)\s*\}\}")
_RAW_RE = re.compile(r"\{\{\{\s*([a-zA-Z_][\w\.]*)\s*\}\}\}")
_BLOCK_OPEN_RE = re.compile(
    r"\{\{#(each|if)\s+([a-zA-Z_][\w\.]*)\s*\}\}"
)
_BLOCK_CLOSE_RE = re.compile(r"\{\{/(each|if)\s*\}\}")


def _resolve(path: str, ctx: Dict[str, Any]) -> Any:
    if path.startswith("@"):
        return ctx.get(path)
    cur: Any = ctx
    parts = path.split(".")
    for i, part in enumerate(parts):
        if part == "this" and i == 0:
            cur = ctx.get("this", ctx)
            continue
        if isinstance(cur, dict):
            cur = cur.get(part)
        else:
            return None
        if cur is None:
            return None
    return cur


def _stringify(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (list, dict)):
        return json.dumps(v, ensure_ascii=False)
    return str(v)


def _find_matching_close(tpl: str, start: int, kind: str) -> int:
    """从 start 开始扫描，返回与 kind 配对的 {{/kind}} 的起始位置。-1 失败。"""
    depth = 1
    i = start
    while i < len(tpl):
        op = _BLOCK_OPEN_RE.search(tpl, i)
        cl = _BLOCK_CLOSE_RE.search(tpl, i)
        if not cl:
            return -1
        if op and op.start() < cl.start():
            if op.group(1) == kind:
                depth += 1
            else:
                # 不同类型嵌套也要计数（粗略：only same kind affects depth；
                # 但模板里 if/each 互嵌时各自独立，需要分别配对——这里用栈处理）
                return _find_matching_close_stack(tpl, start, kind)
            i = op.end()
        else:
            if cl.group(1) == kind:
                depth -= 1
                if depth == 0:
                    return cl.start()
            i = cl.end()
    return -1


def _find_matching_close_stack(tpl: str, start: int, outer_kind: str) -> int:
    """更稳的栈式扫描，处理 if/each 互嵌。"""
    stack = [outer_kind]
    i = start
    while i < len(tpl) and stack:
        op = _BLOCK_OPEN_RE.search(tpl, i)
        cl = _BLOCK_CLOSE_RE.search(tpl, i)
        if not cl:
            return -1
        if op and op.start() < cl.start():
            stack.append(op.group(1))
            i = op.end()
        else:
            kind = cl.group(1)
            # 弹出最近的同类项
            for j in range(len(stack) - 1, -1, -1):
                if stack[j] == kind:
                    del stack[j]
                    break
            if not stack:
                return cl.start()
            i = cl.end()
    return -1


def render_template(tpl: str, ctx: Dict[str, Any]) -> str:
    """递归扫描，正确处理嵌套 each / if。"""
    out: List[str] = []
    i = 0
    while i < len(tpl):
        m_open = _BLOCK_OPEN_RE.search(tpl, i)
        if not m_open:
            out.append(tpl[i:])
            break
        # 把 m_open 之前的纯文本先处理
        out.append(tpl[i : m_open.start()])
        kind = m_open.group(1)
        key = m_open.group(2)
        body_start = m_open.end()
        close_pos = _find_matching_close_stack(tpl, body_start, kind)
        if close_pos < 0:
            # 找不到闭合：原样输出剩余并退出
            out.append(tpl[m_open.start() :])
            break
        body = tpl[body_start:close_pos]
        # 跳过 {{/kind}}
        close_match = _BLOCK_CLOSE_RE.match(tpl, close_pos)
        i = close_match.end() if close_match else close_pos

        if kind == "if":
            val = _resolve(key, ctx)
            truthy = bool(val) and (
                not isinstance(val, (list, dict, str)) or len(val) > 0
            )
            if truthy:
                out.append(render_template(body, ctx))
        else:  # each
            val = _resolve(key, ctx)
            if isinstance(val, list):
                for idx, item in enumerate(val):
                    sub_ctx = dict(ctx)
                    if isinstance(item, dict):
                        sub_ctx.update(item)
                    sub_ctx["this"] = item
                    sub_ctx["@index"] = idx
                    sub_ctx["@first"] = idx == 0
                    sub_ctx["@last"] = False  # 末项后置覆写
                    out.append(render_template(body, sub_ctx))
            elif isinstance(val, dict):
                items = list(val.items())
                for idx, (k, v) in enumerate(items):
                    sub_ctx = dict(ctx)
                    if isinstance(v, dict):
                        sub_ctx.update(v)
                    sub_ctx["this"] = v
                    sub_ctx["@key"] = k
                    sub_ctx["@index"] = idx
                    out.append(render_template(body, sub_ctx))

    rendered = "".join(out)
    # 变量替换最后一步
    rendered = _RAW_RE.sub(
        lambda m: _stringify(_resolve(m.group(1), ctx)), rendered
    )
    rendered = _VAR_RE.sub(
        lambda m: html.escape(_stringify(_resolve(m.group(1), ctx)), quote=True),
        rendered,
    )
    return rendered


# ---------- SVG 生成器 ----------

GRADE_COLORS = {
    "A": "#7a1f1f",  # 朱砂深
    "B": "#c98a3a",  # 赭黄
    "C": "#5b6f8a",  # 青灰
    "D": "#9a9a9a",  # 灰
}


def grade_pie_svg(grade_counts: Dict[str, int], size: int = 180) -> str:
    total = sum(grade_counts.values())
    if total == 0:
        return f'<svg class="grade-pie" width="{size}" height="{size}" role="img" aria-label="来源分级（无数据）"><circle cx="{size/2}" cy="{size/2}" r="{size/2-4}" fill="#eee" stroke="#999"/></svg>'
    cx = cy = size / 2
    r = size / 2 - 4
    parts: List[str] = []
    legend: List[str] = []
    angle = -math.pi / 2  # 12 点方向
    for grade in ("A", "B", "C", "D"):
        n = grade_counts.get(grade, 0)
        if n == 0:
            continue
        frac = n / total
        sweep = frac * 2 * math.pi
        x1 = cx + r * math.cos(angle)
        y1 = cy + r * math.sin(angle)
        angle2 = angle + sweep
        x2 = cx + r * math.cos(angle2)
        y2 = cy + r * math.sin(angle2)
        large = 1 if sweep > math.pi else 0
        color = GRADE_COLORS[grade]
        if frac >= 0.999:
            # 单一切片：直接画整圆
            parts.append(
                f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{color}" stroke="#fff" stroke-width="1"/>'
            )
        else:
            d = (
                f"M {cx:.2f} {cy:.2f} "
                f"L {x1:.2f} {y1:.2f} "
                f"A {r:.2f} {r:.2f} 0 {large} 1 {x2:.2f} {y2:.2f} Z"
            )
            parts.append(
                f'<path d="{d}" fill="{color}" stroke="#fff" stroke-width="1"><title>{grade}: {n} ({frac*100:.0f}%)</title></path>'
            )
        legend.append(
            f'<tspan fill="{color}">●</tspan> {grade} {n} ({frac*100:.0f}%)'
        )
        angle = angle2
    legend_y_start = size + 14
    legend_lines = [
        f'<text x="0" y="{legend_y_start + i*16}" font-size="12">{ln}</text>'
        for i, ln in enumerate(legend)
    ]
    height = size + 14 + 16 * len(legend)
    return (
        f'<svg class="grade-pie" width="{size}" height="{height}" '
        f'viewBox="0 0 {size} {height}" role="img" aria-label="来源分级饼图">'
        + "".join(parts)
        + "".join(legend_lines)
        + "</svg>"
    )


def timeline_svg(events: Sequence[Dict[str, Any]], width: int = 760) -> str:
    if not events:
        return '<svg class="timeline-svg" width="100" height="40"><text x="0" y="20">无事件</text></svg>'
    # 提取年份；若无 year 字段，按顺序均匀分布
    years: List[Optional[float]] = []
    for ev in events:
        y = ev.get("year") if isinstance(ev, dict) else None
        try:
            years.append(float(y) if y is not None else None)
        except (TypeError, ValueError):
            years.append(None)
    valid = [y for y in years if y is not None]
    if valid and len(set(valid)) > 1:
        ymin, ymax = min(valid), max(valid)
    else:
        ymin, ymax = 0.0, max(1, len(events) - 1)
        years = [float(i) for i in range(len(events))]
    pad = 40
    inner_w = width - 2 * pad
    height = 220
    axis_y = 90
    parts: List[str] = [
        f'<line x1="{pad}" y1="{axis_y}" x2="{width-pad}" y2="{axis_y}" stroke="#444" stroke-width="1"/>'
    ]
    for i, ev in enumerate(events):
        y = years[i]
        if y is None:
            y = ymin + (ymax - ymin) * (i / max(1, len(events) - 1))
        if ymax == ymin:
            x = pad + inner_w / 2
        else:
            x = pad + inner_w * (y - ymin) / (ymax - ymin)
        label = html.escape(str(ev.get("event", ev.get("text", ""))))
        year_lbl = html.escape(str(ev.get("year", "")))
        flip = i % 2 == 0
        ty = axis_y - 14 if flip else axis_y + 28
        line_y = axis_y - 4 if flip else axis_y + 4
        line_y2 = axis_y - 50 if flip else axis_y + 50
        parts.append(
            f'<line x1="{x:.1f}" y1="{line_y}" x2="{x:.1f}" y2="{line_y2}" stroke="#7a1f1f" stroke-width="1"/>'
        )
        parts.append(
            f'<circle cx="{x:.1f}" cy="{axis_y}" r="4" fill="#7a1f1f"/>'
        )
        parts.append(
            f'<text x="{x:.1f}" y="{ty}" text-anchor="middle" font-size="11" fill="#222">{year_lbl}</text>'
        )
        parts.append(
            f'<text x="{x:.1f}" y="{ty + (-14 if flip else 14)}" text-anchor="middle" font-size="11" fill="#444">{label}</text>'
        )
    return (
        f'<svg class="timeline-svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="时间轴">'
        + "".join(parts)
        + "</svg>"
    )


def _esc(v: Any) -> str:
    return html.escape(_stringify(v), quote=True)


def players_table_html(players: Sequence[Any]) -> str:
    if not players:
        return '<p class="muted">未提供玩家数据</p>'
    rows: List[str] = []
    for p in players:
        if isinstance(p, dict):
            name = html.escape(str(p.get("name", "未提供")))
            role = html.escape(str(p.get("role", p.get("category", ""))))
            note = html.escape(str(p.get("note", p.get("desc", ""))))
            rel = html.escape(str(p.get("relation", "")))
        else:
            name, role, note, rel = html.escape(str(p)), "", "", ""
        rows.append(
            f"<tr><td>{name}</td><td>{role}</td><td>{rel}</td><td>{note}</td></tr>"
        )
    return (
        '<table class="players-table"><thead><tr>'
        "<th>玩家</th><th>角色/类别</th><th>关系</th><th>备注</th>"
        "</tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table>"
    )


# ---------- 数据预处理 ----------

REQUIRED_TOP = [
    "domain",
    "tier",
    "thesis",
    "facts",
    "mechanisms",
    "viewpoints",
]

PLACEHOLDER = "未提供"


def warn(msg: str) -> None:
    print(f"[render.py warning] {msg}", file=sys.stderr)


def normalize(data: Dict[str, Any]) -> Dict[str, Any]:
    for k in REQUIRED_TOP:
        if k not in data or data[k] in (None, "", []):
            warn(f"缺字段：{k}（注入占位）")
    data.setdefault("domain", PLACEHOLDER)
    data.setdefault("domain_slug", "domain")
    data.setdefault("tier", "medium")
    data.setdefault("preset", "tech")
    data.setdefault("cutoff_date", PLACEHOLDER)
    data.setdefault("thesis", PLACEHOLDER)
    data.setdefault("ai_disclaimer", "")

    skel = data.setdefault("skeleton", {})
    for k in ("concepts", "players", "timeline", "tensions", "learning_path"):
        skel.setdefault(k, [])

    data.setdefault("facts", [])
    data.setdefault("mechanisms", [])
    data.setdefault("viewpoints", [])
    data.setdefault("reflexivity", {})
    data.setdefault("isomorphisms", [])
    data.setdefault("structure_layer", {})
    data.setdefault("paradigm_layer", {})
    data.setdefault("known_unknowns", [])
    data.setdefault("self_check_questions", [])
    data.setdefault("experts", [])
    data.setdefault("sources", [])
    data.setdefault("misreadings", [])
    data.setdefault("blind_spots", [])

    # facts: 给数字 anchor，方便 quality_check 通过 id="fact-N" 数
    fact_id_to_anchor: Dict[str, str] = {}
    for i, f in enumerate(data["facts"], start=1):
        f.setdefault("id", f"f{i}")
        f["anchor"] = f"fact-{i}"
        fact_id_to_anchor[str(f["id"])] = f["anchor"]
        fact_id_to_anchor[str(i)] = f["anchor"]
        f.setdefault("text", PLACEHOLDER)
        f.setdefault("source", PLACEHOLDER)
        g = (f.get("grade") or "C").upper()
        if g not in GRADE_COLORS:
            g = "C"
        f["grade"] = g

    # mechanisms / viewpoints id；将 fact_refs 翻译成可点击的锚点 list
    for i, m in enumerate(data["mechanisms"], start=1):
        m.setdefault("id", f"m{i}")
        m.setdefault("text", PLACEHOLDER)
        m.setdefault("fact_refs", [])
        m["fact_anchors"] = [
            {"anchor": fact_id_to_anchor.get(str(r), f"fact-{r}"), "label": str(r)}
            for r in m["fact_refs"]
        ]
    for i, v in enumerate(data["viewpoints"], start=1):
        v.setdefault("id", f"v{i}")
        v.setdefault("text", PLACEHOLDER)
        v.setdefault("mechanism_refs", [])
        v.setdefault("counter_evidence", PLACEHOLDER)

    # 派生字段
    grade_counts: Dict[str, int] = {"A": 0, "B": 0, "C": 0, "D": 0}
    for f in data["facts"]:
        grade_counts[f["grade"]] = grade_counts.get(f["grade"], 0) + 1
    data["grade_counts"] = grade_counts
    data["grade_pie_svg"] = grade_pie_svg(grade_counts)
    data["timeline_svg"] = timeline_svg(skel.get("timeline", []))
    data["players_table_html"] = players_table_html(skel.get("players", []))

    # 来源分级表行
    total = sum(grade_counts.values()) or 1
    rows: List[str] = []
    for g in ("A", "B", "C", "D"):
        n = grade_counts.get(g, 0)
        pct = n * 100 / total
        rows.append(
            f'<tr><td class="grade-{g}">{g}</td><td>{n}</td><td>{pct:.1f}%</td></tr>'
        )
    data["source_grading_table_html"] = (
        '<table class="source-grading-table">'
        "<thead><tr><th>等级</th><th>数量</th><th>占比</th></tr></thead>"
        "<tbody>" + "".join(rows) + "</tbody></table>"
    )

    # 顶部小占位符（百分比、tier 标签、阅读时间、生成日期等）
    pct_str = lambda g: f"{grade_counts.get(g, 0)*100/total:.0f}%"
    data["grade_a_pct"] = pct_str("A")
    data["grade_b_pct"] = pct_str("B")
    data["grade_c_pct"] = pct_str("C")
    data["grade_d_pct"] = pct_str("D")

    tier = data.get("tier", "medium")
    tier_label_map = {
        "flash": "⚡ 闪研",
        "medium": "📖 精研",
        "deep": "🔬 深研",
    }
    reading_time_map = {
        "flash": "约 30 分钟",
        "medium": "约 60 分钟",
        "deep": "约 90 分钟",
    }
    data["tier_label"] = tier_label_map.get(tier, "📖 精研")
    data["reading_time"] = reading_time_map.get(tier, "约 60 分钟")
    data["fact_count"] = len(data["facts"])
    data.setdefault("domain_name", data.get("domain", PLACEHOLDER))
    data.setdefault(
        "thesis_one_liner", data.get("thesis", PLACEHOLDER)
    )
    data["generation_date"] = datetime.date.today().isoformat()

    # 预渲染 HTML 片段
    build_html_fragments(data)

    return data


# ---------- HTML 片段预渲染 ----------

def _render_concepts_html(items: Sequence[Any]) -> str:
    if not items:
        return '<p class="muted">未提供核心概念</p>'
    rows: List[str] = []
    for c in items:
        if isinstance(c, dict):
            term = _esc(c.get("term", PLACEHOLDER))
            explain = _esc(c.get("explain", c.get("def", "")))
        else:
            term, explain = _esc(c), ""
        rows.append(
            f'<li><strong class="jargon">{term}</strong>'
            + (f' — {explain}' if explain else '')
            + '</li>'
        )
    return '<ul class="concepts-list">' + "".join(rows) + "</ul>"


def _render_players_html(players: Sequence[Any]) -> str:
    if not players:
        return '<p class="muted">未提供玩家数据</p>'
    rows: List[str] = []
    for p in players:
        if isinstance(p, dict):
            name = _esc(p.get("name", PLACEHOLDER))
            ptype = _esc(p.get("type", p.get("role", p.get("category", ""))))
            ctx = _esc(p.get("context", p.get("note", p.get("desc", ""))))
            rel = _esc(p.get("relation", ""))
        else:
            name, ptype, ctx, rel = _esc(p), "", "", ""
        rows.append(
            f"<tr><td>{name}</td><td>{ptype}</td><td>{rel}</td><td>{ctx}</td></tr>"
        )
    return (
        '<table class="players-table"><thead><tr>'
        "<th>玩家</th><th>类别</th><th>关系</th><th>背景/说明</th>"
        "</tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table>"
    )


def _render_timeline_html(events: Sequence[Any], svg: str) -> str:
    parts = [svg or ""]
    if events:
        rows: List[str] = []
        for ev in events:
            if isinstance(ev, dict):
                year = _esc(ev.get("year", ""))
                text = _esc(ev.get("event", ev.get("text", "")))
            else:
                year, text = "", _esc(ev)
            rows.append(f"<li><strong>{year}</strong> · {text}</li>")
        parts.append('<ol class="timeline-list">' + "".join(rows) + "</ol>")
    return "\n".join(parts)


def _render_tensions_html(items: Sequence[Any]) -> str:
    if not items:
        return '<p class="muted">未提供矛盾结构</p>'
    rows = []
    for t in items:
        if isinstance(t, dict):
            text = _esc(t.get("text", t.get("tension", str(t))))
        else:
            text = _esc(t)
        rows.append(f"<li>{text}</li>")
    return '<ul class="tensions-list">' + "".join(rows) + "</ul>"


def _render_learning_path_html(items: Sequence[Any]) -> str:
    if not items:
        return '<p class="muted">未提供学习路径</p>'
    blocks: List[str] = []
    for it in items:
        if isinstance(it, dict):
            cat = _esc(it.get("category", it.get("phase", PLACEHOLDER)))
            sub = it.get("items", it.get("list", []))
            if isinstance(sub, list) and sub:
                lis = "".join(f"<li>{_esc(x)}</li>" for x in sub)
                blocks.append(
                    f'<div class="learning-step"><h4>{cat}</h4>'
                    f'<ul>{lis}</ul></div>'
                )
            else:
                desc = _esc(it.get("desc", it.get("text", "")))
                blocks.append(
                    f'<div class="learning-step"><h4>{cat}</h4><p>{desc}</p></div>'
                )
        else:
            blocks.append(f"<li>{_esc(it)}</li>")
    if all(b.startswith("<li>") for b in blocks):
        return '<ol class="learning-path-list">' + "".join(blocks) + "</ol>"
    return '<div class="learning-path">' + "".join(blocks) + "</div>"


def _render_facts_html(facts: Sequence[Dict[str, Any]]) -> str:
    if not facts:
        return '<p class="muted">未提供事实</p>'
    rows: List[str] = []
    for f in facts:
        anchor = _esc(f.get("anchor", ""))
        text = _esc(f.get("text", PLACEHOLDER))
        source = _esc(f.get("source", PLACEHOLDER))
        grade = _esc(f.get("grade", "C"))
        grade_lc = grade.lower()
        rows.append(
            f'<li id="{anchor}" class="fact-anchor fact">'
            f'<span class="fact-text">{text}</span> '
            f'<span class="fact-source muted">— {source}</span>'
            f'<span class="grade grade-{grade_lc}">{grade}</span>'
            f'</li>'
        )
    return '<ol class="facts-list">' + "".join(rows) + "</ol>"


def _render_mechanisms_html(mechs: Sequence[Dict[str, Any]]) -> str:
    if not mechs:
        return '<p class="muted">未提供机制</p>'
    blocks: List[str] = []
    for m in mechs:
        text = _esc(m.get("text", PLACEHOLDER))
        mid = _esc(m.get("id", ""))
        anchors = m.get("fact_anchors", [])
        # 数据属性里放原始引用
        refs_attr = ",".join(_stringify(r) for r in m.get("fact_refs", []))
        ref_links = "".join(
            f'<a class="fact-ref" href="#{a.get("anchor","")}">{html.escape(_stringify(a.get("label","")))}</a> '
            for a in anchors
        )
        blocks.append(
            f'<div class="mechanism" id="{mid}" data-fact-refs="{html.escape(refs_attr, quote=True)}">'
            f'<p class="mech-text"><strong>机制：</strong>{text}</p>'
            f'<p class="mech-refs muted">支撑事实：{ref_links}</p>'
            f'</div>'
        )
    return "\n".join(blocks)


def _render_viewpoints_html(views: Sequence[Dict[str, Any]]) -> str:
    if not views:
        return '<p class="muted">未提供观点</p>'
    blocks: List[str] = []
    for v in views:
        text = _esc(v.get("text", PLACEHOLDER))
        vid = _esc(v.get("id", ""))
        counter = v.get("counter_evidence") or ""
        counter_html = ""
        if counter and counter != PLACEHOLDER:
            counter_html = (
                f'<div class="counter">{_esc(counter)}</div>'
            )
        else:
            counter_html = (
                '<div class="counter">反例：暂无明确反证；证伪条件待补。</div>'
            )
        m_refs = v.get("mechanism_refs", [])
        m_links = "".join(
            f'<a href="#{_esc(r)}">{_esc(r)}</a> ' for r in m_refs
        )
        blocks.append(
            f'<div class="viewpoint" id="{vid}">'
            f'<p class="vp-text"><strong>观点：</strong>{text}</p>'
            f'{counter_html}'
            + (
                f'<p class="vp-refs muted">基于机制：{m_links}</p>'
                if m_links
                else ''
            )
            + '</div>'
        )
    return "\n".join(blocks)


def _render_reflexivity_html(refl: Dict[str, Any]) -> str:
    if not refl:
        return '<p class="muted">未提供反身性分析</p>'
    narrative = _esc(refl.get("narrative", PLACEHOLDER))
    self_re = _esc(refl.get("self_reinforce", PLACEHOLDER))
    fail = _esc(refl.get("failure_condition", PLACEHOLDER))
    return (
        '<dl class="reflexivity">'
        f'<dt>主流叙事</dt><dd>{narrative}</dd>'
        f'<dt>自我证实链路</dt><dd>{self_re}</dd>'
        f'<dt>失效条件（如果……则叙事崩塌）</dt><dd>{fail}</dd>'
        '</dl>'
    )


def _render_misconceptions_html(mis: Sequence[Any], blind: Sequence[Any]) -> str:
    parts: List[str] = []
    if mis:
        lis = "".join(f"<li>{_esc(x)}</li>" for x in mis)
        parts.append(f"<h3>外部误读</h3><ul>{lis}</ul>")
    if blind:
        lis = "".join(f"<li>{_esc(x)}</li>" for x in blind)
        parts.append(f"<h3>局内人盲区</h3><ul>{lis}</ul>")
    if not parts:
        return '<p class="muted">未提供认知误区</p>'
    return "\n".join(parts)


def _render_kv_html(d: Dict[str, Any], empty_msg: str) -> str:
    if not d:
        return f'<p class="muted">{empty_msg}</p>'
    rows: List[str] = []
    for k, v in d.items():
        rows.append(f"<dt>{_esc(k)}</dt><dd>{_esc(v)}</dd>")
    return "<dl>" + "".join(rows) + "</dl>"


def _render_isomorphism_html(items: Sequence[Any]) -> str:
    if not items:
        return '<p class="muted">未提供跨领域同构案例</p>'
    blocks: List[str] = []
    for it in items:
        if isinstance(it, dict):
            src = _esc(it.get("source", PLACEHOLDER))
            sim = _esc(it.get("similarity", PLACEHOLDER))
            anti = _esc(it.get("anti_similarity", PLACEHOLDER))
            blocks.append(
                '<div class="isomorphism">'
                f'<h4>对照：{src}</h4>'
                f'<p><strong>同构点：</strong>{sim}</p>'
                f'<p><strong>反同构点（不能照搬）：</strong>{anti}</p>'
                '</div>'
            )
        else:
            blocks.append(f"<p>{_esc(it)}</p>")
    return "\n".join(blocks)


def _render_known_unknowns_html(items: Sequence[Any]) -> str:
    if not items:
        return (
            '<ul id="known-unknowns-list" class="unknowns-list">'
            '<li>未提供已知的未知清单</li></ul>'
        )
    rows: List[str] = []
    for u in items:
        if isinstance(u, dict):
            q = _esc(u.get("q", u.get("question", PLACEHOLDER)))
            where = _esc(u.get("where", u.get("hint", "")))
            extra = (
                f' <span class="muted">（线索：{where}）</span>' if where else ''
            )
            rows.append(f"<li>{q}{extra}</li>")
        else:
            rows.append(f"<li>{_esc(u)}</li>")
    return (
        '<ul id="known-unknowns-list" class="unknowns-list">'
        + "".join(rows)
        + '</ul>'
    )


def _render_self_check_html(qs: Sequence[Any]) -> str:
    if not qs:
        return '<p class="muted">未提供自检题</p>'
    blocks: List[str] = []
    for q in qs:
        if isinstance(q, dict):
            qt = _esc(q.get("q", q.get("question", PLACEHOLDER)))
            ans = _esc(q.get("a", q.get("answer", "")))
            blocks.append(
                '<details class="self-check">'
                f'<summary>{qt}</summary>'
                f'<div class="answer">{ans}</div>'
                '</details>'
            )
        else:
            blocks.append(
                '<details class="self-check">'
                f'<summary>{_esc(q)}</summary>'
                '</details>'
            )
    return "\n".join(blocks)


def _render_sources_list_html(facts: Sequence[Dict[str, Any]], sources: Sequence[Any]) -> str:
    rows: List[str] = []
    for f in facts:
        anchor = _esc(f.get("anchor", ""))
        text = _esc(f.get("text", PLACEHOLDER))
        source = _esc(f.get("source", PLACEHOLDER))
        grade = _esc(f.get("grade", "C"))
        grade_lc = grade.lower()
        rows.append(
            f'<li id="src-{anchor}"><a href="#{anchor}">{anchor}</a> '
            f'<span class="grade grade-{grade_lc}">{grade}</span> '
            f'{text} <span class="muted">— {source}</span></li>'
        )
    if not rows:
        return '<p class="muted">未提供来源</p>'
    return '<ol class="sources-list">' + "".join(rows) + "</ol>"


def _render_recommendations_html(experts: Sequence[Any]) -> str:
    if not experts:
        return (
            '<ul class="recommendations-list">'
            '<li>未提供推荐人/账号/社区——读者应自行寻找一手发声者</li>'
            '<li>建议：从领域顶级会议演讲者、长期写作的从业者、被反复引用的研究者入手</li>'
            '<li>验证方法：交叉对比 ≥3 位独立来源，看观点分歧而非共识</li>'
            '</ul>'
        )
    rows: List[str] = []
    for e in experts:
        if isinstance(e, dict):
            name = _esc(e.get("name", PLACEHOLDER))
            ctx = _esc(e.get("context", e.get("desc", "")))
            rows.append(f"<li><strong>{name}</strong> — {ctx}</li>")
        else:
            rows.append(f"<li>{_esc(e)}</li>")
    return '<ul class="recommendations-list">' + "".join(rows) + "</ul>"


def _render_ai_disclaimer_extra_html(text: str) -> str:
    if not text:
        return ""
    return f'<p class="ai-disclaimer-extra">{_esc(text)}</p>'


def build_html_fragments(data: Dict[str, Any]) -> None:
    """把结构化字段预渲染成 HTML 字符串，注入 ctx 的 *_html 字段。"""
    skel = data.get("skeleton", {})
    data["concepts_html"] = _render_concepts_html(skel.get("concepts", []))
    data["players_html"] = _render_players_html(skel.get("players", []))
    data["timeline_html"] = _render_timeline_html(
        skel.get("timeline", []), data.get("timeline_svg", "")
    )
    data["tensions_html"] = _render_tensions_html(skel.get("tensions", []))
    data["learning_path_html"] = _render_learning_path_html(
        skel.get("learning_path", [])
    )
    data["facts_html"] = _render_facts_html(data.get("facts", []))
    data["mechanisms_html"] = _render_mechanisms_html(data.get("mechanisms", []))
    data["viewpoints_html"] = _render_viewpoints_html(data.get("viewpoints", []))
    data["reflexivity_html"] = _render_reflexivity_html(data.get("reflexivity", {}))
    data["misconceptions_html"] = _render_misconceptions_html(
        data.get("misreadings", []), data.get("blind_spots", [])
    )
    data["structure_html"] = _render_kv_html(
        data.get("structure_layer", {}),
        "未提供结构层分析（深研档建议补：reality-shaping 约束、替换条件后的形态变化）",
    )
    data["paradigm_html"] = _render_kv_html(
        data.get("paradigm_layer", {}),
        "未提供范式层分析（深研档建议补：硬核 / 异端 / 范式切换信号）",
    )
    data["isomorphism_html"] = _render_isomorphism_html(data.get("isomorphisms", []))
    data["known_unknowns_html"] = _render_known_unknowns_html(
        data.get("known_unknowns", [])
    )
    data["self_check_html"] = _render_self_check_html(
        data.get("self_check_questions", [])
    )
    data["sources_list_html"] = _render_sources_list_html(
        data.get("facts", []), data.get("sources", [])
    )
    data["recommendations_html"] = _render_recommendations_html(
        data.get("experts", [])
    )
    data["ai_disclaimer_extra_html"] = _render_ai_disclaimer_extra_html(
        data.get("ai_disclaimer", "")
    )


# ---------- 默认模板 fallback ----------

def default_template() -> str:
    """模板未就绪时使用的兜底模板，保证脚本可独立运行。"""
    return r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{domain}} · 领域速通</title>
<style>
:root { --fg:#1a1a1a; --bg:#fbfaf6; --accent:#7a1f1f; --muted:#666; --rule:#d8d3c4; }
@media (prefers-color-scheme: dark) {
  :root { --fg:#e8e4d8; --bg:#15140f; --accent:#c98a3a; --muted:#999; --rule:#3a382f; }
}
[data-theme="dark"] { --fg:#e8e4d8; --bg:#15140f; --accent:#c98a3a; --muted:#999; --rule:#3a382f; }
* { box-sizing: border-box; }
html, body { background: var(--bg); color: var(--fg); }
body { font-family: "Songti SC", "STSong", "SimSun", "Noto Serif CJK SC", serif;
  max-width: 820px; margin: 0 auto; padding: 2rem 1.2rem; line-height: 1.75; }
h1, h2, h3 { font-weight: 600; letter-spacing: 0.02em; }
h1 { font-size: 1.8rem; border-bottom: 2px solid var(--accent); padding-bottom: .4rem; }
h2 { font-size: 1.3rem; margin-top: 2rem; color: var(--accent); }
h3 { font-size: 1.1rem; margin-top: 1.4rem; }
.thesis { font-size: 1.15rem; padding: .8rem 1rem; border-left: 3px solid var(--accent);
  background: rgba(122,31,31,.04); margin: 1rem 0; }
.tier-controls { margin: 1rem 0; }
.tier-controls button { font-family: inherit; padding: .3rem .8rem; margin-right: .4rem;
  background: var(--bg); color: var(--fg); border: 1px solid var(--rule); cursor: pointer; }
.tier-controls button.active { background: var(--accent); color: #fff; border-color: var(--accent); }
.tier-medium, .tier-deep { display: none; }
body.show-medium .tier-medium, body.show-deep .tier-medium { display: block; }
body.show-deep .tier-deep { display: block; }
table { border-collapse: collapse; width: 100%; margin: .8rem 0; font-size: .95rem; }
th, td { border: 1px solid var(--rule); padding: .4rem .6rem; text-align: left; }
th { background: rgba(122,31,31,.06); }
code, .jargon { font-family: "JetBrains Mono", "SF Mono", Menlo, Consolas, monospace;
  font-size: .9em; background: rgba(0,0,0,.04); padding: 0 .2em; border-radius: 2px; }
.fact { padding: .3rem .6rem; border-left: 2px solid var(--accent); margin: .4rem 0;
  background: rgba(0,0,0,.02); }
.grade-A { color: #7a1f1f; font-weight: 600; }
.grade-B { color: #c98a3a; font-weight: 600; }
.grade-C { color: #5b6f8a; }
.grade-D { color: #9a9a9a; }
.muted { color: var(--muted); }
.source-grading-table { max-width: 320px; }
.players-table th { white-space: nowrap; }
.disclaimer { border: 1px dashed var(--rule); padding: 1rem; margin: 2rem 0;
  background: rgba(0,0,0,.02); font-size: .95rem; }
.viewpoint { margin: 1rem 0; padding: .6rem 1rem; border-left: 3px solid var(--accent); }
.counter { color: var(--muted); font-style: italic; margin-top: .3rem; }
.counter::before { content: "反例 / "; color: var(--accent); font-style: normal; font-weight: 600; }
@media print { @page { size: A4; margin: 1.6cm; } .tier-controls { display:none; } }
</style>
</head>
<body class="show-deep">
<header>
  <h1>{{domain}} · 领域速通</h1>
  <p class="muted">cutoff: {{cutoff_date}} · tier: {{tier}} · preset: {{preset}}</p>
  <p class="thesis">{{thesis}}</p>
  <div class="tier-controls" role="tablist">
    <button data-tier="flash">闪研 30min</button>
    <button data-tier="medium">精研 60min</button>
    <button data-tier="deep" class="active">深研 90min</button>
  </div>
</header>

<section class="tier-flash">
  <h2>骨架五件套</h2>
  <h3>核心概念</h3>
  <ul>{{#each skeleton.concepts}}<li><span class="jargon">{{this.term}}</span> — {{this.def}}</li>{{/each}}</ul>
  <h3>玩家地图</h3>
  {{{players_table_html}}}
  <h3>时间轴</h3>
  {{{timeline_svg}}}
  <h3>矛盾结构</h3>
  <ul>{{#each skeleton.tensions}}<li>{{this}}</li>{{/each}}</ul>
  <h2>关键事实（最重要的几条）</h2>
  {{#each facts}}<div class="fact" id="{{this.anchor}}">[<span class="grade-{{this.grade}}">{{this.grade}}</span>] {{this.text}} <span class="muted">— {{this.source}}</span></div>{{/each}}
</section>

<section class="tier-medium">
  <h2>机制层</h2>
  {{#each mechanisms}}
  <div class="mechanism" id="{{this.id}}" data-fact-refs="{{#each this.fact_refs}}{{this}},{{/each}}"><strong>{{this.text}}</strong>
    <div class="muted">支撑事实：{{#each this.fact_anchors}}<a href="#{{this.anchor}}">{{this.label}}</a> {{/each}}</div>
  </div>
  {{/each}}
  <h2>观点层</h2>
  {{#each viewpoints}}
  <div class="viewpoint" id="{{this.id}}">{{this.text}}
    <div class="counter">{{this.counter_evidence}}</div>
    <div class="muted">基于机制：{{#each this.mechanism_refs}}<a href="#{{this}}">{{this}}</a> {{/each}}</div>
  </div>
  {{/each}}
  <h2>反身性元透镜</h2>
  <p><strong>主流叙事：</strong>{{reflexivity.narrative}}</p>
  <p><strong>自我证实链路：</strong>{{reflexivity.self_reinforce}}</p>
  <p><strong>失效条件：</strong>{{reflexivity.failure_condition}}</p>
  <h2>来源分级</h2>
  {{{grade_pie_svg}}}
  {{{source_grading_table_html}}}
  <h2>行业认知误区与盲区</h2>
  <h3>外部误读</h3>
  <ul>{{#each misreadings}}<li>{{this}}</li>{{/each}}</ul>
  <h3>局内人盲区</h3>
  <ul>{{#each blind_spots}}<li>{{this}}</li>{{/each}}</ul>
</section>

<section class="tier-deep">
  <h2>结构层</h2>
  <dl>{{#each structure_layer}}<dt>{{@key}}</dt><dd>{{this}}</dd>{{/each}}</dl>
  <h2>范式层</h2>
  <dl>{{#each paradigm_layer}}<dt>{{@key}}</dt><dd>{{this}}</dd>{{/each}}</dl>
  <h2>跨领域同构</h2>
  {{#each isomorphisms}}
  <div><h3>对照：{{this.source}}</h3>
    <p><strong>同构点：</strong>{{this.similarity}}</p>
    <p><strong>反同构点（不能照搬）：</strong>{{this.anti_similarity}}</p>
  </div>
  {{/each}}
  <h2>学习路径</h2>
  <ol>{{#each skeleton.learning_path}}<li>{{this}}</li>{{/each}}</ol>
  <h2>自检题</h2>
  <ol>{{#each self_check_questions}}<li>{{this}}</li>{{/each}}</ol>
</section>

<section>
  <h2>已知的未知（known unknowns）</h2>
  <ul>{{#each known_unknowns}}<li>{{this}}</li>{{/each}}</ul>
  <h2>推荐人 / 账号 / 社区</h2>
  <ul>{{#each experts}}<li><strong>{{this.name}}</strong> — {{this.context}}</li>{{/each}}</ul>
  <h2>来源清单</h2>
  <ol>{{#each sources}}<li>{{this}}</li>{{/each}}</ol>
</section>

<section id="ai-disclaimer" class="disclaimer">
  <h2>AI 视角局限性 disclaimer</h2>
  <p>模型 cutoff: {{cutoff_date}}。此后的进展不在掌握范围。</p>
  <p>{{ai_disclaimer}}</p>
  <p class="muted">AI 是主流叙事的载体——读完请去找上面的真人专家交叉验证。</p>
</section>

<script>
(function(){
  var body = document.body;
  var btns = document.querySelectorAll('.tier-controls button');
  function setTier(t) {
    body.classList.remove('show-medium','show-deep');
    if (t === 'medium') body.classList.add('show-medium');
    if (t === 'deep') body.classList.add('show-medium','show-deep');
    btns.forEach(function(b){ b.classList.toggle('active', b.dataset.tier === t); });
  }
  btns.forEach(function(b){ b.addEventListener('click', function(){ setTier(b.dataset.tier); }); });
  setTier('{{tier}}');
})();
</script>
</body>
</html>
"""


# ---------- 主流程 ----------

def render(data: Dict[str, Any], template: str) -> str:
    return render_template(template, data)


def word_count(text: str) -> int:
    # 粗略估算：去 HTML 标签后，中文按字符计、英文按词计
    plain = re.sub(r"<[^>]+>", " ", text)
    plain = re.sub(r"\s+", " ", plain).strip()
    cn = len(re.findall(r"[一-鿿]", plain))
    en = len(re.findall(r"[A-Za-z]+", plain))
    return cn + en


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="domain.json → 单文件 HTML 渲染器")
    ap.add_argument("input", help="domain.json 路径")
    ap.add_argument("-o", "--output", required=True, help="输出 HTML 路径")
    ap.add_argument(
        "--template",
        default=None,
        help="HTML 模板路径（默认 ../assets/html-template.html）",
    )
    args = ap.parse_args(argv)

    in_path = Path(args.input)
    if not in_path.exists():
        print(f"[render.py error] 找不到输入文件：{in_path}", file=sys.stderr)
        return 2
    try:
        data = json.loads(in_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"[render.py error] JSON 解析失败：{e}", file=sys.stderr)
        return 2
    if not isinstance(data, dict):
        print("[render.py error] 顶层必须是 object", file=sys.stderr)
        return 2

    tpl_path = Path(
        args.template
        or (Path(__file__).resolve().parent.parent / "assets" / "html-template.html")
    )
    if tpl_path.exists():
        template = tpl_path.read_text(encoding="utf-8")
    else:
        warn(f"模板不存在：{tpl_path}，使用内置兜底模板")
        template = default_template()

    data = normalize(data)
    out = render(data, template)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(out, encoding="utf-8")

    # 渲染统计
    gc = data["grade_counts"]
    total_g = sum(gc.values()) or 1
    pcts = " ".join(f"{g}:{gc[g]*100/total_g:.0f}%" for g in ("A", "B", "C", "D"))
    wc = word_count(out)
    print(
        f"[render.py] OK → {out_path}\n"
        f"  facts={len(data['facts'])} mechanisms={len(data['mechanisms'])} "
        f"viewpoints={len(data['viewpoints'])}\n"
        f"  grade_pct: {pcts}\n"
        f"  word_count≈{wc}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
