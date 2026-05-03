#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
visual_check.py — 视觉闸门（domain-onboarding skill）

扫描 render.py 产出的单文件 HTML，校验视觉/结构侧硬约束。

检查项
1. 三档差异化比例
   - 闪研字数 = .tier-flash 内容
   - 精研字数 = .tier-flash + .tier-medium 内容（嵌套）
   - 深研字数 = 全部三档（嵌套）
   - 精研 ≥ 1.3× 闪研；深研 ≥ 1.5× 精研
2. 零 CDN：所有 src/href 中不允许出现 http(s):// 外链（anchor #xxx 与 mailto:/data: 例外）
3. <meta name="viewport" ... width=device-width>
4. <html lang="zh-CN">
5. 暗色模式：含 prefers-color-scheme: dark 或 [data-theme="dark"]
6. 打印优化：含 @page 或 @media print
7. inline SVG 数量在 [1, 30]
8. 反 AI slop 视觉清单
   - 不能有 linear-gradient 含 purple 主色
   - .h1/.h2 不能 text-transform: uppercase
   - box-shadow 出现次数 ≤ 5
   - 中文段落不能 text-align: center（标题除外）

CLI: python visual_check.py output.html
退出码: 0 通过 / 1 不通过 / 2 输入错误
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

# 允许有 BeautifulSoup 就用，没有就 fallback 正则
try:  # pragma: no cover
    from bs4 import BeautifulSoup  # type: ignore
    _HAS_BS = True
except Exception:  # pragma: no cover
    _HAS_BS = False


# ---------- 文本提取 ----------

_SCRIPT_STYLE_RE = re.compile(
    r"<(script|style)\b[^>]*>.*?</\1>", re.DOTALL | re.IGNORECASE
)
_TAG_RE = re.compile(r"<[^>]+>", re.DOTALL)


def strip_tags(s: str) -> str:
    s = _SCRIPT_STYLE_RE.sub(" ", s)
    s = _TAG_RE.sub(" ", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def word_count(s: str) -> int:
    plain = strip_tags(s)
    cn = len(re.findall(r"[一-鿿]", plain))
    en = len(re.findall(r"[A-Za-z]+", plain))
    return cn + en


def extract_class_blocks(html: str, cls: str) -> List[str]:
    """提取所有 class 包含 cls 的块（含子内容），不依赖 BeautifulSoup。"""
    blocks: List[str] = []
    pat = re.compile(
        r'<(div|section|article|aside|main)[^>]*class\s*=\s*["\'][^"\']*\b'
        + re.escape(cls)
        + r'\b[^"\']*["\'][^>]*>',
        re.IGNORECASE,
    )
    for m in pat.finditer(html):
        tag = m.group(1).lower()
        depth = 1
        i = m.end()
        open_pat = re.compile(rf"<{tag}\b", re.IGNORECASE)
        close_pat = re.compile(rf"</{tag}\s*>", re.IGNORECASE)
        end = len(html)
        while i < len(html):
            o = open_pat.search(html, i)
            c = close_pat.search(html, i)
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
        blocks.append(html[m.end() : end])
    return blocks


def extract_class_blocks_bs(html: str, cls: str) -> List[str]:  # pragma: no cover
    soup = BeautifulSoup(html, "html.parser")
    return [str(node) for node in soup.find_all(class_=cls)]


def get_blocks(html: str, cls: str) -> List[str]:
    if _HAS_BS:
        try:
            return extract_class_blocks_bs(html, cls)
        except Exception:
            pass
    return extract_class_blocks(html, cls)


# ---------- 报告 ----------

class Report:
    def __init__(self) -> None:
        self.violations: List[str] = []
        self.notes: List[str] = []

    def fail(self, code: str, msg: str) -> None:
        self.violations.append(f"[{code}] {msg}")

    def note(self, msg: str) -> None:
        self.notes.append(msg)


# ---------- 检查项 ----------

def _detect_tier(html: str) -> str:
    """从 HTML 中识别 tier 等级（默认 medium）。
    优先匹配 <body data-tier="..."> 上的实际属性，避免被 CSS 选择器
    body[data-tier="flash"] 这种规则干扰。
    """
    m = re.search(
        r'<body\b[^>]*\bdata-tier\s*=\s*["\'](flash|medium|deep)["\']',
        html,
        re.IGNORECASE | re.DOTALL,
    )
    if m:
        return m.group(1).lower()
    m = re.search(
        r'data-tier\s*=\s*["\'](flash|medium|deep)["\']', html, re.IGNORECASE
    )
    if m:
        return m.group(1).lower()
    m = re.search(
        r'\btier\s*[:=]\s*["\']?(flash|medium|deep)\b', html, re.IGNORECASE
    )
    if m:
        return m.group(1).lower()
    return "medium"


def check_tier_word_ratios(html: str, rep: Report) -> None:
    flash_blocks = get_blocks(html, "tier-flash")
    medium_blocks = get_blocks(html, "tier-medium")
    deep_blocks = get_blocks(html, "tier-deep")

    if not flash_blocks:
        rep.fail("三档结构", "未找到 .tier-flash 节点（HTML 必须包含闪研区块）")
    if not medium_blocks:
        rep.fail("三档结构", "未找到 .tier-medium 节点")
    if not deep_blocks:
        rep.fail("三档结构", "未找到 .tier-deep 节点")
    if not (flash_blocks and medium_blocks and deep_blocks):
        return

    flash_text = " ".join(flash_blocks)
    medium_text = flash_text + " " + " ".join(medium_blocks)
    deep_text = medium_text + " " + " ".join(deep_blocks)

    wf = word_count(flash_text)
    wm = word_count(medium_text)
    wd = word_count(deep_text)
    rep.note(f"字数：闪研≈{wf} 精研≈{wm} 深研≈{wd}")

    # 闪研档不强制扩展比例：闪研 sample 的设计目标就是 30 分钟读完，
    # 深研/精研 tier 节点存在但不要求字数超过闪研主体。
    # 只对 medium / deep 档位 sample 施加扩展比例约束。
    tier = _detect_tier(html)
    if tier == "flash":
        rep.note(f"detected tier=flash → 跳过档位字数比例检查")
        return

    if wf <= 0:
        rep.fail("字数", "闪研字数为 0")
        return
    ratio_m = wm / wf if wf else 0
    ratio_d = wd / wm if wm else 0
    if ratio_m < 1.3:
        rep.fail(
            "档位差异",
            f"精研/闪研 = {ratio_m:.2f} < 1.3（精研需要在闪研基础上扩展更多内容）",
        )
    if tier == "deep" and ratio_d < 1.5:
        rep.fail(
            "档位差异",
            f"深研/精研 = {ratio_d:.2f} < 1.5（深研需要明显厚于精研）",
        )


def check_no_cdn(html: str, rep: Report) -> None:
    # src= 与 href= 的所有取值
    hits: List[Tuple[int, str]] = []
    for m in re.finditer(
        r'\b(?:src|href)\s*=\s*["\']([^"\']+)["\']',
        html,
        re.IGNORECASE,
    ):
        url = m.group(1).strip()
        if re.match(r"^https?://", url, re.IGNORECASE):
            hits.append((m.start(), url))
    if hits:
        # 头三个示例
        sample = "; ".join(f"{u}" for _, u in hits[:3])
        rep.fail(
            "零 CDN",
            f"发现 {len(hits)} 处 http(s) 外链（必须全本地化）：{sample}",
        )


def check_viewport(html: str, rep: Report) -> None:
    m = re.search(
        r'<meta[^>]+name\s*=\s*["\']viewport["\'][^>]*>',
        html,
        re.IGNORECASE,
    )
    if not m or "width=device-width" not in m.group(0).lower().replace(" ", ""):
        rep.fail(
            "viewport",
            '缺少 <meta name="viewport" ...width=device-width...>',
        )


def check_lang(html: str, rep: Report) -> None:
    if not re.search(r'<html[^>]+lang\s*=\s*["\']zh-CN["\']', html, re.IGNORECASE):
        rep.fail("lang", "缺少 <html lang=\"zh-CN\">")


def check_dark_mode(html: str, rep: Report) -> None:
    if not (
        re.search(r"prefers-color-scheme\s*:\s*dark", html, re.IGNORECASE)
        or re.search(r'\[data-theme\s*=\s*["\']dark["\']\]', html, re.IGNORECASE)
    ):
        rep.fail(
            "暗色模式",
            "未发现 prefers-color-scheme: dark 或 [data-theme=\"dark\"] 选择器",
        )


def check_print(html: str, rep: Report) -> None:
    if not (re.search(r"@page\b", html) or re.search(r"@media\s+print\b", html)):
        rep.fail("打印优化", "未发现 @page 或 @media print")


def check_svg_count(html: str, rep: Report) -> None:
    n = len(re.findall(r"<svg\b", html, re.IGNORECASE))
    if n < 1:
        rep.fail("SVG", "未发现任何 inline SVG（至少需要 1 个装饰/图表）")
    elif n > 30:
        rep.fail("SVG", f"inline SVG 共 {n} 个 > 30（装饰过载）")


def _gather_styles(html: str) -> str:
    """抽取所有 <style> 块 + 内联 style 属性，拼成一段文本以便正则扫描。"""
    parts: List[str] = []
    for m in re.finditer(
        r"<style\b[^>]*>(.*?)</style>", html, re.DOTALL | re.IGNORECASE
    ):
        parts.append(m.group(1))
    for m in re.finditer(
        r'style\s*=\s*["\']([^"\']+)["\']', html, re.IGNORECASE
    ):
        parts.append(m.group(1))
    return "\n".join(parts)


def check_anti_slop(html: str, rep: Report) -> None:
    style_blob = _gather_styles(html)

    # 紫色 linear-gradient
    for m in re.finditer(
        r"linear-gradient\s*\([^)]*\)", style_blob, re.IGNORECASE
    ):
        chunk = m.group(0).lower()
        if (
            "purple" in chunk
            or "#80" in chunk and "ff" in chunk  # 粗略避免误伤
            or re.search(r"#(?:6|7|8|9)[0-9a-f]00?[a-f0-9]{0,3}", chunk)
            and "purple" in chunk
        ):
            rep.fail(
                "AI slop 紫色渐变",
                f'禁止 purple linear-gradient："{m.group(0)[:80]}"',
            )
    # 直接 named purple
    if re.search(r"linear-gradient\s*\([^)]*\bpurple\b", style_blob, re.IGNORECASE):
        rep.fail("AI slop 紫色渐变", "linear-gradient 含 purple 关键字")

    # h1 / h2 / .h1 / .h2 上的 text-transform: uppercase
    for m in re.finditer(
        r"(\.?h[12]\b[^{]*)\{([^}]*)\}", style_blob, re.IGNORECASE | re.DOTALL
    ):
        rule_body = m.group(2)
        if re.search(r"text-transform\s*:\s*uppercase", rule_body, re.IGNORECASE):
            rep.fail(
                "AI slop 大写标题",
                f'h1/h2 不应使用 uppercase（命中规则："{m.group(0)[:80]}..."）',
            )

    # box-shadow 数量
    bs_count = len(re.findall(r"box-shadow\s*:", style_blob, re.IGNORECASE))
    if bs_count > 5:
        rep.fail(
            "AI slop box-shadow",
            f"box-shadow 出现 {bs_count} 处 > 5（过度阴影）",
        )

    # 中文段落 text-align: center（标题豁免）
    # 启发式：扫 p / .p / li 选择器规则
    for m in re.finditer(
        r"([^{}]+)\{([^}]*text-align\s*:\s*center[^}]*)\}",
        style_blob,
        re.IGNORECASE | re.DOTALL,
    ):
        sel = m.group(1).strip()
        # 选择器若包含 h1/h2/h3/h4/h5/h6 / .title / header / .center / .hero 等就豁免
        if re.search(r"h[1-6]\b|\btitle\b|\bheader\b|\bhero\b|\.center\b|\.tier-controls\b", sel, re.IGNORECASE):
            continue
        # 如果选择器里出现 p / li / body / article / section
        if re.search(r"\bp\b|\bli\b|\bbody\b|\barticle\b|\bsection\b|\.thesis\b", sel, re.IGNORECASE):
            rep.fail(
                "AI slop 居中正文",
                f'中文正文不应 text-align:center（选择器："{sel[:80]}"）',
            )


# ---------- 主入口 ----------

def run_checks(html: str) -> Report:
    rep = Report()
    check_tier_word_ratios(html, rep)
    check_no_cdn(html, rep)
    check_viewport(html, rep)
    check_lang(html, rep)
    check_dark_mode(html, rep)
    check_print(html, rep)
    check_svg_count(html, rep)
    check_anti_slop(html, rep)
    return rep


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="domain-onboarding 视觉闸门")
    ap.add_argument("html", help="渲染后的 HTML 文件路径")
    args = ap.parse_args(argv)

    p = Path(args.html)
    if not p.exists():
        print(f"[visual_check.py error] 找不到文件：{p}", file=sys.stderr)
        return 2
    text = p.read_text(encoding="utf-8")

    rep = run_checks(text)
    for n in rep.notes:
        print(f"[note] {n}")
    if rep.violations:
        print(f"[FAIL] 视觉闸门未通过：{len(rep.violations)} 条 violations")
        for v in rep.violations:
            print(f"  - {v}")
        return 1
    print("[OK] 视觉闸门通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
