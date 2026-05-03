---
name: domain-onboarding
description: 让用户在 30 / 60 / 90 分钟内从 0 到 1 拿下一个领域。把"领域骨架五件套（核心概念图/玩家地图/时间轴/矛盾结构/学习路径）+ 棱镜双轴四层（现象→机制→结构→范式 × 跨领域同构）+ 三层证据链（事实→机制→观点）+ A/B/C/D 来源分级 + 已知的未知清单"蒸馏成单文件典雅 HTML。无论用户说"快速了解 XX 领域"、"入门 XX"、"我下周要谈 XX 给我地图"、"闪研/精研/深研 XX"、"XX onboarding"、"XX primer"、"领域速通"、"我想搞清楚 XX 是怎么回事"、"帮我吃透 XX"、"扫盲 XX"——都用这个 skill；只要话题落在"一整个领域而非单本书或单家公司"且用户希望快速建立系统认知，就触发，**即使用户没说"领域"二字**。不适用：单本书蒸馏（用 book-distiller）、单家公司/产品深度研究（用 prism-research）、单点查询（直接回答）。
---

# Domain Onboarding · 领域速通

## 核心宪法（先读这一段，再做任何事）

**这个 skill 解决的问题**：让用户在指定时长内从 0 到 1 拿下一个**领域**——不是一本书，不是一个产品，是一整个领域。

**两种失败模式必须避免**：
- 只有结构没有事实 — 写出"看上去专业"的水稿
- 只有事实没有结构 — 写成维基百科长版

**唯一的成功路径**：**事实 → 机制 → 观点**三层证据链，每一层都向下游负责。

> 不能空有观点。事实支撑观点。揭示系统逻辑。事实陈述本身也要系统化。

这条宪法继承自 book-distiller，但在领域速通里要求更严：因为领域比单本书更容易"假装专业"——AI 自己就是主流叙事的载体，让 AI 评论领域，必须时刻警惕**自反性陷阱**（详见 `references/ai-reflexivity-disclaimer.md`）。

## 触发与反触发

### 应该触发（任意一条命中即用本 skill）
- 用户说"快速了解 XX 领域 / 入门 XX / 我想搞懂 XX / 给我 XX 的地图"
- 用户说"闪研 / 精研 / 深研 XX"
- 用户说"XX primer / XX onboarding / 领域速通 / 扫盲 XX"
- 用户描述场景："我下周要见 XX 客户"、"老板让我评估 XX"、"我想转行做 XX"
- 用户在没有明确说"领域"的情况下，问的是一个**整体格局**问题（"AI 现在是什么状态"、"REITs 怎么玩"）

### 不应触发（push back）
- "蒸馏《XX 这本书》" → 用 `book-distiller`
- "research XX 这家公司 / XX 这个产品" → 用 `prism-research`
- "XX 是什么？"——单点查询不需要 skill，直接简短回答
- 颗粒度异常（见下方决策树第一步）

## 工作流（5 步，不可跳）

### Step 1. 领域分类决策树（必须先跑，不准跳）

接到请求后**第一件事**不是开写，而是分类。读 `references/domain-classification-tree.md` 完成三问：

**Q1. 领域颗粒度**：超广 / 中等 / 超窄？
- 超广（"AI"、"金融"、"互联网"）→ **必须 push back**。给用户 3-5 个子领域候选让他选。例：用户说"了解 AI"，回："AI 太广了，请选一个：(a) 大模型基础设施 (b) AI 应用层 (c) 具身智能 (d) AI 监管与伦理 (e) AI 芯片"。
- 中等（"向量数据库"、"REITs"、"日本动画产业"）→ 正常进入。
- 超窄（"HNSW 算法"、"BERT 的 attention"）→ 建议改用 prism-research 或 book-distiller。除非用户明确坚持。

**Q2. 领域成熟度**：成熟 / 新兴 / 衰退？
- 成熟（SaaS、传统银行）：玩家地图重点，格局已稳定。
- 新兴（World Model、具身智能）：争议结构 + 不确定性重点，**禁止伪装成稳定**。
- 衰退（黑莓生态、传统出版）：教训抽取 + "还有谁在/为什么死"。

**Q3. 用户先验水平**：零基础 / 邻域转入 / 有基础求拓宽？
- 影响：黑话密度、跳过哪些常识、强调哪些迁移类比。
- 用户没说时默认"邻域转入"——技术能力强但对此领域不熟。

**输出格式**（必须先和用户对齐 30 秒，除非用户已在 prompt 里说清楚）：
```
我理解你要的是：
- 领域：XX
- 颗粒度：中等 / 超广（建议收敛）/ 超窄（建议改用 X skill）
- 成熟度：成熟 / 新兴 / 衰退
- 假设你的水平：零基础 / 邻域转入 / 有基础（猜的，错了告诉我）
- 档位：闪研 30min / 精研 60min / 深研 90min（默认精研）
- preset：技术 / 商业 / 金融 / 文化（按领域自选）
对吗？或者直接说"按你猜的来"我就开干。
```

### Step 2. 选 preset + 构建骨架五件套

按 Q3 的领域类型读对应 preset：
- 技术领域 → `references/domain-presets/tech.md`
- 商业领域 → `references/domain-presets/business.md`
- 金融领域 → `references/domain-presets/finance.md`
- 文化/社会领域 → `references/domain-presets/culture.md`

然后按 `references/domain-skeleton-five.md` 构建五件套：

```
1. 核心概念图    10-30 个必懂术语 + 互相关系（含黑话/jargon 4 类）
2. 玩家地图      公司/人/学派/产品 + 关系网络
3. 时间轴        关键事件 + 时间尺度套利点
4. 矛盾结构      核心争议、利益冲突、流派分歧
5. 学习路径      next reading + 跟谁、订阅什么、参加哪些会议/社区
```

### Step 3. 应用棱镜双轴 + 元透镜

读 `references/prism-axes.md`、`references/structure-layer-questions.md`、`references/paradigm-layer-questions.md`、`references/reflexivity-lens.md`、`references/isomorphism-lens.md`。

**纵轴四层**（每一层都必须问对应章节里的"提问范式"）：
- 现象层：发生了什么？谁在场？时间轴上的拐点？
- 机制层：怎么运转？壁垒/规模效应/锁定从哪来？
- 结构层 ⭐：为什么必须这样？哪些约束是 reality-shaping？
- 范式层 ⭐：处于哪种范式时期？硬核是什么？异端在哪？

**横轴一把**（跨领域同构）：必须给 ≥2 个同构案例（历史时期 + 邻接领域），并给"同构点"和"反同构点"。

**两个元透镜叠加**：
- 反身性：主流叙事是什么？谁在传播？自我证实链路？失效条件？
- 跨领域同构：见上。

### Step 4. 写作时保持事实-机制-观点链条

读 `references/fact-mechanism-viewpoint-chain.md`（强制规则），然后调用 `references/analytical-toolbox.md` 选取分析工具——但**不要在正文里念框架名**（详见 `references/method-internalization.md`）。

**事实密度量化指标**（quality_check.py 会扫描）：
| 档位 | 最少事实锚点 | A+B 级源占比 |
|------|--------------|--------------|
| 闪研 ⚡ | ≥15 | ≥40% |
| 精研 📖 | ≥35 | ≥50% |
| 深研 🔬 | ≥70 | ≥60% |

每个机制层陈述 ≥3 个事实锚点支持。每个观点层陈述必须给"反例事实"或"证伪条件"。

### Step 5. 渲染 + 双闸门质量检查

写中间产物 `domain.json`，然后用 `scripts/render.py` 生成单文件 HTML。最后跑两道闸门：
- **内容闸**：`scripts/quality_check.py`——扫学究腔黑名单、事实密度、单边叙事、AI 自反性 disclaimer 是否存在
- **视觉闸**：`scripts/visual_check.py`——三档差异化比例（精研 ≥1.3× 闪研、深研 ≥1.5× 精研）、SVG 装饰合规、暗色模式可切

任一闸门不过 → 返工，不出 HTML。

## 输出位置与文件结构

```
~/workspace/<domain-slug>/
├── domain.json          # 结构化中间产物（事实/机制/观点都在这里有锚点）
└── <domain>.html        # 单文件 HTML（含速读/精研/深研三模式 + 暗色模式）
```

`<domain-slug>` 用 kebab-case 英文（如 `vector-databases`、`japanese-anime-industry`）。

## 三档输出严格嵌套（不是替代）

读 `references/three-tier-nesting.md`。

```
闪研 ⚡   = 骨架五件套精简 + 黑话表 + 3 个最重要事实
精研 📖   = 闪研全部内容 + 机制层 + 反身性元透镜 + 来源分级表
深研 🔬   = 精研全部内容 + 结构层 + 范式层 + 同构案例 + 学习路径完整版
```

HTML 用同一文档 + CSS class 切换，用户点 `⚡ 📖 🔬` 按钮升档不丢已读内容。

## 强制必出元素清单（缺一项 → 返工）

不论档位，**HTML 末尾必须包含**：
- [ ] AI 视角局限性 disclaimer（cutoff date + 模型作为主流叙事载体的免责）
- [ ] 已知的未知清单（≥5 条 known unknowns，详见 `references/known-unknowns.md`）
- [ ] 推荐人/账号/会议/社区 ≥3 个（用户去人肉验证）
- [ ] 来源分级表（A/B/C/D 占比 + 主要 A/B 级源列表）

精研档及以上额外要求：
- [ ] 反身性章节（主流叙事 + 失效条件）
- [ ] 行业认知误区（外部误解 ≥3）+ 局内人盲区 ≥2

深研档额外要求：
- [ ] 结构层提问全部回答
- [ ] 范式层提问全部回答
- [ ] 跨领域同构案例 ≥2 个
- [ ] 自检题 ≥10 道（让用户读完测自己）

## 视觉风格

读 `references/visual-style-guide.md`。核心要点：
- 宋体（衬线）正文 + 等宽体黑话表 + 朱砂色重点 + 水墨 SVG 装饰
- 单文件、零 CDN、可离线
- 支持暗色模式（CSS 变量切换，研究类内容长时间阅读必备）
- A4 打印优化（深研档）

## 反 AI Slop 守则

不要写：
- "在数字时代浪潮下"等套话开头
- "综上所述/总而言之"等空洞收尾
- "波特五力分析告诉我们"等学究腔（→ 用洞见替代框架名）
- 整段整段的并列结构（每段都"首先/其次/再次"）
- 所有形容词都正向（"伟大的、卓越的、重要的"）

要写：
- 具体事实（数字、名字、年份、地点）
- 反例与证伪条件
- 不确定性的诚实标注（"我不知道"、"模型 cutoff 之后我不掌握"）
- 局内人才知道的"行话"（带圈外人解释）

## 与其他 skill 的协作

- 一手来源补全：调用 web search 获取 cutoff 之后的最新事实
- 技术文档校验：调用 context7 查框架/SDK 文档
- 可视化增强：参考 huashu-design 的反 AI slop 清单和典雅 HTML 模板

## references 索引（按需读，不要一次全读）

| 路径 | 何时读 |
|------|--------|
| `references/core-thesis.md` | 任何时候卡住，回宪法 |
| `references/domain-classification-tree.md` | Step 1 必读 |
| `references/domain-skeleton-five.md` | Step 2 必读 |
| `references/domain-presets/{tech,business,finance,culture}.md` | Step 2 选其一 |
| `references/prism-axes.md` | Step 3 必读（双轴四层概览） |
| `references/structure-layer-questions.md` | 写结构层必读 |
| `references/paradigm-layer-questions.md` | 写范式层必读 |
| `references/reflexivity-lens.md` | 反身性元透镜落地 |
| `references/isomorphism-lens.md` | 跨领域同构落地 |
| `references/analytical-toolbox.md` | 选分析工具时读 |
| `references/fact-mechanism-viewpoint-chain.md` | 写作前必读，三层证据链规则 |
| `references/method-internalization.md` | 写作时随时对照（学究腔黑名单） |
| `references/source-grading.md` | 标 A/B/C/D 来源时读 |
| `references/ai-reflexivity-disclaimer.md` | 写最终 disclaimer 必读 |
| `references/known-unknowns.md` | 写"已知的未知"清单必读 |
| `references/three-tier-nesting.md` | 三档输出规范 |
| `references/visual-style-guide.md` | 视觉与排版规范 |

## scripts 用法

```bash
# 渲染（中间 JSON → 单文件 HTML）
python scripts/render.py ~/workspace/<slug>/domain.json -o ~/workspace/<slug>/<slug>.html

# 内容闸
python scripts/quality_check.py ~/workspace/<slug>/<slug>.html

# 视觉闸
python scripts/visual_check.py ~/workspace/<slug>/<slug>.html
```

任一脚本退出码非 0 → 不允许交付，必须修复。

## 失败模式与退出协议

如果 5 步走完仍写不出合格 HTML：
1. 不要伪造（不要为了凑事实密度编数字）
2. 不要硬撑（缺一手来源就明确说"模型对此领域 cutoff 后不掌握"）
3. 输出降档版本 + 明确说明"这个版本只到 X 档因为 Y 原因"
4. 给用户列出"你需要补哪些一手材料给我，我能升档到 Z"

> 一份诚实的"我不知道"比一份编出来的"看上去专业"更有价值。
