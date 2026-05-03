# 视觉风格指南 · Visual Style Guide

> **典雅中文风**：宋体（衬线）正文 + 等宽体黑话表 + 朱砂色重点 + 水墨 SVG 装饰。
> 一份认真写出来的研究文档，应该看起来像**线装书 + 学术期刊**的混合，
> **不是 SaaS 落地页，不是 ChatGPT 默认输出**。

---

## 设计基调（先看这一段）

```
┌─────────────────────────────────────────────────────────────┐
│  优先级：可读性 > 信息密度 > 装饰                              │
│  审美参照：商务印书馆汉译名著系列、岩波文库、Pelican Classics │
│  反审美参照：紫色渐变 SaaS 着陆页、Gradient Hero Banner、     │
│             巨大 emoji 标题、玻璃拟态卡片                     │
└─────────────────────────────────────────────────────────────┘
```

---

## CSS 变量定义

### 颜色（必用十六进制）

```css
:root {
  /* 文字 */
  --ink-primary:   #1a1a1a;   /* 正文：纯黑略带 warm */
  --ink-secondary: #4a4a4a;   /* 次要文字 */
  --ink-tertiary:  #8a8a8a;   /* 注释、来源 */
  --ink-warn:      #8b0000;   /* 朱砂 — 重点、警告、AI disclaimer */
  --ink-stress:    #c8463a;   /* 朱砂浅 — 段内强调 */
  --ink-link:      #2c5e7a;   /* 深青 — 链接 */

  /* 纸面 */
  --paper-base:    #fdfcf8;   /* 主纸面：略带米黄，长读不刺眼 */
  --paper-tinted:  #f5f1e8;   /* 强调框、引用块 */
  --paper-line:    #e0dcd0;   /* 浅分割线 */

  /* 来源分级配色 */
  --grade-A: #8b0000;
  --grade-B: #2c3e50;
  --grade-C: #6b6b6b;
  --grade-D: #a0a0a0;
}

/* 暗色模式 */
[data-theme="dark"] {
  --ink-primary:   #e8e4d8;
  --ink-secondary: #c4c0b4;
  --ink-tertiary:  #8a8680;
  --ink-warn:      #d97a6c;   /* 朱砂在暗底要提亮 */
  --ink-stress:    #f0998c;
  --ink-link:      #87b3c4;

  --paper-base:    #1c1f23;
  --paper-tinted:  #262a30;
  --paper-line:    #3a3e44;

  --grade-A: #d97a6c;
  --grade-B: #87b3c4;
  --grade-C: #b0aca0;
  --grade-D: #6b6864;
}
```

### 字体 stack（系统字体 ONLY，零 CDN）

```css
:root {
  --font-serif:
    "Source Han Serif SC", "Source Han Serif CN",
    "Noto Serif CJK SC", "Noto Serif SC",
    "Songti SC", "STSong", "FangSong", "STFangsong",
    Georgia, "Times New Roman", serif;

  --font-mono:
    "JetBrains Mono", "Fira Code", "SF Mono",
    "Cascadia Code", Menlo, Consolas,
    "Sarasa Mono SC", "Noto Sans Mono CJK SC", monospace;

  --font-sans:
    "PingFang SC", "Hiragino Sans GB",
    "Microsoft YaHei", "Source Han Sans SC",
    -apple-system, BlinkMacSystemFont, sans-serif;
}
```

### 间距单位（基于行高）

```css
:root {
  --line: 1.75em;          /* 基础行高，长读关键 */
  --space-xs: 0.4em;
  --space-sm: 0.8em;
  --space-md: 1.4em;
  --space-lg: 2.2em;
  --space-xl: 3.5em;
  --measure: 36em;         /* 段宽——衬线体长行难读 */
}

body {
  font-family: var(--font-serif);
  line-height: var(--line);
  color: var(--ink-primary);
  background: var(--paper-base);
  max-width: var(--measure);
  margin: 0 auto;
  padding: var(--space-xl) var(--space-md);
}
```

---

## A4 打印优化（深研档必需）

```css
@page {
  size: A4;
  margin: 18mm 16mm 20mm 16mm;
  @bottom-center { content: counter(page) " / " counter(pages); }
}

@media print {
  body {
    background: white;
    color: black;
    max-width: 100%;
    font-size: 10.5pt;
  }
  /* 章节硬分页 */
  h1, h2 { page-break-after: avoid; }
  h2 { page-break-before: auto; }
  section.deep-tier-only { page-break-before: always; }
  /* 装饰元素不打印 */
  .tier-switcher, .ink-svg-deco, .theme-toggle { display: none; }
  /* 链接打印时显示 URL */
  a[href^="http"]::after { content: " ⟨" attr(href) "⟩"; font-size: 0.85em; }
  /* 来源表防孤行 */
  .source-list table { page-break-inside: auto; }
  .source-list tr { page-break-inside: avoid; }
}
```

---

## SVG 水墨装饰使用准则

```
✓ 用法：章节起首一笔（章节标题左侧 / 上方）、引文气口、章末水墨章
✗ 不要：装饰性背景大水墨、SVG 替代真正信息（图表/数据）、
        每段都来一个、动画飘动、外链 SVG（必须内嵌）
```

### 内嵌示例（章首一笔）
```html
<h2>
  <svg class="ink-svg-deco" viewBox="0 0 60 20" aria-hidden="true">
    <path d="M2,12 C8,5 18,3 28,8 S48,14 58,9"
          stroke="var(--ink-warn)" stroke-width="1.5"
          fill="none" stroke-linecap="round" />
  </svg>
  机制层 · Mechanism
</h2>
```

### 装饰用量上限
- 闪研档：≤ 3 处装饰 SVG
- 精研档：≤ 6 处装饰 SVG
- 深研档：≤ 10 处装饰 SVG
- **每个 SVG 文件大小 ≤ 4KB**，整 HTML 内嵌 SVG 总和 ≤ 30KB

### 反例（绝对不要）
```html
<!-- ✗ 全屏渐变背景 SVG 装饰 -->
<svg style="position:fixed;width:100vw;height:100vh"> ... </svg>

<!-- ✗ 在每段开头都来一个 -->
<p><svg>...</svg> 这段话开头……</p>
```

---

## 反 AI Slop 视觉清单

下列做法 = visual_check.py 直接红：

| 反模式 | 说明 | 替代方案 |
|--------|------|---------|
| ✗ 紫色渐变（`linear-gradient(purple, blue)`）作主色 | 这是 SaaS 落地页味 | 用 `--paper-tinted` 单色 + 朱砂点缀 |
| ✗ 全大写英文标题做装饰（`text-transform: uppercase`） | 是 marketing 风 | 标题保持原大小写 |
| ✗ 大量 emoji 当视觉元素（每段都有） | 是 ChatGPT 默认味 | emoji 仅用于档位切换 ⚡📖🔬 |
| ✗ box-shadow 做"卡片浮起" | 是 web 2.0 残留 | 用细边框 1px solid `--paper-line` |
| ✗ 玻璃拟态（`backdrop-filter: blur`） | 2020 视觉过时 | 不要 |
| ✗ 居中对齐做长正文（`text-align: center`） | 衬线体非居中本职 | 长正文一律左对齐 |
| ✗ Hero 大字号 banner（72px+ 标题）| Marketing 套路 | h1 上限 28-32px |
| ✗ 圆角太大（`border-radius: 16px+`） | 现代 web 套路 | ≤ 4px 或不用圆角 |
| ✗ 图标 + 标题对齐用 flex gap 4px | UI 套路 | 用排版语言：缩进、引号、破折号 |
| ✗ 渐变文字（`background-clip: text`） | 视觉噪音 | 单色 + 朱砂强调 |

---

## 中文排版细节

### 标点挤压（CSS 控制）
```css
body {
  text-align: justify;
  text-justify: inter-ideograph;
  hanging-punctuation: allow-end;
}

/* CJK 标点跟在文字后不分离 */
.title { text-spacing-trim: trim-start; }
```

### 引号方向
- 双引号：`"…"` 不要 `"…"`（大陆 / 港台都接受弯引号）
- 书名号：`《…》`，不要 `<<…>>` 或 `<…>`
- 引号嵌套：`"外层 '内层' 外层"`

### 等宽数字（财务/统计要点）
```css
.num, table td.num, .stat-value {
  font-variant-numeric: tabular-nums;
  font-family: var(--font-mono);
}
```
**用法**：表格里的数字、百分比、年份、估值——一律用 `tabular-nums`，对齐才好看。

### 连字符使用
- 中文里**不要**用 `-` 当连接符（"产品-服务" → 改"产品 / 服务"或"产品与服务"）
- 中英混排在数字与汉字之间**自动加空格**（CSS `font-feature-settings: "halt"` 或手动）
- 范围用 `–` (en-dash) 不用 `-`：`2018–2023` 而不是 `2018-2023`

### 段落首行缩进 vs 段间距
中文典雅风**二选一**：
```css
/* 风格 A · 古籍风：首行缩进 2 字 + 无段间距 */
p { text-indent: 2em; margin: 0; }

/* 风格 B · 现代学术：无缩进 + 段间距 1 行 */
p { text-indent: 0; margin: var(--space-md) 0; }
```
本 skill **推荐风格 B**——更适合长正文 + 屏幕阅读。打印 A4 时切风格 A。

---

## 黑话表 / 引用块 视觉

### 黑话表（等宽 + 双列）
```css
.jargon-table {
  font-family: var(--font-mono);
  font-size: 0.92em;
  border-collapse: collapse;
}
.jargon-table td {
  padding: var(--space-xs) var(--space-sm);
  border-bottom: 1px dotted var(--paper-line);
}
.jargon-table .term { color: var(--ink-warn); white-space: nowrap; }
.jargon-table .gloss { color: var(--ink-secondary); }
```

### 引用块（典雅范式）
```css
blockquote {
  border-left: 3px solid var(--ink-warn);
  padding: var(--space-sm) var(--space-md);
  margin: var(--space-md) 0;
  background: var(--paper-tinted);
  font-style: italic;
  color: var(--ink-secondary);
}
blockquote::before {
  content: """;
  font-size: 2em;
  color: var(--ink-warn);
  float: left;
  margin-right: 0.2em;
  line-height: 0.8;
}
```

---

## 单文件零 CDN 强制要求

```
✓ 必须：所有字体走系统字体 stack
✓ 必须：所有 SVG 内嵌（不允许 <img src="...">）
✓ 必须：所有 CSS 内嵌 <style>（不允许 <link rel="stylesheet">）
✓ 必须：所有 JS 内嵌 <script>（不允许 src）
✓ 允许：图片用 base64 内嵌（≤ 100KB 每张）
✓ 允许：特殊字体用 base64 内嵌（≤ 100KB 总和）
✗ 禁止：CDN 链接（cdnjs / unpkg / Google Fonts）
✗ 禁止：第三方 tracking / analytics
✗ 禁止：iframe / 外部 embed
```

完整文件大小目标：
- 闪研档 HTML ≤ 200 KB
- 精研档 HTML ≤ 400 KB
- 深研档 HTML ≤ 800 KB

超过 = 视觉闸门红 = 必返工压缩。

---

## 暗色模式切换（必须）

```html
<button class="theme-toggle" aria-label="切换暗色模式">
  <span class="light-icon">☼</span><span class="dark-icon">☾</span>
</button>

<script>
const setTheme = (t) => {
  document.documentElement.dataset.theme = t;
  localStorage.setItem('theme', t);
};
const saved = localStorage.getItem('theme');
setTheme(saved || (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'));
document.querySelector('.theme-toggle').onclick = () => {
  setTheme(document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark');
};
</script>
```

切换时所有用 `var(--xxx)` 的样式自动跟随。**不要**给个别元素硬编码颜色。

---

## 视觉合规 checklist

- [ ] 字体 stack 是否纯系统字体？
- [ ] 颜色是否全部走 CSS 变量？
- [ ] 朱砂红 `#8b0000` 仅用于真正的重点 / 警告 / AI disclaimer？
- [ ] 暗色模式切换流畅，无硬编码颜色泄漏？
- [ ] A4 打印预览是否正常（深研档必查）？
- [ ] 装饰 SVG 数量在上限内？
- [ ] 没有紫色渐变 / 玻璃拟态 / 阴影卡片？
- [ ] 没有居中长段正文？
- [ ] 没有 emoji 装饰段首？
- [ ] 数字使用 tabular-nums？
- [ ] 引号方向正确（中文用 "..."、书名用《》）？
- [ ] 范围使用 en-dash（–）而非 hyphen（-）？
- [ ] 单文件大小在档位限额内？
- [ ] 零 CDN，全部内嵌？
