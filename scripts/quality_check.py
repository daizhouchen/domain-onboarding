#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
quality_check.py — 内容闸门（domain-onboarding skill）

扫描 render.py 产出的单文件 HTML，跑内容侧硬约束。任一项失败即退出码 1，
打印每条 violation（中文 + 具体定位）。

检查项（参照 SKILL.md "强制必出元素清单" + "事实密度量化指标"）
1. 事实密度：fact-N 锚点数 ≥ 档位下限（闪研 15 / 精研 35 / 深研 70）
2. A+B 级源占比：闪研 ≥40% / 精研 ≥50% / 深研 ≥60%（解析 .source-grading-table）
3. 三层链完整性：每个 .mechanism 至少 cite 3 个 fact 锚点；
   每个 .viewpoint 必须含反例话语（counter_evidence 文本或 .counter 子节点）
4. 学究腔黑名单扫描（FORBIDDEN_TERMS 在正文 hit 任一即报错；附录区段豁免）
5. AI 自反性 disclaimer 必出：id="ai-disclaimer" + cutoff date + ≥3 个 expert 推荐
6. 已知的未知清单：≥5/8/12 条（按档位）
7. 单边叙事检测：每个 viewpoint section 出现至少一个反对话语标志
8. 来源分级表必出：.source-grading-table 存在
9. H1/H2/H3 不暴露分析框架（v0.2 新增）：标题文字不含"事实层/机制层/观点层/
   反身性/结构层/范式层/三层证据链/骨架·一/二/三/四/五"等框架名，应改用
   问题驱动的叙事化标题

CLI: python quality_check.py output.html
退出码: 0 通过 / 1 有 violations / 2 输入错误
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple


# ---------- 常量 ----------

TIER_FACT_MIN = {"flash": 15, "medium": 35, "deep": 70}
TIER_AB_MIN_PCT = {"flash": 40, "medium": 50, "deep": 60}
TIER_KU_MIN = {"flash": 5, "medium": 8, "deep": 12}

FORBIDDEN_TERMS: List[str] = [
    "波特五力分析告诉我们",
    "波特五力告诉",
    "根据波特五力",
    "波特五力分析显示",
    "Christensen 认为",
    "按照 Christensen",
    "克里斯坦森认为",
    "Hamilton Helmer 的 7 Powers",
    "应用 Wardley Map",
    "用 Wardley Map 分析",
    "根据 Braudel",
    "按照 Braudel 的",
    "Braudel 的三层时间",
    "基于 Perez 的技术革命周期",
    "Perez 周期理论",
    "从博弈论角度",
    "博弈论告诉我们",
    "用 Munger 的多元思维",
    "Munger 的多元思维模型告诉我们",
    "Soros 的反身性理论",
    "应用 Taleb 的反脆弱",
    "Taleb 的反脆弱理论",
    "Kahneman 的双系统",
    "Mauboussin 的二阶思维",
    "综上所述",
    "总而言之",
    "总的来说",
    "由此可见",
    "在数字时代浪潮下",
    "在 AI 时代",
    "在AI时代",
    "随着技术的飞速发展",
    "随着科技的飞速发展",
    "毋庸置疑",
    "无疑是",
    "众所周知",
    "我们必须认识到",
    "首先其次再次",
    "在新时代背景下",
    "蓬勃发展",
    "如火如荼",
    "方兴未艾",
]

# 反对话语标志（出现 ≥1 个即视为非单边叙事）
COUNTER_MARKERS: List[str] = [
    "反例",
    "证伪",
    "但是",
    "然而",
    "反过来",
    "如果",
    "另一方面",
    "反观",
    "悖论",
    "失效",
    "counter",
    "however",
    "前提是",
    "除非",
    "假如不",
]

# H1/H2/H3 不允许出现的分析框架名（v0.2 新增 · 标题暴露扫描）
HEADING_FORBIDDEN_TERMS: List[str] = [
    "事实层",
    "机制层",
    "观点层",
    "反身性",
    "结构层",
    "范式层",
    "跨领域同构",
    "三层证据链",
    "骨架·一",
    "骨架·二",
    "骨架·三",
    "骨架·四",
    "骨架·五",
    "骨架 · 一",
    "骨架 · 二",
    "骨架 · 三",
    "骨架 · 四",
    "骨架 · 五",
]


# 工具索引附录区段（FORBIDDEN_TERMS 在这里出现豁免）
TOOL_INDEX_MARKERS = [
    "id=\"tool-index\"",
    "id='tool-index'",
    "class=\"tool-index\"",
    "class='tool-index'",
    "id=\"appendix\"",
    "id='appendix'",
    "class=\"appendix\"",
    "class='appendix'",
]


# ---------- HTML 简单解析 ----------

_TAG_RE = re.compile(r"<[^>]+>", re.DOTALL)
_SCRIPT_STYLE_RE = re.compile(
    r"<(script|style)\b[^>]*>.*?</\1>", re.DOTALL | re.IGNORECASE
)


def strip_tags(html_text: str) -> str:
    s = _SCRIPT_STYLE_RE.sub(" ", html_text)
    s = _TAG_RE.sub(" ", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def find_blocks_by_class(html_text: str, cls: str) -> List[Tuple[int, str]]:
    """返回 [(起始位置, 块 HTML 文本), ...]，简易实现：从开标签到下一个同名同类闭合
    或 section 边界。够用即可——质检对宽容度有要求。"""
    blocks: List[Tuple[int, str]] = []
    # v0.2 起 .viewpoint 改用 <blockquote>，.mechanism 用 <p>，所以扩展标签集合
    pat = re.compile(
        r'<(div|section|article|p|li|blockquote)[^>]*class\s*=\s*["\'][^"\']*\b'
        + re.escape(cls)
        + r'\b[^"\']*["\'][^>]*>',
        re.IGNORECASE,
    )
    for m in pat.finditer(html_text):
        tag = m.group(1).lower()
        start = m.end()
        # 找匹配的闭合标签（容忍嵌套同名标签）
        depth = 1
        i = start
        open_pat = re.compile(rf"<{tag}\b", re.IGNORECASE)
        close_pat = re.compile(rf"</{tag}\s*>", re.IGNORECASE)
        end = len(html_text)
        while i < len(html_text):
            o = open_pat.search(html_text, i)
            c = close_pat.search(html_text, i)
            if not c:
                break
            if o and o.start() < c.start():
                depth += 1
                i = o.end()
            else:
                depth -= 1
                if depth == 0:
                    end = c.start()
                    break
                i = c.end()
        blocks.append((m.start(), html_text[m.start() : end]))
    return blocks


def line_of(html_text: str, pos: int) -> int:
    return html_text.count("\n", 0, pos) + 1


# ---------- 各项检查 ----------

class Report:
    def __init__(self) -> None:
        self.violations: List[str] = []
        self.notes: List[str] = []

    def fail(self, code: str, msg: str) -> None:
        self.violations.append(f"[{code}] {msg}")

    def note(self, msg: str) -> None:
        self.notes.append(msg)


def detect_tier(html_text: str) -> str:
    # 优先：body 上的 data-tier 属性（v0.2 模板）
    m = re.search(
        r'<body\b[^>]*\bdata-tier\s*=\s*["\'](flash|medium|deep)["\']',
        html_text,
        re.IGNORECASE | re.DOTALL,
    )
    if m:
        return m.group(1).lower()
    # 次优：任何 data-tier= 属性（取首个）
    m = re.search(
        r'\bdata-tier\s*=\s*["\'](flash|medium|deep)["\']',
        html_text,
        re.IGNORECASE,
    )
    if m:
        return m.group(1).lower()
    # 通用：tier=xxx 写法
    m = re.search(
        r'\btier\s*[:=]\s*["\']?(flash|medium|deep)\b', html_text, re.IGNORECASE
    )
    if m:
        return m.group(1).lower()
    # body class show-deep / show-medium 作为 fallback
    if "show-deep" in html_text:
        return "deep"
    if "show-medium" in html_text:
        return "medium"
    # 启发式：fact 锚点数倒推
    n = len(re.findall(r'id\s*=\s*["\']fact-\d+["\']', html_text))
    if n >= 70:
        return "deep"
    if n >= 35:
        return "medium"
    return "flash"


def check_fact_density(html_text: str, tier: str, rep: Report) -> int:
    n = len(re.findall(r'id\s*=\s*["\']fact-\d+["\']', html_text))
    minimum = TIER_FACT_MIN[tier]
    if n < minimum:
        rep.fail(
            "事实密度",
            f"fact 锚点数 {n} < 档位 {tier} 下限 {minimum}（需要在 HTML 中加 id=\"fact-N\"）",
        )
    return n


def parse_grade_table(html_text: str) -> Optional[Dict[str, int]]:
    m = re.search(
        r'<table[^>]*class\s*=\s*["\'][^"\']*\bsource-grading-table\b[^"\']*["\'][^>]*>(.*?)</table>',
        html_text,
        re.DOTALL | re.IGNORECASE,
    )
    if not m:
        return None
    body = m.group(1)
    counts: Dict[str, int] = {}
    # 行：<tr><td...>A</td><td>n</td>...</tr>
    for row in re.finditer(r"<tr\b[^>]*>(.*?)</tr>", body, re.DOTALL | re.IGNORECASE):
        cells = re.findall(r"<t[dh]\b[^>]*>(.*?)</t[dh]>", row.group(1), re.DOTALL | re.IGNORECASE)
        if len(cells) < 2:
            continue
        grade_txt = strip_tags(cells[0]).strip().upper()
        if grade_txt in ("A", "B", "C", "D"):
            digits = re.search(r"\d+", strip_tags(cells[1]))
            if digits:
                counts[grade_txt] = int(digits.group(0))
    return counts or None


def check_grade_table(html_text: str, tier: str, rep: Report) -> None:
    if "source-grading-table" not in html_text:
        rep.fail("来源分级表", "未找到 .source-grading-table 节点")
        return
    counts = parse_grade_table(html_text)
    if not counts:
        rep.fail(
            "来源分级表",
            "找到 .source-grading-table 但无法解析 A/B/C/D 行（确认每行首列是单字母 A/B/C/D，次列是数字）",
        )
        return
    total = sum(counts.values())
    if total == 0:
        rep.fail("来源分级表", "A/B/C/D 计数全为 0")
        return
    ab = counts.get("A", 0) + counts.get("B", 0)
    pct = ab * 100 / total
    floor = TIER_AB_MIN_PCT[tier]
    if pct < floor:
        rep.fail(
            "A+B 占比",
            f"A+B 级源占比 {pct:.1f}% < 档位 {tier} 下限 {floor}%（A={counts.get('A',0)}, B={counts.get('B',0)}, 总={total}）",
        )


def check_three_layer_chain(html_text: str, rep: Report) -> None:
    # 机制：每个 .mechanism 至少 cite 3 个 fact 锚点
    mech_blocks = find_blocks_by_class(html_text, "mechanism")
    if not mech_blocks:
        rep.fail("机制层", "未找到任何 .mechanism 节点（缺三层链中段）")
    for pos, block in mech_blocks:
        refs = set(re.findall(r"#fact-(\d+)", block))
        # 兼容显式数据属性 data-fact-refs="f1,f3"
        attr = re.search(
            r'data-fact-refs\s*=\s*["\']([^"\']+)["\']', block, re.IGNORECASE
        )
        if attr:
            for r in re.findall(r"\d+", attr.group(1)):
                refs.add(r)
        if len(refs) < 3:
            rep.fail(
                "机制-事实链",
                f"line {line_of(html_text, pos)}: .mechanism 节点引用事实 {len(refs)} 条 < 3（需要 ≥3 个 #fact-N 链接或 data-fact-refs）",
            )

    # 观点：必须含反例话语
    vp_blocks = find_blocks_by_class(html_text, "viewpoint")
    if not vp_blocks:
        rep.fail("观点层", "未找到任何 .viewpoint 节点")
    for pos, block in vp_blocks:
        text = strip_tags(block)
        has_counter_node = bool(
            re.search(r'class\s*=\s*["\'][^"\']*\bcounter\b', block, re.IGNORECASE)
        )
        has_marker = any(mk in text for mk in COUNTER_MARKERS)
        if not (has_counter_node or has_marker):
            rep.fail(
                "观点反例缺失",
                f"line {line_of(html_text, pos)}: .viewpoint 节点既无 .counter 子节点也无反对话语（{', '.join(COUNTER_MARKERS[:6])} 等）",
            )


def remove_appendix(html_text: str) -> str:
    """从 HTML 中剔除工具索引/附录区段（FORBIDDEN_TERMS 豁免区）。"""
    out = html_text
    for marker in TOOL_INDEX_MARKERS:
        # 找到 marker 起始的标签，按 div/section 配对粗暴剔除
        for m in list(re.finditer(re.escape(marker), out)):
            # 向前找到所属开标签起点
            start_tag = out.rfind("<", 0, m.start())
            if start_tag < 0:
                continue
            tag_match = re.match(r"<(div|section|article)\b", out[start_tag:])
            if not tag_match:
                continue
            tag = tag_match.group(1)
            close = re.search(rf"</{tag}\s*>", out[m.end():], re.IGNORECASE)
            if not close:
                continue
            end = m.end() + close.end()
            out = out[:start_tag] + " " + out[end:]
    return out


def check_forbidden_terms(html_text: str, rep: Report) -> None:
    cleaned = remove_appendix(html_text)
    plain = strip_tags(cleaned)
    for term in FORBIDDEN_TERMS:
        if term in plain:
            # 在原始 html 中定位行号（取首次出现）
            idx = html_text.find(term)
            ln = line_of(html_text, idx) if idx >= 0 else -1
            rep.fail(
                "学究腔黑名单",
                f'line {ln}: 出现禁用词 "{term}"（用具体洞见替代框架名）',
            )


def check_ai_disclaimer(html_text: str, rep: Report) -> None:
    if not re.search(r'id\s*=\s*["\']ai-disclaimer["\']', html_text):
        rep.fail("AI disclaimer", "未找到 id=\"ai-disclaimer\" 的 section")
        return
    m = re.search(
        r'id\s*=\s*["\']ai-disclaimer["\'].*?</section>',
        html_text,
        re.DOTALL | re.IGNORECASE,
    )
    if not m:
        m = re.search(
            r'id\s*=\s*["\']ai-disclaimer["\'].*?</div>',
            html_text,
            re.DOTALL | re.IGNORECASE,
        )
    block = m.group(0) if m else ""
    plain = strip_tags(block)
    if not re.search(r"\b(20\d{2})\b", plain) and "cutoff" not in plain.lower() and "截止" not in plain:
        rep.fail(
            "AI disclaimer",
            "ai-disclaimer 内未发现 cutoff date（年份或 'cutoff' / '截止'）",
        )


def check_experts(html_text: str, rep: Report) -> None:
    """启发式：找 .recommendations-list 或"推荐人"区段下的 li 数。"""
    # 优先：直接找 .recommendations-list
    m = re.search(
        r'<ul[^>]*class\s*=\s*["\'][^"\']*\brecommendations-list\b[^"\']*["\'][^>]*>(.*?)</ul>',
        html_text,
        re.DOTALL | re.IGNORECASE,
    )
    if m:
        seg = m.group(1)
        li = re.findall(r"<li\b[^>]*>(.*?)</li>", seg, re.DOTALL | re.IGNORECASE)
        n = sum(1 for x in li if strip_tags(x).strip())
        if n < 3:
            rep.fail(
                "专家推荐",
                f"推荐人/账号/社区条目 {n} 条 < 3（在 HTML 加 ≥3 个 <li> 给真人/账号让用户去人肉验证）",
            )
        return

    # 次选：剔除 style/script 后用关键词正则定位
    cleaned = _SCRIPT_STYLE_RE.sub(" ", html_text)
    m = re.search(
        r"(推荐人|推荐账号|推荐.{0,4}社区|experts?)[\s\S]{0,3000}",
        cleaned,
        re.IGNORECASE,
    )
    seg = m.group(0) if m else ""
    li = re.findall(r"<li\b[^>]*>(.*?)</li>", seg, re.DOTALL | re.IGNORECASE)
    n = sum(1 for x in li if strip_tags(x).strip())
    if n < 3:
        rep.fail(
            "专家推荐",
            f"推荐人/账号/社区条目 {n} 条 < 3（在 HTML 加 ≥3 个 <li> 给真人/账号让用户去人肉验证）",
        )


def check_no_framework_in_headings(html_text: str, rep: Report) -> None:
    """v0.2 新增：扫描所有 H1/H2/H3 标题文本，禁止出现分析框架名。
    呈现是叙事，不是把"事实层/机制层/观点层/反身性"等分析框架名直接糊到标题上。
    """
    pattern = re.compile(r"<(h[123])\b[^>]*>(.*?)</\1>", re.DOTALL | re.IGNORECASE)
    for m in pattern.finditer(html_text):
        tag = m.group(1).lower()
        inner = m.group(2)
        text = strip_tags(inner).strip()
        if not text:
            continue
        for term in HEADING_FORBIDDEN_TERMS:
            if term in text:
                ln = line_of(html_text, m.start())
                rep.fail(
                    "H2 暴露",
                    f'line {ln}: 标题"{text}"包含分析框架名"{term}"——'
                    f'应改为问题驱动的叙事化标题',
                )
                break  # 同一标题只报一次


def check_known_unknowns(html_text: str, tier: str, rep: Report) -> None:
    floor = TIER_KU_MIN[tier]
    # 优先：找 id="known-unknowns" 节点（v0.2 旁路数据 ul）
    m = re.search(
        r'id\s*=\s*["\']known-unknowns["\']',
        html_text,
        re.IGNORECASE,
    )
    if m:
        # 从该 id 起向后取 4000 字符并截到下一个 </details> / </section> / 下一个 h2
        seg = html_text[m.end() : m.end() + 5000]
        end = re.search(r"</details\s*>|</section\s*>|<h2\b", seg, re.IGNORECASE)
        if end:
            seg = seg[: end.start()]
        li = re.findall(r"<li\b[^>]*>(.*?)</li>", seg, re.DOTALL | re.IGNORECASE)
        n = sum(1 for x in li if strip_tags(x).strip())
        if n < floor:
            rep.fail(
                "已知的未知",
                f"已知的未知条目 {n} < 档位 {tier} 下限 {floor}（id=known-unknowns 区段下 li 数）",
            )
        return

    # 次选：用关键词定位（剔除 style/script 后）
    cleaned = _SCRIPT_STYLE_RE.sub(" ", html_text)
    m = re.search(
        r"(已知的未知|known\s*unknowns)[\s\S]{0,4000}",
        cleaned,
        re.IGNORECASE,
    )
    if not m:
        rep.fail(
            "已知的未知",
            f'未找到"已知的未知 / known unknowns"区段（应有 ≥{floor} 条 li）',
        )
        return
    seg = m.group(0)
    end = re.search(r"<h2\b|</section\s*>|</details\s*>", seg[20:], re.IGNORECASE)
    if end:
        seg = seg[: 20 + end.start()]
    li = re.findall(r"<li\b[^>]*>(.*?)</li>", seg, re.DOTALL | re.IGNORECASE)
    n = sum(1 for x in li if strip_tags(x).strip())
    if n < floor:
        rep.fail(
            "已知的未知",
            f"已知的未知条目 {n} < 档位 {tier} 下限 {floor}",
        )


# ---------- 主入口 ----------

def run_checks(html_text: str) -> Report:
    rep = Report()
    tier = detect_tier(html_text)
    rep.note(f"detected tier = {tier}")

    check_fact_density(html_text, tier, rep)
    check_grade_table(html_text, tier, rep)
    check_three_layer_chain(html_text, rep)
    check_forbidden_terms(html_text, rep)
    check_no_framework_in_headings(html_text, rep)
    check_ai_disclaimer(html_text, rep)
    check_experts(html_text, rep)
    check_known_unknowns(html_text, tier, rep)
    return rep


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="domain-onboarding 内容闸门")
    ap.add_argument("html", help="渲染后的 HTML 文件路径")
    args = ap.parse_args(argv)

    p = Path(args.html)
    if not p.exists():
        print(f"[quality_check.py error] 找不到文件：{p}", file=sys.stderr)
        return 2
    text = p.read_text(encoding="utf-8")

    rep = run_checks(text)
    for n in rep.notes:
        print(f"[note] {n}")
    if rep.violations:
        print(f"[FAIL] 内容闸门未通过：{len(rep.violations)} 条 violations")
        for v in rep.violations:
            print(f"  - {v}")
        return 1
    print("[OK] 内容闸门通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
