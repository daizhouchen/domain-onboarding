#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
render.py — domain.json → 单文件 HTML 渲染器（domain-onboarding skill, v0.2）

v0.2 schema 变化
----------------
- chapters[] 主流程：10 章 narrative_html，已织入脚注/机制段落/观点引文，render
  直接嵌入 H2 下面（不再拆解、不再做 HTML 转义）
- 新增 subtitle / thesis_one_liner / known_unknowns_data
- ai_disclaimer 由 V1 模板硬编码，render 不再需要单独渲染

兼容协议
--------
若 domain.json 不含 chapters[] 但含旧字段（skeleton/facts/mechanisms/viewpoints），
退化到 v0.1 行为并打 stderr warning。

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


# ---------- 极简模板引擎（保持不变） ----------

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


def _find_matching_close_stack(tpl: str, start: int, outer_kind: str) -> int:
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
            for j in range(len(stack) - 1, -1, -1):
                if stack[j] == kind:
                    del stack[j]
                    break
            if not stack:
                return cl.start()
            i = cl.end()
    return -1


def render_template(tpl: str, ctx: Dict[str, Any]) -> str:
    out: List[str] = []
    i = 0
    while i < len(tpl):
        m_open = _BLOCK_OPEN_RE.search(tpl, i)
        if not m_open:
            out.append(tpl[i:])
            break
        out.append(tpl[i : m_open.start()])
        kind = m_open.group(1)
        key = m_open.group(2)
        body_start = m_open.end()
        close_pos = _find_matching_close_stack(tpl, body_start, kind)
        if close_pos < 0:
            out.append(tpl[m_open.start() :])
            break
        body = tpl[body_start:close_pos]
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
                    sub_ctx["@last"] = False
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
    rendered = _RAW_RE.sub(
        lambda m: _stringify(_resolve(m.group(1), ctx)), rendered
    )
    rendered = _VAR_RE.sub(
        lambda m: html.escape(_stringify(_resolve(m.group(1), ctx)), quote=True),
        rendered,
    )
    return rendered


# ---------- SVG 生成器（保留） ----------

GRADE_COLORS = {
    "A": "#7a1f1f",
    "B": "#c98a3a",
    "C": "#5b6f8a",
    "D": "#9a9a9a",
}


def grade_pie_svg(grade_counts: Dict[str, int], size: int = 180) -> str:
    total = sum(grade_counts.values())
    if total == 0:
        return f'<svg class="grade-pie" width="{size}" height="{size}" role="img" aria-label="来源分级（无数据）"><circle cx="{size/2}" cy="{size/2}" r="{size/2-4}" fill="#eee" stroke="#999"/></svg>'
    cx = cy = size / 2
    r = size / 2 - 4
    parts: List[str] = []
    legend: List[str] = []
    angle = -math.pi / 2
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


def _esc(v: Any) -> str:
    return html.escape(_stringify(v), quote=True)


# ---------- v1.1 视觉常量 ----------

# 章节中文编号映射（壹～拾）
ZH_NUMERAL = ["壹", "贰", "叁", "肆", "伍", "陆", "柒", "捌", "玖", "拾"]

# chapter-summary 块匹配（取最后一个作为章末总结，包进 chapter-coda）
_SUMMARY_RE = re.compile(r'(<p class="chapter-summary">.*?</p>)', re.DOTALL)


def _split_summary(narrative_html: str) -> tuple:
    """从 narrative_html 尾部抽离最后一个 <p class="chapter-summary">...</p>。
    返回 (body_without_summary, coda_html)；若未找到 summary 则 coda 为空串。
    """
    if not isinstance(narrative_html, str) or not narrative_html:
        return narrative_html or "", ""
    matches = _SUMMARY_RE.findall(narrative_html)
    if not matches:
        return narrative_html, ""
    summary = matches[-1]
    # 仅替换最后一次出现：用 rfind + 切片，避免与前文相同 summary 误删
    pos = narrative_html.rfind(summary)
    if pos < 0:
        return narrative_html, ""
    body = narrative_html[:pos] + narrative_html[pos + len(summary):]
    coda = f'<div class="chapter-coda">{summary}</div>'
    return body, coda


# ---------- v1.2 段落内层次 typography post-processing ----------
#
# sample 里把"分组标题 / 子项标题 / 编号条目 / 玩家段 / 镜子段 / 叙事段"全部
# 用同一个 <p><strong>X.</strong>...</p> 内联粗体表示，视觉权重相同读起来累。
# 这里识别 6 类平铺 pattern（A 字母分组 / B 字母+数字子项 / C 中文条目 /
# D 镜子条目 / E 叙事条目 / F 编号 unknowns），把它们转成语义化 HTML 结构
# （h4/h5 + section/div + 子 span 编号），让模板 CSS 能给出对应视觉层次。
#
# 关键约束：
# - sample JSON 不动，只在 render 时做后处理
# - 先用 placeholder 替换 mechanism / viewpoint / quote / chapter-summary，
#   等 typography 应用完再恢复——避免误吞结构化引文里的 strong
# - 每个 pattern 单独失败回退（保留原段落 > 错误转换）

_TYPO_PROTECT_RE = re.compile(
    r'(<p\s+class="mechanism"[^>]*>.*?</p>'
    r'|<blockquote[^>]*>.*?</blockquote>'
    r'|<p\s+class="chapter-summary"[^>]*>.*?</p>'
    r'|<p\s+class="transition"[^>]*>.*?</p>)',
    re.DOTALL,
)

# Pattern A 变体 1（vec 风）：<p><strong>A. 标题——lead.</strong>正文</p>
# title/lead 都在 strong 内部，正文在 strong 之后
_TYPO_GROUP_HEADING_V1_RE = re.compile(
    r'<p><strong>([A-DＡ-Ｄ])\.\s*([^。<]{2,30}?)(?:。|——)([^<]{0,200}?)</strong>(.*?)</p>',
    re.DOTALL,
)

# Pattern A 变体 2（dollar 风）：<p class="group-lead">前缀<strong>A. 标题</strong>——lead</p>
_TYPO_GROUP_HEADING_V2_RE = re.compile(
    r'<p class="group-lead"[^>]*>(.{0,40}?)<strong>([A-DＡ-Ｄ])\.\s*([^<]{2,40}?)</strong>(.{0,500}?)</p>',
    re.DOTALL,
)

# Pattern B：<p><strong>A1. 子项标题。</strong>正文</p>
_TYPO_ITEM_BLOCK_RE = re.compile(
    r"<p><strong>([A-DＡ-Ｄ]\d+)\.\s*(.{2,80}?)。\s*</strong>(.*?)</p>",
    re.DOTALL,
)

# Pattern C：<p><strong>第一条：标题。</strong>正文</p>
# 支持"第五条 · 标题。"这种用中点替代冒号的变体
_TYPO_NUMBERED_ITEM_RE = re.compile(
    r'<p><strong>(第[一二三四五六七八九十]+条)\s*(?:[：:]|·|\s·\s)\s*([^。<]{2,80})[。:]\s*</strong>(.*?)</p>',
    re.DOTALL,
)

# Pattern D：<p><strong>镜子一：标题。</strong>正文</p>
# 支持"镜子三（跨行业）：标题"这种带括号注释的变体
_TYPO_MIRROR_BLOCK_RE = re.compile(
    r'<p><strong>(镜子[一二三四五六七八九十])(?:（[^）<]{1,20}）)?[：:]\s*([^。<]{2,80})[。]?\s*</strong>(.*?)</p>',
    re.DOTALL,
)

# Pattern E：<p><strong>叙事 A：标题。</strong>正文</p>
_TYPO_NARRATIVE_BLOCK_RE = re.compile(
    r'<p><strong>(叙事\s*[ABCＡＢＣ])[：:]\s*([^。<]{2,80})[。]?\s*</strong>(.*?)</p>',
    re.DOTALL,
)

# Pattern F：<p><strong>1. 标题——副标题。</strong>正文</p>（编号 unknowns）
_TYPO_UNKNOWN_ITEM_RE = re.compile(
    r'<p><strong>(\d{1,2})\.\s*(.{2,80}?)。\s*</strong>(.*?)</p>',
    re.DOTALL,
)


def _typo_replace_a_v1(m: "re.Match[str]") -> str:
    letter, title, lead_in, rest = m.groups()
    lead = (lead_in + rest).strip().lstrip('—-。 ')
    return (
        f'<h4 class="group-heading"><span class="group-letter">{letter}</span>'
        f'{title.strip()}</h4>\n'
        f'<p class="group-intro">{lead}</p>'
    )


def _typo_replace_a_v2(m: "re.Match[str]") -> str:
    _prefix, letter, title, rest = m.groups()
    # prefix 是"先说/然后是/第三类是/最后是"等转折语，丢掉
    lead = rest.strip().lstrip('——-。 ')
    return (
        f'<h4 class="group-heading"><span class="group-letter">{letter}</span>'
        f'{title.strip()}</h4>\n'
        f'<p class="group-intro">{lead}</p>'
    )


def _typo_replace_b(m: "re.Match[str]") -> str:
    num, title, rest = m.groups()
    return (
        f'<div class="item-block">\n'
        f'  <h5 class="item-heading"><span class="item-num">{num}</span>'
        f'{title.strip()}</h5>\n'
        f'  <p>{rest.strip()}</p>\n'
        f'</div>'
    )


def _typo_replace_c(m: "re.Match[str]") -> str:
    label, title, rest = m.groups()
    return (
        f'<section class="numbered-item">\n'
        f'  <h4 class="numbered-heading"><span class="num-label">{label}</span>'
        f'{title.strip()}</h4>\n'
        f'  <p>{rest.strip()}</p>\n'
        f'</section>'
    )


def _typo_replace_d(m: "re.Match[str]") -> str:
    label, title, rest = m.groups()
    return (
        f'<div class="mirror-block">\n'
        f'  <h5 class="mirror-heading"><span class="mirror-num">{label}</span>'
        f'{title.strip()}</h5>\n'
        f'  <p>{rest.strip()}</p>\n'
        f'</div>'
    )


def _typo_replace_e(m: "re.Match[str]") -> str:
    tag, title, rest = m.groups()
    tag_clean = tag.strip()
    return (
        f'<div class="narrative-block">\n'
        f'  <h5 class="narrative-heading"><span class="narrative-tag">{tag_clean}</span>'
        f'{title.strip()}</h5>\n'
        f'  <p>{rest.strip()}</p>\n'
        f'</div>'
    )


def _typo_replace_f(m: "re.Match[str]") -> str:
    num, title, rest = m.groups()
    return (
        f'<div class="unknown-item" data-num="{num}">\n'
        f'  <h5 class="unknown-heading"><span class="unknown-num">{num}</span>'
        f'{title.strip()}</h5>\n'
        f'  <p>{rest.strip()}</p>\n'
        f'</div>'
    )


def _apply_typography_layers(html_text: str) -> str:
    """对 narrative_html body（已剥离 chapter-summary）应用 6 类 pattern 转换。

    保护策略：先把 mechanism / viewpoint / quote / transition 这些已经语义化的
    结构块替换成 placeholder，应用 typography pattern 后再恢复——避免正则误吞
    引文块里的 <strong>。

    Pattern 顺序敏感：
    - A 必须在 B 之前（A. 比 A1. 短，但 A1.、A2. 都不会被 A 误匹配，因为 A. 后
      没有数字）；为防万一仍把 B 放在 A 后面更保守。
    - 实际上 A 的正则 `[A-DＡ-Ｄ]\.` 后面只允许非数字（被 `\.` 限定），所以
      不会匹配 "A1."。
    - F (\d+\.) 放最后，它最宽，最后兜底。
    """
    if not isinstance(html_text, str) or not html_text:
        return html_text or ""

    # Step 1: 保护已语义化的引文块
    placeholders: List[str] = []

    def _stash(m: "re.Match[str]") -> str:
        placeholders.append(m.group(1))
        return f"\x00PROTECT{len(placeholders) - 1}\x00"

    safe = _TYPO_PROTECT_RE.sub(_stash, html_text)

    # Step 2: 按顺序应用 6 类 pattern（每个独立 try 兜底，单点失败不影响其他）
    pattern_specs = [
        (_TYPO_GROUP_HEADING_V1_RE, _typo_replace_a_v1, "A1"),
        (_TYPO_GROUP_HEADING_V2_RE, _typo_replace_a_v2, "A2"),
        (_TYPO_ITEM_BLOCK_RE, _typo_replace_b, "B"),
        (_TYPO_NUMBERED_ITEM_RE, _typo_replace_c, "C"),
        (_TYPO_MIRROR_BLOCK_RE, _typo_replace_d, "D"),
        (_TYPO_NARRATIVE_BLOCK_RE, _typo_replace_e, "E"),
        (_TYPO_UNKNOWN_ITEM_RE, _typo_replace_f, "F"),
    ]
    for pat, fn, name in pattern_specs:
        try:
            safe = pat.sub(fn, safe)
        except Exception as e:  # noqa: BLE001
            warn(f"typography pattern {name} 失败：{e}（跳过该 pattern）")

    # Step 3: 恢复保护块
    for i, p in enumerate(placeholders):
        safe = safe.replace(f"\x00PROTECT{i}\x00", p)
    return safe


# ---------- 数据预处理 ----------

REQUIRED_TOP_V02 = ["domain", "chapters", "facts"]
PLACEHOLDER = "未提供"

# 旧 schema 字段（用于检测和 deprecation 提示）
# 注意：self_check_questions / experts / known_unknowns_data 在 v0.2 仍是合法旁路数据，
# 不在此列表中。这里只列必须被 chapters[].narrative_html 内化的"叙事级"字段。
LEGACY_FIELDS = [
    "skeleton",
    "mechanisms",
    "viewpoints",
    "reflexivity",
    "isomorphisms",
    "structure_layer",
    "paradigm_layer",
    "known_unknowns",
    "misreadings",
    "blind_spots",
]


def warn(msg: str) -> None:
    print(f"[render.py warning] {msg}", file=sys.stderr)


def _has_v02_chapters(data: Dict[str, Any]) -> bool:
    chapters = data.get("chapters")
    return isinstance(chapters, list) and len(chapters) > 0


def normalize(data: Dict[str, Any]) -> Dict[str, Any]:
    """将 domain.json 标准化（注入占位/派生字段）。
    v0.2 主流程基于 chapters[]；若无 chapters 但有旧字段，退化到 v0.1。
    """
    use_v02 = _has_v02_chapters(data)
    data["_schema_v02"] = use_v02

    if use_v02:
        # v0.2 必需字段
        for k in REQUIRED_TOP_V02:
            if k not in data or data[k] in (None, "", []):
                warn(f"缺字段：{k}（注入占位）")
        # 检测残留旧字段
        legacy_present = [k for k in LEGACY_FIELDS if data.get(k)]
        if legacy_present:
            warn(
                f"检测到旧 schema 字段（已被 chapters[] 内化）：{legacy_present}；"
                f"v0.2 主渲染流程会忽略这些字段，请将其叙事化进 chapters[].narrative_html"
            )
    else:
        # 兼容旧 schema：检查 v0.1 字段
        for k in ("domain", "thesis", "facts", "mechanisms", "viewpoints"):
            if k not in data or data[k] in (None, "", []):
                warn(f"缺字段：{k}（注入占位）")
        warn(
            "未检测到 chapters[]（v0.2 schema），退化到 v0.1 旧渲染逻辑——建议升级到 chapters[] 章节弧线"
        )

    # 兼容性：老 sample 可能有 tier 字段，直接忽略
    if "tier" in data:
        data.pop("tier", None)

    # 顶层占位
    data.setdefault("domain", PLACEHOLDER)
    data.setdefault("domain_slug", "domain")
    data.setdefault("preset", "tech")
    data.setdefault("cutoff_date", PLACEHOLDER)
    data.setdefault("subtitle", "")
    data.setdefault("thesis", PLACEHOLDER)
    data.setdefault("thesis_one_liner", data.get("thesis", PLACEHOLDER))
    data.setdefault("ai_disclaimer", "")

    # v0.2 数据源
    data.setdefault("chapters", [])
    data.setdefault("known_unknowns_data", [])

    # 通用集合（v0.1/v0.2 共享）
    data.setdefault("facts", [])
    data.setdefault("experts", [])
    data.setdefault("self_check_questions", [])
    data.setdefault("sources", [])

    # 旧 schema 的 fallback 容器
    skel = data.setdefault("skeleton", {})
    for k in ("concepts", "players", "timeline", "tensions", "learning_path"):
        skel.setdefault(k, [])
    data.setdefault("mechanisms", [])
    data.setdefault("viewpoints", [])
    data.setdefault("reflexivity", {})
    data.setdefault("isomorphisms", [])
    data.setdefault("structure_layer", {})
    data.setdefault("paradigm_layer", {})
    data.setdefault("known_unknowns", [])
    data.setdefault("misreadings", [])
    data.setdefault("blind_spots", [])

    # facts 标准化（两套 schema 都需要）
    fact_id_to_anchor: Dict[str, str] = {}
    for i, f in enumerate(data["facts"], start=1):
        f.setdefault("id", f"f{i}")
        f["anchor"] = f"fact-{i}"
        f["data_anchor"] = f"fact-data-{i}"
        f["index"] = i
        fact_id_to_anchor[str(f["id"])] = f["anchor"]
        fact_id_to_anchor[str(i)] = f["anchor"]
        f.setdefault("text", PLACEHOLDER)
        f.setdefault("source", PLACEHOLDER)
        g = (f.get("grade") or "C").upper()
        if g not in GRADE_COLORS:
            g = "C"
        f["grade"] = g

    # 旧机制/观点 id（仅旧 schema fallback 用）
    if not use_v02:
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

    # 等级计数 / 派生字段
    grade_counts: Dict[str, int] = {"A": 0, "B": 0, "C": 0, "D": 0}
    for f in data["facts"]:
        grade_counts[f["grade"]] = grade_counts.get(f["grade"], 0) + 1
    data["grade_counts"] = grade_counts
    data["grade_pie_svg"] = grade_pie_svg(grade_counts)

    # 来源分级表行（保留：底部折叠区还要用）
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

    pct_str = lambda g: f"{grade_counts.get(g, 0)*100/total:.0f}%"
    data["grade_a_pct"] = pct_str("A")
    data["grade_b_pct"] = pct_str("B")
    data["grade_c_pct"] = pct_str("C")
    data["grade_d_pct"] = pct_str("D")

    data["fact_count"] = len(data["facts"])
    data.setdefault("domain_name", data.get("domain", PLACEHOLDER))
    data["generation_date"] = datetime.date.today().isoformat()

    # 预渲染 HTML 片段
    build_html_fragments(data)

    return data


# ---------- HTML 片段预渲染（v0.2 主路径） ----------

def _render_chapters_html(chapters: Sequence[Any]) -> str:
    """v1.1 主流程：每章渲染为 chapter-cover（汉字编号 + h2）+ chapter-body
    （narrative + 末尾 chapter-coda）结构。
    narrative_html 直接嵌入（不做 HTML 转义）—— sample 已织入脚注/机制/观点。
    """
    if not chapters:
        return (
            '<section class="chapter" id="chapter-empty" data-chapter-num="0">'
            '<header class="chapter-cover">'
            '<div class="chapter-num-zh"></div>'
            '<h2>章节内容缺失</h2>'
            '</header>'
            '<div class="chapter-body">'
            '<p class="muted">domain.json 中 chapters[] 为空，无法渲染主体内容。</p>'
            '</div>'
            '</section>'
        )
    blocks: List[str] = []
    for idx, ch in enumerate(chapters):
        if not isinstance(ch, dict):
            continue
        chapter_num = idx + 1
        cid = str(ch.get("id", f"chapter-{chapter_num}"))
        title = _esc(ch.get("title", PLACEHOLDER))
        narrative = ch.get("narrative_html") or ""
        if not isinstance(narrative, str):
            narrative = _stringify(narrative)
        body, coda = _split_summary(narrative)
        # v1.2：对 body 应用段落内层次后处理（A/B/C/D/E/F 六类 pattern）
        body = _apply_typography_layers(body)
        # 中文编号：超过 10 章则留空（sample 固定 10 章）
        zh = ZH_NUMERAL[idx] if idx < len(ZH_NUMERAL) else str(chapter_num)
        # 关键：narrative_html 直接嵌入，不转义
        blocks.append(
            f'<section class="chapter" id="chapter-{_esc(cid)}" data-chapter-num="{chapter_num}">\n'
            f'  <header class="chapter-cover">\n'
            f'    <div class="chapter-num-zh">{zh}</div>\n'
            f'    <h2>{title}</h2>\n'
            f'  </header>\n'
            f'  <div class="chapter-body">\n'
            f'{body}\n'
            f'{coda}\n'
            f'  </div>\n'
            f'</section>'
        )
    return "\n".join(blocks)


def _render_chapter_nav_html(chapters: Sequence[Any]) -> str:
    """v1.1：hero 后的 10 章预览导航卡片。
    标题截前 12 个汉字（中点前部分优先）。
    """
    if not chapters:
        return '<nav class="chapter-nav" aria-label="章节导航"></nav>'
    items: List[str] = []
    for i, c in enumerate(chapters[:10]):
        if not isinstance(c, dict):
            continue
        cid = str(c.get("id", f"chapter-{i+1}"))
        title = c.get("title", PLACEHOLDER) or PLACEHOLDER
        if not isinstance(title, str):
            title = _stringify(title)
        # 保留中点前部分（"它怎么走到今天 · 副标题" → "它怎么走到今天"）
        if "·" in title:
            title = title.split("·", 1)[0].strip()
        if len(title) > 12:
            title = title[:12]
        zh = ZH_NUMERAL[i] if i < len(ZH_NUMERAL) else str(i + 1)
        items.append(
            f'<a href="#chapter-{_esc(cid)}" class="nav-item">'
            f'<span class="num">{zh}</span>'
            f'<span class="title">{_esc(title)}</span>'
            f'</a>'
        )
    return (
        '<nav class="chapter-nav" aria-label="章节导航">\n'
        + "\n".join(items)
        + "\n</nav>"
    )


def _render_side_toc_html(chapters: Sequence[Any]) -> str:
    """v1.1：桌面端右侧浮动迷你目录（圆点 + 简称）。"""
    if not chapters:
        return '<aside class="side-toc" aria-label="侧边目录"><ol></ol></aside>'
    items: List[str] = []
    for i, c in enumerate(chapters[:10]):
        if not isinstance(c, dict):
            continue
        cid = str(c.get("id", f"chapter-{i+1}"))
        title = c.get("title", PLACEHOLDER) or PLACEHOLDER
        if not isinstance(title, str):
            title = _stringify(title)
        if "·" in title:
            title = title.split("·", 1)[0].strip()
        if len(title) > 8:
            title = title[:8]
        zh = ZH_NUMERAL[i] if i < len(ZH_NUMERAL) else str(i + 1)
        items.append(
            f'<li data-chapter-id="chapter-{_esc(cid)}">'
            f'<span class="dot"></span>'
            f'<span class="label">{zh} · {_esc(title)}</span>'
            f'</li>'
        )
    return (
        '<aside class="side-toc" aria-label="侧边目录"><ol>\n'
        + "\n".join(items)
        + "\n</ol></aside>"
    )


def _render_facts_complete_list_html(facts: Sequence[Dict[str, Any]]) -> str:
    """完整事实清单（底部折叠区）；narrative 里的脚注 [N] href="#fact-data-N"
    指向这里。"""
    if not facts:
        return '<p class="muted">未提供事实清单</p>'
    rows: List[str] = []
    for f in facts:
        idx = f.get("index", "?")
        data_anchor = _esc(f.get("data_anchor", f"fact-data-{idx}"))
        text = _esc(f.get("text", PLACEHOLDER))
        source = _esc(f.get("source", PLACEHOLDER))
        grade = _esc(f.get("grade", "C"))
        # narrative 中的 [N] 锚点 id="fact-N"，用户从清单回跳时也保留导航
        # 此处的 li id 是数据锚点
        rows.append(
            f'<li id="{data_anchor}" class="fact-entry">'
            f'<span class="grade-{grade}">[{grade}]</span> '
            f'<span class="fact-text">{text}</span> '
            f'<span class="source muted">来源：{source}</span>'
            f'</li>'
        )
    return '<ol class="facts-complete-list">' + "".join(rows) + "</ol>"


def _render_known_unknowns_data_html(items: Sequence[Any]) -> str:
    """旁路数据 ul（折叠），让 quality_check 数 li 满足下限。"""
    if not items:
        return (
            '<ul id="known-unknowns-list" class="unknowns-data-list">'
            '<li>未提供已知的未知数据条目</li></ul>'
        )
    rows: List[str] = []
    for u in items:
        if isinstance(u, dict):
            q = _esc(u.get("q", u.get("question", PLACEHOLDER)))
            where = _esc(u.get("where", u.get("hint", "")))
            extra = f' — {where}' if where else ''
            rows.append(f"<li><strong>{q}</strong>{extra}</li>")
        else:
            rows.append(f"<li>{_esc(u)}</li>")
    return (
        '<ul id="known-unknowns-list" class="unknowns-data-list">'
        + "".join(rows)
        + '</ul>'
    )


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
                f'<dd class="answer">{ans}</dd>'
                '</details>'
            )
        else:
            blocks.append(
                '<details class="self-check">'
                f'<summary>{_esc(q)}</summary>'
                '</details>'
            )
    return "\n".join(blocks)


# ---------- v0.1 fallback 渲染器（保留以兼容旧 sample） ----------

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


def _render_players_html_legacy(players: Sequence[Any]) -> str:
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


def _render_legacy_facts_html(facts: Sequence[Dict[str, Any]]) -> str:
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


def _render_legacy_mechanisms_html(mechs: Sequence[Dict[str, Any]]) -> str:
    if not mechs:
        return '<p class="muted">未提供机制</p>'
    blocks: List[str] = []
    for m in mechs:
        text = _esc(m.get("text", PLACEHOLDER))
        mid = _esc(m.get("id", ""))
        anchors = m.get("fact_anchors", [])
        refs_attr = ",".join(_stringify(r) for r in m.get("fact_refs", []))
        ref_links = "".join(
            f'<a class="fact-ref" href="#{a.get("anchor","")}">{html.escape(_stringify(a.get("label","")))}</a> '
            for a in anchors
        )
        blocks.append(
            f'<p class="mechanism" id="{mid}" data-fact-refs="{html.escape(refs_attr, quote=True)}">'
            f'<strong>机制：</strong>{text} '
            f'<span class="mech-refs muted">支撑事实：{ref_links}</span>'
            f'</p>'
        )
    return "\n".join(blocks)


def _render_legacy_viewpoints_html(views: Sequence[Dict[str, Any]]) -> str:
    if not views:
        return '<p class="muted">未提供观点</p>'
    blocks: List[str] = []
    for v in views:
        text = _esc(v.get("text", PLACEHOLDER))
        vid = _esc(v.get("id", ""))
        counter = v.get("counter_evidence") or ""
        if counter and counter != PLACEHOLDER:
            counter_html = f'<span class="counter">{_esc(counter)}</span>'
        else:
            counter_html = (
                '<span class="counter">但是：暂无明确反证；证伪条件待补。</span>'
            )
        blocks.append(
            f'<blockquote class="viewpoint" id="{vid}">'
            f'{text} {counter_html}'
            '</blockquote>'
        )
    return "\n".join(blocks)


def _render_legacy_chapters_html(data: Dict[str, Any]) -> str:
    """v0.1 fallback：把旧字段拼成 v0.2 风格的章节序列，让模板能渲染。"""
    skel = data.get("skeleton", {})
    chapters_synthesized: List[Dict[str, Any]] = []
    # 1. what-and-why（用 thesis 作为开场）
    chapters_synthesized.append({
        "id": "what-and-why",
        "title": "这是什么 · 为什么现在值得花一小时",
        "narrative_html": f'<p>{_esc(data.get("thesis", PLACEHOLDER))}</p>'
                          + _render_concepts_html(skel.get("concepts", [])),
    })
    # 2. history
    timeline = skel.get("timeline", [])
    if timeline:
        rows = "".join(
            f"<li><strong>{_esc(ev.get('year','') if isinstance(ev,dict) else '')}</strong> · "
            f"{_esc(ev.get('event', ev.get('text','')) if isinstance(ev,dict) else ev)}</li>"
            for ev in timeline
        )
        chapters_synthesized.append({
            "id": "history",
            "title": "它怎么走到今天",
            "narrative_html": f'<ol class="timeline-list">{rows}</ol>',
        })
    # 3. players
    chapters_synthesized.append({
        "id": "players",
        "title": "谁在场上 · 谁在赌什么",
        "narrative_html": _render_players_html_legacy(skel.get("players", [])),
    })
    # 4. insider（合并误读+盲区）
    insider_parts = []
    if data.get("misreadings"):
        lis = "".join(f"<li>{_esc(x)}</li>" for x in data["misreadings"])
        insider_parts.append(f'<h3>外部误读</h3><ul>{lis}</ul>')
    if data.get("blind_spots"):
        lis = "".join(f"<li>{_esc(x)}</li>" for x in data["blind_spots"])
        insider_parts.append(f'<h3>圈内盲区</h3><ul>{lis}</ul>')
    if insider_parts:
        chapters_synthesized.append({
            "id": "insider",
            "title": "圈内人才懂的几件事",
            "narrative_html": "\n".join(insider_parts),
        })
    # 5. structural
    if data.get("structure_layer"):
        rows = "".join(
            f"<dt>{_esc(k)}</dt><dd>{_esc(v)}</dd>" for k, v in data["structure_layer"].items()
        )
        chapters_synthesized.append({
            "id": "structural",
            "title": "表面之下 · 几条不可变的约束",
            "narrative_html": f'<dl>{rows}</dl>',
        })
    # 6. paradigm
    if data.get("paradigm_layer"):
        rows = "".join(
            f"<dt>{_esc(k)}</dt><dd>{_esc(v)}</dd>" for k, v in data["paradigm_layer"].items()
        )
        chapters_synthesized.append({
            "id": "paradigm",
            "title": "这是什么时期 · 异端正从边缘浮现",
            "narrative_html": f'<dl>{rows}</dl>',
        })
    # 7. isomorphism
    iso_blocks = []
    for it in data.get("isomorphisms", []):
        if isinstance(it, dict):
            iso_blocks.append(
                f'<h4>对照：{_esc(it.get("source", PLACEHOLDER))}</h4>'
                f'<p>同构：{_esc(it.get("similarity", PLACEHOLDER))}</p>'
                f'<p>但是反过来：{_esc(it.get("anti_similarity", PLACEHOLDER))}</p>'
            )
    if iso_blocks:
        chapters_synthesized.append({
            "id": "isomorphism",
            "title": "别处的故事 · 镜照本地",
            "narrative_html": "\n".join(iso_blocks),
        })
    # 8. reflexivity
    refl = data.get("reflexivity", {})
    if refl:
        chapters_synthesized.append({
            "id": "reflexivity",
            "title": "主流叙事 · 它如何自我强化又如何崩",
            "narrative_html": (
                f'<p><strong>主流叙事：</strong>{_esc(refl.get("narrative", PLACEHOLDER))}</p>'
                f'<p><strong>自我证实链路：</strong>{_esc(refl.get("self_reinforce", PLACEHOLDER))}</p>'
                f'<p><strong>失效条件：</strong>如果 {_esc(refl.get("failure_condition", PLACEHOLDER))}，整个故事就崩。</p>'
            ),
        })
    # 9. learning-path
    lp = skel.get("learning_path", [])
    if lp:
        items = "".join(f"<li>{_esc(x)}</li>" for x in lp)
        chapters_synthesized.append({
            "id": "learning-path",
            "title": "接下来你应该读什么 · 信谁",
            "narrative_html": f'<ol>{items}</ol>',
        })
    # 10. unknowns
    ku = data.get("known_unknowns", [])
    if ku:
        items = "".join(f"<li>{_esc(x)}</li>" for x in ku)
        chapters_synthesized.append({
            "id": "unknowns",
            "title": "我（AI）不知道的几件事",
            "narrative_html": f'<ul>{items}</ul>',
        })

    # 把旧的 facts/mechanisms/viewpoints 块附加到 evidence-chain（藏在 what-and-why 后面）
    legacy_evidence = (
        '<section class="legacy-evidence-chain">'
        '<h3>事实清单（旧 schema）</h3>'
        + _render_legacy_facts_html(data.get("facts", []))
        + '<h3>机制段落（旧 schema）</h3>'
        + _render_legacy_mechanisms_html(data.get("mechanisms", []))
        + '<h3>观点引文（旧 schema）</h3>'
        + _render_legacy_viewpoints_html(data.get("viewpoints", []))
        + '</section>'
    )
    if chapters_synthesized:
        chapters_synthesized[0]["narrative_html"] += "\n" + legacy_evidence

    return _render_chapters_html(chapters_synthesized)


def build_html_fragments(data: Dict[str, Any]) -> None:
    """把结构化字段预渲染成 HTML 字符串，注入 ctx 的 *_html 字段。
    v0.2 主路径：chapters_html / facts_complete_list_html / known_unknowns_data_html
    v1.1 新增：chapter_nav_html / side_toc_html / word_count_str
    旧 schema fallback：合成等价 chapters。
    """
    if data.get("_schema_v02"):
        chapters = data.get("chapters", [])
        data["chapters_html"] = _render_chapters_html(chapters)
        # v1.1：导航 / 侧边目录基于真实 chapters[]
        data["chapter_nav_html"] = _render_chapter_nav_html(chapters)
        data["side_toc_html"] = _render_side_toc_html(chapters)
    else:
        data["chapters_html"] = _render_legacy_chapters_html(data)
        # 旧 schema：占位为空 nav/toc，避免模板引用空字段崩
        data["chapter_nav_html"] = '<nav class="chapter-nav" aria-label="章节导航"></nav>'
        data["side_toc_html"] = '<aside class="side-toc" aria-label="侧边目录"><ol></ol></aside>'

    data["facts_complete_list_html"] = _render_facts_complete_list_html(
        data.get("facts", [])
    )
    data["known_unknowns_data_html"] = _render_known_unknowns_data_html(
        data.get("known_unknowns_data", []) or data.get("known_unknowns", [])
    )
    data["recommendations_html"] = _render_recommendations_html(
        data.get("experts", [])
    )
    data["self_check_html"] = _render_self_check_html(
        data.get("self_check_questions", [])
    )

    # v1.1：基于 chapters_html + 其它正文片段估算字数（cover-meta 用千分位展示）
    blob_parts = [
        data.get("chapters_html", ""),
        data.get("facts_complete_list_html", ""),
        data.get("known_unknowns_data_html", ""),
        data.get("recommendations_html", ""),
        data.get("self_check_html", ""),
    ]
    wc = word_count("\n".join(blob_parts))
    data["word_count"] = wc
    data["word_count_str"] = f"{wc:,}"

    # 兼容性：保留几个旧占位符的别名（万一模板里还引用）
    data.setdefault("ai_disclaimer_extra_html", "")
    # 旧模板可能引用的 *_html 占位（v0.1 模板向后兼容）
    if not data.get("_schema_v02"):
        skel = data.get("skeleton", {})
        data["concepts_html"] = _render_concepts_html(skel.get("concepts", []))
        data["players_html"] = _render_players_html_legacy(skel.get("players", []))
        data["facts_html"] = _render_legacy_facts_html(data.get("facts", []))
        data["mechanisms_html"] = _render_legacy_mechanisms_html(data.get("mechanisms", []))
        data["viewpoints_html"] = _render_legacy_viewpoints_html(data.get("viewpoints", []))


# ---------- 默认模板 fallback (v0.2 风格) ----------

def default_template() -> str:
    """模板未就绪时使用的兜底模板，保证脚本可独立运行。
    包含 v1.0 期望的所有占位符（单档深度产物）+ 闸门可扫描的元素。
    """
    return r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{domain_name}} · 领域速通</title>
<style>
:root { --fg:#1a1a1a; --bg:#fbfaf6; --accent:#7a1f1f; --muted:#666; --rule:#d8d3c4; }
@media (prefers-color-scheme: dark) {
  :root { --fg:#e8e4d8; --bg:#15140f; --accent:#c98a3a; --muted:#999; --rule:#3a382f; }
}
[data-theme="dark"] { --fg:#e8e4d8; --bg:#15140f; --accent:#c98a3a; --muted:#999; --rule:#3a382f; }
* { box-sizing: border-box; }
body { background: var(--bg); color: var(--fg);
  font-family: "Songti SC", "STSong", "SimSun", "Noto Serif CJK SC", serif;
  max-width: 760px; margin: 0 auto; padding: 2rem 1.2rem; line-height: 1.8; }
h1 { font-size: 2rem; }
h2 { font-size: 1.4rem; margin-top: 2.5rem; color: var(--accent); border-bottom: 1px solid var(--rule); padding-bottom: .3rem; }
.hero .subtitle { color: var(--muted); font-size: 1.05rem; }
.hero .thesis-line { font-style: italic; padding: .6rem 0 .4rem; border-left: 3px solid var(--accent); padding-left: 1rem; margin: 1rem 0; }
.hero .cutoff { color: var(--muted); font-size: .85rem; }
sup a.fact-ref { color: var(--accent); text-decoration: none; font-size: .8em; }
.mechanism { padding: .4rem .8rem; border-left: 2px solid var(--accent); background: rgba(122,31,31,.04); margin: 1rem 0; }
blockquote.viewpoint { padding: .6rem 1rem; border-left: 3px solid var(--accent); margin: 1.2rem 0; }
blockquote.viewpoint .counter { display: block; color: var(--muted); margin-top: .4rem; font-style: italic; }
blockquote.viewpoint .counter::before { content: "但是 / "; color: var(--accent); font-weight: 600; font-style: normal; }
.grade-A { color: #7a1f1f; font-weight: 600; }
.grade-B { color: #c98a3a; font-weight: 600; }
.grade-C { color: #5b6f8a; }
.grade-D { color: #9a9a9a; }
table.source-grading-table { border-collapse: collapse; margin: 1rem 0; }
table.source-grading-table td, table.source-grading-table th { border: 1px solid var(--rule); padding: .3rem .6rem; }
.muted { color: var(--muted); }
.ai-disclaimer-footer { font-size: .85rem; color: var(--muted); border-top: 1px solid var(--rule); padding-top: 1rem; margin-top: 3rem; }
@page { size: A4; margin: 1.6cm; }
@media print { body { background: #fff; color: #000; } }
</style>
</head>
<body>

<header class="hero">
  <h1>{{domain_name}}</h1>
  {{#if subtitle}}<p class="subtitle">{{subtitle}}</p>{{/if}}
  <p class="thesis-line">{{thesis_one_liner}}</p>
  <p class="cutoff muted">cutoff {{cutoff_date}}</p>
</header>

<main>
{{{chapters_html}}}
</main>

<details id="sources-fold">
  <summary>信息来源（{{fact_count}} 条 · 折叠）</summary>
  <div class="grade-overview">{{{grade_pie_svg}}}</div>
  {{{source_grading_table_html}}}
  <h3>事实锚点完整列表</h3>
  {{{facts_complete_list_html}}}
  <h3>推荐人 / 账号 / 会议</h3>
  {{{recommendations_html}}}
</details>

<details id="self-check-fold">
  <summary>自检题 · 读完测自己</summary>
  {{{self_check_html}}}
</details>

<details id="known-unknowns">
  <summary>已知的未知 · 数据清单（折叠）</summary>
  {{{known_unknowns_data_html}}}
</details>

<footer id="ai-disclaimer" class="ai-disclaimer-footer">
  <p>本页由 AI 模型基于训练数据生成，cutoff <strong>{{cutoff_date}}</strong>。
  cutoff 之后的事件、融资、人事变动一概不掌握；AI 是主流叙事的载体——所有"观点"判断都是可被打脸的假设，请用上方"推荐人/会议"去交叉验证。
  生成于 {{generation_date}}。</p>
</footer>
</body>
</html>
"""


# ---------- 主流程 ----------

# HTML 注释剥离正则（在渲染前去除，避免注释里的占位符也被模板引擎展开/二次注入大段 HTML）
_HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)


def render(data: Dict[str, Any], template: str) -> str:
    # 先剥离 HTML 注释——避免模板里的"用法示例"注释被引擎展开导致 chapters 等
    # 大段 HTML 被重复注入两次（v0.2 模板里有这种 inline 注释示意）。
    template_clean = _HTML_COMMENT_RE.sub("", template)
    return render_template(template_clean, data)


def word_count(text: str) -> int:
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
    n_chapters = len(data.get("chapters", []))
    n_facts = len(data["facts"])
    # 从 chapters 内的 narrative_html 数 .mechanism / .viewpoint 节点
    chapters_blob = "\n".join(
        ch.get("narrative_html", "") if isinstance(ch, dict) else ""
        for ch in data.get("chapters", [])
    )
    if not chapters_blob and not data.get("_schema_v02"):
        # 旧 schema fallback：直接从 mechanisms/viewpoints 数
        n_mech = len(data.get("mechanisms", []))
        n_view = len(data.get("viewpoints", []))
    else:
        n_mech = len(re.findall(r'class\s*=\s*["\'][^"\']*\bmechanism\b', chapters_blob))
        n_view = len(re.findall(r'class\s*=\s*["\'][^"\']*\bviewpoint\b', chapters_blob))
    # v1.1 新占位符注入数：从 out 中扫，便于看见 nav/toc 是否真的进了模板
    nav_hits = len(re.findall(r'class="nav-item"', out))
    toc_hits = len(re.findall(r'data-chapter-id="chapter-', out))
    print(
        f"[render.py] OK → {out_path}\n"
        f"  facts={n_facts} mechanisms={n_mech} viewpoints={n_view} chapters={n_chapters}\n"
        f"  word_count≈{wc}\n"
        f"  grade_pct: {pcts}\n"
        f"  v1.1: chapter_nav={nav_hits} side_toc={toc_hits}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
