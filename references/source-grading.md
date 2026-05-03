# 来源分级 · A / B / C / D Source Grading

> 一手 > 二手 > 模型常识。
> 来源越上，结论越能撑起重量。来源越下，越要标注"这只是模型常识"。
> 来源不够级别 → 要么 push back 让用户补料，要么主动 web search 升档，要么明确降档输出。

---

## 四级来源定义

### A 级 · 一手原始 · 最高权重

**定义**：原始记录方自己发布的、未经二次加工的内容。

**5 个具体例子**：
1. **学术原始论文**：arXiv:2310.06825 (Mistral 论文原文)
   引用语法：`<sup class="src-A">[A1]</sup>` → 末尾来源表 `A1: Mistral 7B, arXiv:2310.06825, 2023-10`
2. **监管原始文件**：SEC 10-K (Apple 2023 Annual Report)
   引用语法：`<sup class="src-A">[A2]</sup>` → `A2: Apple Inc. Form 10-K, SEC filing, 2023-09-30`
3. **公司公告/财报电话会**：NVIDIA Q3 FY24 earnings call transcript
   引用语法：`<sup class="src-A">[A3]</sup>` → `A3: NVIDIA FY24Q3 Earnings Call Transcript, 2023-11-21`
4. **创始人/亲历者第一人称**：Sam Altman 在 Lex Fridman 播客原话
   引用语法：`<sup class="src-A">[A4]</sup>` → `A4: Sam Altman on Lex Fridman Podcast #419, 2024-03, timestamp 1:23:45`
5. **官方数据集/数据库**：Bureau of Labor Statistics CPI 原数据
   引用语法：`<sup class="src-A">[A5]</sup>` → `A5: U.S. BLS CPI-U Series CUUR0000SA0, accessed 2024-11`

> **A 级关键判定**：信息源**就是事件当事人**，没有第三方加工。"创始人推特原文"是 A，"媒体报道创始人推特"是 B。

---

### B 级 · 权威加工 · 高权重

**定义**：有编辑流程、有事实核查、有声誉机制的二次加工，但加工方专业可信。

**5 个具体例子**：
1. **顶级财经媒体调查报道**：Bloomberg / Financial Times / Reuters / The Economist 长篇调查
   引用语法：`<sup class="src-B">[B1]</sup>` → `B1: "How NVIDIA Cornered the AI Market", FT, 2024-08-15`
2. **顶级科学刊物**：Nature / Science / Cell / NEJM 同行评议文章
   引用语法：`<sup class="src-B">[B2]</sup>` → `B2: Nature 615, 47–55 (2023), DOI:10.1038/s41586-022-05608-x`
3. **行业头部分析机构**：Gartner / IDC / Forrester / McKinsey Global Institute / a16z State of AI 报告
   引用语法：`<sup class="src-B">[B3]</sup>` → `B3: Gartner Magic Quadrant for Cloud Database, 2024-04`
4. **顶级行业垂直媒体**：The Information / Stratechery 付费报告 / Bain Tech Report
   引用语法：`<sup class="src-B">[B4]</sup>` → `B4: The Information, "OpenAI's Revenue Detail", 2024-09-12`
5. **官方传记 / 长篇深度访谈**：Walter Isaacson 的 Musk / 由本人授权确认事实的长访谈
   引用语法：`<sup class="src-B">[B5]</sup>` → `B5: Isaacson, W. "Elon Musk", Simon & Schuster, 2023, ch.42`

> **B 级关键判定**：有**专业编辑层把关**+ 错了会**有声誉损失** + 通常引用 A 级源。

---

### C 级 · 行业自媒体 / 圈内人观点 · 中等权重

**定义**：有专业背景但缺少正式编辑流程，或属于个人观点强但圈内权威认可。

**5 个具体例子**：
1. **知名 newsletter**：Ben Thompson 的 Stratechery 免费篇 / Packy McCormick 的 Not Boring / 王川的博客
   引用语法：`<sup class="src-C">[C1]</sup>` → `C1: Stratechery, "The Gen AI Bridge to the Future", 2024-02-26`
2. **知名播客嘉宾发言**：All-In Podcast / Acquired / 张小珺《商业访谈录》 / 后浪研究所嘉宾
   引用语法：`<sup class="src-C">[C2]</sup>` → `C2: Acquired Podcast, "TSMC", with Morris Chang quotes, 2023-04`
3. **知名 X / Twitter 行业观察账号**：@levelsio / @balajis / @swyx / @yangzhizhuo （需附 tweet ID）
   引用语法：`<sup class="src-C">[C3]</sup>` → `C3: @levelsio, X post 1820391045123, 2024-08-03`
4. **行业大会发言/录像**：NeurIPS / ICML 讲者主题报告 / VC Day 投资人公开演讲
   引用语法：`<sup class="src-C">[C4]</sup>` → `C4: Andrej Karpathy, "Intro to LLMs", YouTube, 2023-11-22`
5. **专业垂直社区共识**：Hacker News 高票讨论 / r/MachineLearning 高赞总结 / V2EX 讨论
   引用语法：`<sup class="src-C">[C5]</sup>` → `C5: HN discussion id=37234567, top comments synthesis, 2024-06`

> **C 级关键判定**：作者**有圈内 credibility** 但内容是**个人见解**——可以引用观点，不能当作"事实"使用。

---

### D 级 · 模型常识 / 二手综述 · 低权重

**定义**：没有可追溯的一手源、可能存在转述失真、属于模型训练语料的"平均认知"。

**5 个具体例子**：
1. **模型训练常识**（无具体来源）："众所周知，Transformer 由 Google 2017 年提出"
   引用语法：`<sup class="src-D">[D1]</sup>` → `D1: 模型常识，建议用户验证`
2. **维基百科条目**：Wikipedia "Vector database" 条目
   引用语法：`<sup class="src-D">[D2]</sup>` → `D2: Wikipedia, "Vector database", accessed 2024-11`
3. **普通博客 / 内容农场**：Medium 上无背景作者的综述文 / SEO 内容站
   引用语法：`<sup class="src-D">[D3]</sup>` → `D3: Medium post by anonymous author, URL, 2023`（**默认建议直接弃用**）
4. **二手综述报告**：知乎高赞回答 / CSDN 技术博客 / 36 氪转载稿
   引用语法：`<sup class="src-D">[D4]</sup>` → `D4: 知乎回答 zhihu.com/question/xxx/answer/yyy, 2024`
5. **AI 生成内容（非本次输出）**：其他 AI 摘要 / 内容农场 AI 翻写
   引用语法：`<sup class="src-D">[D5]</sup>` → `D5: 疑似 AI 生成内容，仅作参考`

> **D 级关键判定**：来源不可追溯 / 无人为编辑层 / 转述链 ≥2 层。
> **D 级使用守则**：只能用于"背景陈述"，**不可作为机制层、结构层、观点层的支撑**。

---

## 来源占比量化要求

| 档位 | A+B 占比 | 单独 D 上限 | 强制最低 A 级 |
|------|---------|-------------|---------------|
| 闪研 ⚡ 30min | ≥40% | ≤30% | ≥3 个 |
| 精研 📖 60min | ≥50% | ≤25% | ≥7 个 |
| 深研 🔬 90min | ≥60% | ≤15% | ≥15 个 |

quality_check.py 会扫描每篇 HTML 的 `<sup class="src-X">` 标记，统计占比。不达标 = 直接闸门红。

---

## A 级源不足时的三种应对路径

接到任务后**第一步**评估能搜到多少 A 级源。如果不够：

### 路径 1 · push back 给用户要料（最优）
```
我能写出来，但 A 级一手源只有 2 个，达不到精研档 ≥7 的要求。
你那边能不能给我：
  - 该领域 1-2 份内部资料（IPO 招股书、内部研究报告、监管文件原文）
  - 1-2 个圈内人的访谈/对话记录
  - 你自己的笔记或观察
有了这些我能升到精研，否则只能输出闪研档。
```

### 路径 2 · 主动 web search 升档
当用户没有内部资料时，**主动调用 web search**找：
- arXiv / SSRN / 公司财报网站 / 监管网站 (SEC EDGAR / 港交所披露易)
- 关键词组合：`"<领域>" filetype:pdf site:sec.gov` / `"<公司>" 10-K` / `"<topic>" arxiv`
- 找完后**重新计算 A+B 占比**，达标再开写

### 路径 3 · 明确降档输出
两条路都不通时：
```
我只能交付闪研档，因为：
  - A 级源只搜到 X 个，达不到精研 ≥7 的硬指标
  - 关键章节（机制层 / 结构层）缺一手锚点，只能写到现象层
  - 已知的未知清单会更长
```
**禁止做的事**：用 D 级源凑数充当 A 级 / 编造看似具体的引用。

---

## 来源标注语法范例（HTML 内嵌）

### 句中标注（短引用）
```html
向量数据库市场 2024 年规模约 $4.3B<sup class="src-B">[B7]</sup>，
但 80% 的简单场景已被 pgvector 吃掉<sup class="src-C">[C12]</sup>。
```

### 段尾合并标注（多源支撑）
```html
NVIDIA 2024 年数据中心收入超过游戏业务 5 倍以上，
这是 GPU 用途结构性转移的信号。
<span class="src-cite">[A3, B7, C2]</span>
```

### 末尾来源表（HTML 末尾固定区域）
```html
<section class="source-list">
  <h3>来源分级表 · Source Grading</h3>
  <p class="source-stats">本文件共引用 28 个来源：A 级 9 个（32%）、B 级 8 个（29%）、
     C 级 7 个（25%）、D 级 4 个（14%）。A+B 占比 61%，达深研档要求。</p>
  <table>
    <tr><th>编号</th><th>级别</th><th>引用</th></tr>
    <tr><td>A1</td><td class="grade-A">A</td><td>NVIDIA FY24Q3 10-Q, SEC filing, 2023-11-21</td></tr>
    <tr><td>B7</td><td class="grade-B">B</td><td>FT, "AI Boom or Bubble", 2024-08-15</td></tr>
    <tr><td>C12</td><td class="grade-C">C</td><td>@swyx, X post id=18203, 2024-09</td></tr>
    <tr><td>D4</td><td class="grade-D">D</td><td>知乎回答 zhihu.com/q/xxx/a/yyy</td></tr>
  </table>
</section>
```

### CSS 视觉区分（深浅四档）
```
.src-A { color: #8b0000; font-weight: 600; }   /* 朱砂 - 最显眼 */
.src-B { color: #2c3e50; }                      /* 深青 */
.src-C { color: #6b6b6b; }                      /* 中灰 */
.src-D { color: #a0a0a0; font-style: italic; }  /* 浅灰斜体 - 最淡 */
```

---

## 反模式 · 不合格的引用

```
✗ "据说……"                        ← 没有源
✗ "<sup>[1]</sup>"                  ← 没有级别
✗ "据多位业内人士透露"              ← 名字呢？至少 1 个
✗ "网上有人说……"                  ← D 级都不算
✗ "根据某权威报告"                  ← 哪个？哪一年？
✗ "Wikipedia 显示<sup>[A]</sup>"    ← 维基永远不是 A 级
```

合格的引用：
```
✓ NVIDIA 2024Q3 财报披露数据中心收入 $14.5B，同比 +279%<sup class="src-A">[A3]</sup>
✓ Sam Altman 在 Lex Fridman 播客中明确说"GPT-5 训练成本 ≥ $1B"<sup class="src-A">[A4]</sup>
✓ FT 调查记者在 8 月发文披露……<sup class="src-B">[B7]</sup>
✓ Karpathy 在 NeurIPS 主题报告中（C 级因为是个人观点）……<sup class="src-C">[C4]</sup>
```

---

## 来源使用 checklist（写完每段时自检）

- [ ] 这一段有 ≥1 个引用编号吗？纯陈述也要。
- [ ] 引用编号都加了级别 class 吗？
- [ ] D 级用在了观点层 / 机制层 / 结构层吗？（如果是，必须降到现象层或换源）
- [ ] 所有数字都有来源吗？（数字裸奔 = 闸门红）
- [ ] 末尾来源表完整吗？编号能对上吗？
- [ ] A+B 占比达标了吗？（按当前档位）
- [ ] A 级源年份是 cutoff 之内吗？cutoff 之外的标"待用户验证"
