#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
quality_check.py — 内容闸门（domain-onboarding skill）

扫描 render.py 产出的单文件 HTML，跑内容侧硬约束。任一项失败即退出码 1，
打印每条 violation（中文 + 具体定位）。

检查项（v2.0：单档深度产物 · 阈值统一到深研档要求 · 新增语言风格闸门）
1. 整篇英文密度（v2.0 新）：英文字符占比 > 30% 直接 fail，> 25% warn
2. 章节级英文密度（v2.0 新）：单章 > 35% 直接 fail（精确定位"中英混乱"章节）
3. 未注释英文术语扫描（v2.0 新）：扫首字母大写英文词 30 字符内是否有中文括号注释；
   ≥30 个未注释 fail，否则 warn（启发式，含 ENGLISH_TERM_WHITELIST 圈内通行词）
4. 事实密度：fact-N 锚点数 ≥ 70（未达标输出 warning，不 fail——X2 在并行加深内容）
5. A+B 级源占比：≥60%（解析 .source-grading-table）
6. 三层链完整性：每个 .mechanism 至少 cite 3 个 fact 锚点；
   每个 .viewpoint 必须含反例话语（counter_evidence 文本或 .counter 子节点）
7. 学究腔黑名单扫描（FORBIDDEN_TERMS 在正文 hit 任一即报错；附录区段豁免）
8. AI 自反性 disclaimer 必出：id="ai-disclaimer" + cutoff date + ≥3 个 expert 推荐
9. 已知的未知清单：≥12 条
10. 单边叙事检测：每个 viewpoint section 出现至少一个反对话语标志
11. 来源分级表必出：.source-grading-table 存在
12. H1/H2/H3 不暴露分析框架：标题文字不含"事实层/机制层/观点层/
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

# v1.0 单档深度产物 · 阈值统一到深研档要求
FACT_MIN = 70
AB_MIN_PCT = 60
KU_MIN = 12

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


# v2.0：英文专有名词白名单——圈内通行、不需要中文括号注释的术语。
# 启发式扫描在文中遇到这些词不算"未注释"。维护原则：
#   - 只放真正圈内通行的（媒体/教科书都直接用英文）
#   - 不放冷门人名 / 不放公司细分产品（OpenAI 在白名单，但 ChatGPT 之类本身就是英文专名也加）
#   - 缩写优先（API/SDK/GPU），全称如果中文圈也常用英文则加
ENGLISH_TERM_WHITELIST = {
    # 技术通用缩写
    "API", "SDK", "SaaS", "IaaS", "PaaS", "GPU", "CPU", "TPU", "NPU", "ASIC",
    "FPGA", "CDN", "DNS", "HTTP", "HTTPS", "TCP", "UDP", "IP", "URL", "URI",
    "JSON", "XML", "YAML", "CSV", "HTML", "CSS", "REST", "RPC", "gRPC",
    "OAuth", "JWT", "TLS", "SSL", "VPC", "DDoS",
    # AI/ML
    "AI", "ML", "DL", "NLP", "CV", "RL", "LLM", "VLM", "MLLM", "MoE",
    "SFT", "RLHF", "DPO", "PPO", "RAG", "CoT", "ICL",
    "SOTA", "MLOps", "AGI", "ASI",
    "Transformer", "BERT", "GPT", "ChatGPT", "Claude", "Gemini", "Llama",
    "Mistral", "DeepSeek", "Qwen",
    # 商业/金融
    "CEO", "CTO", "CFO", "COO", "CMO", "CIO", "VP", "PM", "PMF",
    "VC", "PE", "LP", "GP", "IPO", "M&A", "SPAC", "ARR", "MRR", "LTV", "CAC",
    "B2B", "B2C", "C2C", "DTC", "P2P", "OEM", "ODM", "OKR", "KPI", "ROI",
    "GDP", "CPI", "PPI", "PMI", "GAAP", "IFRS", "EBITDA", "EPS", "PE",
    "GMV", "DAU", "MAU", "WAU", "ARPU",
    # 国际机构
    "IMF", "BIS", "OECD", "WTO", "NATO", "EU", "UN", "G7", "G20", "ASEAN",
    "BRICS", "IEA", "OPEC", "FAO", "WHO", "UNESCO", "ICO", "ICC",
    # 平台/公司（圈内即文化通用）
    "GitHub", "GitLab", "Bitbucket", "Twitter", "X", "YouTube", "TikTok",
    "Reddit", "Discord", "Slack", "Telegram", "WhatsApp", "LinkedIn",
    "Facebook", "Instagram", "WeChat", "Weibo",
    "iOS", "macOS", "Linux", "Ubuntu", "Debian", "Windows", "Android",
    "Docker", "Kubernetes", "Terraform", "Ansible",
    "OpenAI", "Anthropic", "Google", "Alphabet", "Meta", "Microsoft",
    "Amazon", "Apple", "Tesla", "Nvidia", "Intel", "AMD", "ARM", "TSMC",
    "AWS", "GCP", "Azure", "Cloudflare", "Vercel", "Netlify", "Stripe",
    "ByteDance", "Tencent", "Alibaba", "Baidu", "Huawei", "Xiaomi",
    "Pinecone", "Weaviate", "Milvus", "Qdrant", "Vespa", "Chroma",
    "Elasticsearch", "ClickHouse", "Snowflake", "Databricks",
    "PostgreSQL", "Postgres", "MySQL", "MongoDB", "Redis", "Cassandra",
    "Kafka", "RabbitMQ", "Spark", "Flink", "Hadoop",
    "pgvector", "FAISS", "ScaNN", "Annoy", "HNSW",
    # 编程语言/框架
    "JavaScript", "TypeScript", "Python", "Rust", "Go", "Java", "Kotlin",
    "Swift", "Ruby", "Scala", "Clojure", "Haskell", "Erlang", "Elixir",
    "C", "C++", "C#", "PHP", "SQL",
    "React", "Vue", "Angular", "Svelte", "Next.js", "Nuxt",
    "Django", "Flask", "FastAPI", "Rails", "Spring", "Express",
    "PyTorch", "TensorFlow", "JAX", "NumPy", "Pandas",
    # 协议/数据/算法
    "PDF", "PNG", "JPG", "GIF", "MP3", "MP4", "WebP", "SVG",
    "ASCII", "UTF", "Unicode",
    "SHA", "MD5", "RSA", "ECC", "AES",
    # 货币/市场
    "USD", "EUR", "JPY", "CNY", "RMB", "GBP", "HKD", "SGD",
    "BTC", "ETH", "USDC", "USDT", "DeFi", "NFT", "DAO",
    "FOMC", "Fed", "ECB", "PBOC", "BOJ", "Treasury",
    # 学术领域常见
    "PhD", "MBA", "BSc", "MSc",
    "MIT", "Stanford", "Harvard", "Berkeley", "Caltech", "CMU",
    # 单字母/极短常用词不会被扫描（len < 3 已过滤），下面这些是 ≥3 字母但圈内通用
    "FAQ", "TODO", "FIXME", "WIP", "MVP", "POC", "RFC", "EOL",
}


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
        self.warnings: List[str] = []
        self.notes: List[str] = []

    def fail(self, code: str, msg: str) -> None:
        self.violations.append(f"[{code}] {msg}")

    def warn(self, code: str, msg: str) -> None:
        self.warnings.append(f"[{code}] {msg}")

    def note(self, msg: str) -> None:
        self.notes.append(msg)


def check_chinese_density(html_text: str, rep: Report) -> None:
    """v2.0：整篇英文密度闸门——> 30% fail，> 25% warn，> 20% note 健康。

    和 render.py 的 lang_density 对齐：先剥 script/style 再剥标签，统计中英字符占比。
    超 30% 阈值意味着产物中英混乱、模型应在生成阶段就用中文为主，不是后处理硬替换。
    """
    text = strip_tags(html_text)  # 已剥 script/style + 所有标签
    cn_chars = sum(1 for c in text if "一" <= c <= "鿿")
    en_chars = sum(1 for c in text if c.isascii() and c.isalpha())
    total = cn_chars + en_chars
    if total == 0:
        return

    en_pct = en_chars * 100.0 / total
    if en_pct > 30:
        rep.fail(
            "语言风格",
            f"英文字符占比 {en_pct:.1f}% > 30% 阈值——产物中英混乱，"
            f"模型应在生成阶段就用中文为主，不是后处理（cn={cn_chars}, en={en_chars}）",
        )
    elif en_pct > 25:
        rep.warn(
            "语言风格",
            f"英文字符占比 {en_pct:.1f}% 偏高（25-30% 之间），"
            f"建议检查是否有未注释的英文术语",
        )
    elif en_pct > 20:
        rep.note(f"[语言风格] 英文字符占比 {en_pct:.1f}% 健康范围（20-25%）")
    else:
        rep.note(f"[语言风格] 英文字符占比 {en_pct:.1f}% 良好")


def check_chinese_density_per_chapter(html_text: str, rep: Report) -> None:
    """v2.0：章节级英文密度——单章 > 35% fail，> 25% warn。精确定位中英混乱章节。

    匹配 <section class="chapter ..." id="chapter-XXX">...</section> 结构。
    样本字符总数 < 100 跳过（章节太短测不准）。
    """
    chapter_re = re.compile(
        r'<section\s+class\s*=\s*["\'][^"\']*\bchapter\b[^"\']*["\'][^>]*\bid\s*=\s*["\']chapter-([^"\']+)["\'][^>]*>',
        re.IGNORECASE,
    )
    for m in chapter_re.finditer(html_text):
        chap_id = m.group(1)
        # 用 depth 配对找闭合 </section>
        start = m.end()
        depth = 1
        i = start
        open_pat = re.compile(r"<section\b", re.IGNORECASE)
        close_pat = re.compile(r"</section\s*>", re.IGNORECASE)
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
        chap_html = html_text[start:end]
        text = strip_tags(chap_html)
        cn_chars = sum(1 for c in text if "一" <= c <= "鿿")
        en_chars = sum(1 for c in text if c.isascii() and c.isalpha())
        total = cn_chars + en_chars
        if total < 100:
            continue
        en_pct = en_chars * 100.0 / total
        if en_pct > 35:
            rep.fail(
                "章节英文密度",
                f"第 {chap_id} 章英文占比 {en_pct:.1f}% > 35% — 这一章需要重写为中文为主",
            )
        elif en_pct > 25:
            rep.warn(
                "章节英文密度",
                f"第 {chap_id} 章英文占比 {en_pct:.1f}% 偏高（建议检查未注释英文术语）",
            )


def check_unannotated_english_terms(html_text: str, rep: Report) -> None:
    """v2.0：扫描未注释英文专有名词。启发式：找首字母大写 ≥3 字母的英文词，
    检查前后 30 字符内是否有中文括号注释（中文括号 `（中文`/英文括号 `(中文`）；
    或词本身在 ENGLISH_TERM_WHITELIST 内。

    放 warn 级（启发式可能误报，比如人名首次出现已加身份注释但被剥到注释外了）。
    可疑词数 ≥ 30 时升级 fail——大量未注释意味着确实有"中英混乱"问题。
    """
    text = strip_tags(html_text)
    # 找首字母大写、连续 ≥3 个 ASCII 字母的词；可拼接多个 PascalCase（如 "OpenAI Anthropic"）
    term_re = re.compile(r"\b([A-Z][A-Za-z]{2,}(?:\s+[A-Z][A-Za-z]{2,})*)\b")

    found_terms: Dict[str, int] = {}  # term → 首次出现 pos
    for m in term_re.finditer(text):
        term = m.group(1)
        if term in ENGLISH_TERM_WHITELIST:
            continue
        # 拆开复合词，如果每个组成都在白名单内也算白
        parts = term.split()
        if len(parts) > 1 and all(p in ENGLISH_TERM_WHITELIST for p in parts):
            continue
        if len(term.replace(" ", "")) < 3:
            continue
        # 检查前后 30 字符是否有中文括号注释
        start = max(0, m.start() - 30)
        end = min(len(text), m.end() + 30)
        context = text[start:end]
        # 中文圆括号或半角括号后接中文字符（圈内常用注释格式：英文（中文））
        if re.search(r"（[一-鿿]", context) or re.search(r"\([一-鿿]", context):
            continue
        # 第一次出现记录（重复出现不重复计数）
        if term not in found_terms:
            found_terms[term] = m.start()

    if not found_terms:
        return
    n = len(found_terms)
    sample = list(found_terms.keys())[:10]
    msg = (
        f"检测到 {n} 个英文专有名词没有中文括号注释（前 10 个）："
        f"{', '.join(sample)}"
    )
    if n >= 30:
        rep.fail(
            "未注释英文术语",
            msg + f"——数量 {n} ≥ 30 升级 fail，圈外读者门槛过高",
        )
    else:
        rep.warn("未注释英文术语", msg)


def check_fact_density(html_text: str, rep: Report) -> int:
    """v1.0：事实密度未达标降级为 warning（X2 在并行加深内容；不 block X1 完成）。"""
    n = len(re.findall(r'id\s*=\s*["\']fact-\d+["\']', html_text))
    if n < FACT_MIN:
        rep.warn(
            "事实密度",
            f"fact 锚点数 {n} < 单档深度产物下限 {FACT_MIN}（warning 级别——X2 在并行加深内容）",
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


def check_grade_table(html_text: str, rep: Report) -> None:
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
    if pct < AB_MIN_PCT:
        rep.fail(
            "A+B 占比",
            f"A+B 级源占比 {pct:.1f}% < 单档深度产物下限 {AB_MIN_PCT}%（A={counts.get('A',0)}, B={counts.get('B',0)}, 总={total}）",
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


def check_known_unknowns(html_text: str, rep: Report) -> None:
    """v1.0：已知的未知数量未达标也降级为 warning（与事实密度同属内容密度类——
    X2/X3 在并行加深内容；section 缺失仍 fail，因为那是结构性缺陷）。"""
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
        if n < KU_MIN:
            rep.warn(
                "已知的未知",
                f"已知的未知条目 {n} < 单档深度产物下限 {KU_MIN}（warning 级别——X2/X3 在并行加深内容）",
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
        # 区段完全缺失——这是结构性缺陷，仍然 fail
        rep.fail(
            "已知的未知",
            f'未找到"已知的未知 / known unknowns"区段（应有 ≥{KU_MIN} 条 li）',
        )
        return
    seg = m.group(0)
    end = re.search(r"<h2\b|</section\s*>|</details\s*>", seg[20:], re.IGNORECASE)
    if end:
        seg = seg[: 20 + end.start()]
    li = re.findall(r"<li\b[^>]*>(.*?)</li>", seg, re.DOTALL | re.IGNORECASE)
    n = sum(1 for x in li if strip_tags(x).strip())
    if n < KU_MIN:
        rep.warn(
            "已知的未知",
            f"已知的未知条目 {n} < 单档深度产物下限 {KU_MIN}（warning 级别）",
        )


# ---------- 主入口 ----------

def run_checks(html_text: str) -> Report:
    rep = Report()
    rep.note(
        "v2.0 单档深度产物 · 阈值 ≥70 facts / ≥60% A+B / ≥12 已知的未知 / "
        "整篇英文≤30% / 单章英文≤35%"
    )

    # v2.0：语言风格优先级最高，三项语言闸门放最前
    check_chinese_density(html_text, rep)
    check_chinese_density_per_chapter(html_text, rep)
    check_unannotated_english_terms(html_text, rep)
    # 内容侧硬约束
    check_fact_density(html_text, rep)
    check_grade_table(html_text, rep)
    check_three_layer_chain(html_text, rep)
    check_forbidden_terms(html_text, rep)
    check_no_framework_in_headings(html_text, rep)
    check_ai_disclaimer(html_text, rep)
    check_experts(html_text, rep)
    check_known_unknowns(html_text, rep)
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
    for w in rep.warnings:
        print(f"[WARN] {w}")
    if rep.violations:
        print(f"[FAIL] 内容闸门未通过：{len(rep.violations)} 条 violations")
        for v in rep.violations:
            print(f"  - {v}")
        return 1
    if rep.warnings:
        print(f"[OK] 内容闸门通过（{len(rep.warnings)} 条 warning，未阻断）")
    else:
        print("[OK] 内容闸门通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
