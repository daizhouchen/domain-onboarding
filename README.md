# Domain Onboarding · 领域速通

> 30 / 60 / 90 分钟 · 从 0 到 1 拿下一个领域 · 单文件典雅 HTML

一个 Claude Code skill。给你一份**可读、可信、可考据**的领域地图——不是维基百科的长版，也不是白皮书的短版，是为「下周二要见客户」、「老板让我评估」、「我想转行」这种真实场景设计的快速建模工具。

不写水稿。不堆形容词。事实 → 机制 → 观点，每一层都向下游负责。

---

## 它在解决什么问题

你想快速吃透一个新领域，目前能拿到的东西基本都不太对：

- **维基百科**：定义齐全，但没有玩家格局、没有矛盾结构、读完不知道接下来去关注谁。
- **行业白皮书 / 券商报告**：往往单边强化主流叙事，立场预设好了，反例与失效条件被静音。
- **跑一次 Deep Research**：太重，往往一两个小时还在等，结果是个论文式长文，不是地图。
- **直接问 LLM**：常见三种翻车——堆砌定义没有结构 / 单边强化主流叙事 / 编数字凑专业感。

domain-onboarding 的定位很窄：**把一个领域蒸馏成单文件 HTML**，按你愿意花的时间分三档（30 / 60 / 90 分钟），强制结构化（骨架五件套 + 棱镜双轴 + 三层证据链），强制标注来源等级，强制声明「我不知道」的边界。

> 一份诚实的「我不知道」，比一份编出来的「看上去专业」更有用。

---

## 设计哲学

domain-onboarding 不是凭空造的，它从两个前作里继承基因，又有它自己的问题域。

| 维度 | book-distiller | prism-research | **domain-onboarding** |
|------|----------------|----------------|-----------------------|
| 蒸馏对象 | 一本书 | 一家公司 / 一个产品 / 一个对象 | **一整个领域** |
| 时间假设 | 用户愿意花 60-90 分钟读完一本书的精华 | 用户要做尽调 / 投资 / 竞品决策 | 用户从 0 起步、要快速建模 |
| 输出主轴 | 思想脉络 + 系统逻辑 | 棱镜双轴四层 + 反身性 | **骨架五件套 + 棱镜四层 + 跨领域同构** |
| 失败模式 | 把书读成读后感 | 单边吹捧或单边唱衰 | 写成维基长版 / 强化主流叙事 |
| 输出格式 | 单文件典雅 HTML | 单文件典雅 HTML | 单文件典雅 HTML（三档嵌套） |

**从 book-distiller 继承**：
- 事实 → 机制 → 观点的三层证据链宪法
- A / B / C / D 来源分级体系
- 单文件、零 CDN、可离线的典雅 HTML 美学
- 反 AI slop 守则（不写「在数字时代浪潮下」、不写「综上所述」）

**从 prism-research 继承**：
- 棱镜双轴：纵轴四层（现象 → 机制 → 结构 → 范式），横轴跨领域同构
- 反身性元透镜：主流叙事是什么？谁在传播？失效条件？
- 已知的未知清单（known unknowns），把不确定性显式化

**domain-onboarding 新增**：
- 领域分类决策树：颗粒度（超广 / 中等 / 超窄）× 成熟度（成熟 / 新兴 / 衰退）× 用户先验
- 骨架五件套：核心概念图 / 玩家地图 / 时间轴 / 矛盾结构 / 学习路径
- 三档严格嵌套（不是替代）：闪研 ⊂ 精研 ⊂ 深研，升档不丢已读内容
- AI 自反性免责：模型本身就是主流叙事的载体，让 AI 评论领域要时刻警惕这一点

---

## 三档输出

| 档位 | 时长 | 字数 | 包含 |
|------|------|------|------|
| **闪研 ⚡** | 30 min | ~3000 字 | 骨架五件套精简 + 黑话表 + 3 个最重要事实 + 来源分级 + AI disclaimer |
| **精研 📖** | 60 min | ~8000 字 | 闪研全部 + 机制层 + 反身性元透镜 + 行业认知误区 + 局内人盲区 |
| **深研 🔬** | 90+ min | ~15000 字 | 精研全部 + 结构层 + 范式层 + 跨领域同构 ≥2 + 学习路径完整版 + 自检题 ≥10 |

**事实密度量化**（自动闸门会扫）：

| 档位 | 最少事实锚点 | A+B 级源占比 |
|------|--------------|--------------|
| 闪研 ⚡ | ≥15 | ≥40% |
| 精研 📖 | ≥35 | ≥50% |
| 深研 🔬 | ≥70 | ≥60% |

每一条机制层陈述需要 ≥3 个事实锚点支持，每一条观点层陈述必须给「反例事实」或「证伪条件」。不达标 → 返工，不出 HTML。

---

## 怎么用

### 1. 安装

把这个目录放到你的 Claude Code skills 路径下：

```bash
git clone https://github.com/daizhouchen/domain-onboarding.git ~/.claude/skills/domain-onboarding
```

或者手动复制：

```bash
cp -r domain-onboarding ~/.claude/skills/
```

### 2. 触发

在 Claude Code 里直接说人话就能触发，不用记命令。下面这些 prompt 都会被识别：

```
ok 急用，我下周二要见一家做向量数据库的客户，给我一份精研档地图
老板让我评估跨境电商行业是不是值得切入，闪研一份
我想搞懂 REITs 怎么玩，深研一份
帮我吃透日本动画产业
World Model 这个领域现在到底是什么状态？
扫盲一下 SaaS 估值
```

### 3. 等对齐

skill 的第一步**不是开写**，是 30 秒对齐：

```
我理解你要的是：
- 领域：向量数据库
- 颗粒度：中等
- 成熟度：新兴（2022 年后才大规模出现）
- 假设你的水平：邻域转入（你做 backend 的，对 DB 不陌生）
- 档位：精研 60min
- preset：技术
对吗？或者直接说「按你猜的来」我就开干。
```

如果你的领域是「AI」、「金融」这种超广题，skill 会 push back 让你收敛——这是设计如此，不是 bug。

### 4. 拿到 HTML

输出在 `~/workspace/<domain-slug>/<slug>.html`，单文件、可离线、支持暗色模式、A4 打印优化（深研档）。

---

## 输出长什么样

打开 HTML 看到的结构（精研档示例）：

```
┌─ 顶部档位切换：⚡ 📖 🔬（点击切换深度）
├─ 1. 一句话定位（这个领域到底在解决什么）
├─ 2. 核心概念图 + 黑话表（10-30 个必懂术语 + 圈外人翻译）
├─ 3. 玩家地图（公司 / 人 / 学派 / 产品 + 关系网络）
├─ 4. 时间轴（关键拐点 + 时间尺度套利点）
├─ 5. 矛盾结构（核心争议 / 利益冲突 / 流派分歧）
├─ 6. 机制层（壁垒 / 规模效应 / 锁定从哪来——每条 ≥3 个事实锚点）
├─ 7. 反身性章节（主流叙事是什么 / 谁在传播 / 失效条件）
├─ 8. 行业认知误区（外部误解 ≥3）+ 局内人盲区 ≥2
├─ 9. 学习路径（next reading + 跟谁 + 订阅什么 + 哪些会议）
├─ 10. 来源分级表（A / B / C / D 占比 + 主要 A 级源列表）
├─ 11. 已知的未知清单（≥5 条 known unknowns）
└─ 12. AI 自反性 disclaimer（cutoff date + 模型作为主流叙事载体的免责）
```

视觉风格：宋体（衬线）正文 + 等宽体黑话表 + 朱砂色重点 + 水墨 SVG 装饰，单文件、零 CDN。

---

## 工作流（5 步，不可跳）

1. **领域分类决策树** — 颗粒度三问（超广 / 中等 / 超窄）+ 成熟度三问（成熟 / 新兴 / 衰退）+ 用户先验三问（零基础 / 邻域 / 有基础）。
2. **选 preset + 构建骨架五件套** — 按领域类型读 `references/domain-presets/{tech, business, finance, culture}.md`，然后填核心概念图 / 玩家地图 / 时间轴 / 矛盾结构 / 学习路径。
3. **应用棱镜双轴 + 元透镜** — 纵轴四层（现象 → 机制 → 结构 → 范式）+ 横轴跨领域同构（≥2 个案例）+ 反身性元透镜叠加。
4. **写作时保持事实-机制-观点链条** — 选分析工具但不在正文里念框架名，每条机制陈述 ≥3 个事实锚点。
5. **渲染 + 双闸门质量检查** — `scripts/render.py` 出 HTML → `scripts/quality_check.py` 扫学究腔 + 事实密度 → `scripts/visual_check.py` 扫视觉规范。任一闸门不过 → 返工。

完整规则见 `SKILL.md`。

---

## 文件结构

```
domain-onboarding/
├── SKILL.md                        # 入口，触发条件 + 工作流 + 必出元素
├── README.md                       # 你正在看的这个
├── LICENSE                         # MIT
├── .gitignore
├── references/                     # 按需读，不要一次全读
│   ├── core-thesis.md
│   ├── domain-classification-tree.md
│   ├── domain-skeleton-five.md
│   ├── domain-presets/
│   │   ├── tech.md
│   │   ├── business.md
│   │   ├── finance.md
│   │   └── culture.md
│   ├── prism-axes.md
│   ├── structure-layer-questions.md
│   ├── paradigm-layer-questions.md
│   ├── reflexivity-lens.md
│   ├── isomorphism-lens.md
│   ├── analytical-toolbox.md
│   ├── fact-mechanism-viewpoint-chain.md
│   ├── method-internalization.md
│   ├── source-grading.md
│   ├── ai-reflexivity-disclaimer.md
│   ├── known-unknowns.md
│   ├── three-tier-nesting.md
│   └── visual-style-guide.md
├── scripts/
│   ├── render.py                   # JSON → 单文件 HTML
│   ├── quality_check.py            # 内容闸：学究腔 + 事实密度 + 单边叙事扫描
│   └── visual_check.py             # 视觉闸：三档差异化比例 + SVG 合规 + 暗色模式
├── assets/                         # SVG 装饰、字体子集、CSS 模板
└── evals/
    └── evals.json                  # 8 个测试用例（覆盖技术 / 商业 / 金融 / 文化 + 颗粒度边缘）
```

---

## 强制必出元素（避免 hallucination 的护栏）

不论档位，**HTML 末尾必须包含**——这是把 AI 自我约束硬编码进输出格式，缺一项 → 自动闸门拒绝放行：

- **AI 视角局限性 disclaimer**：cutoff date + 「模型本身是主流叙事的载体」的免责。让用户知道哪些判断要去人肉验证。
- **已知的未知清单（≥5 条）**：把模型不掌握的、有争议的、cutoff 之后的事情明文列出。把不确定性显式化是降低幻觉的最有效手段。
- **推荐人 / 账号 / 会议 / 社区（≥3 个）**：让用户拿着这份地图去现实里继续校准。
- **来源分级表**：A（一手 / 业内人 / 学术）/ B（高质量行业研究）/ C（主流媒体）/ D（社交媒体 / 二手）的占比 + 主要 A/B 级源列表。

精研档及以上额外要求：
- **反身性章节**：主流叙事 + 谁在传播 + 失效条件
- **行业认知误区（外部误解 ≥3）+ 局内人盲区 ≥2**

深研档额外要求：
- **结构层提问全部回答** + **范式层提问全部回答**
- **跨领域同构案例 ≥2 个**
- **自检题 ≥10 道**（让用户读完测自己）

---

## 不适用场景（请用别的 skill）

domain-onboarding 不是万能的，遇到下面这些 case 它会主动 push back：

| 你想做的事 | 用什么 |
|------------|--------|
| 蒸馏《XX 这本书》 | [book-distiller](https://github.com/daizhouchen/book-distiller) |
| 深度 research 一家公司 / 一个产品 | [prism-research](https://github.com/daizhouchen/prism-research) |
| 单点查询「XX 是什么」 | 直接问 Claude，不用 skill |
| 「了解 AI / 金融 / 互联网」这种超广题 | 先 push back 收敛到子领域，再用本 skill |
| 「深研 HNSW 算法」这种超窄题 | 改用 prism-research（研究对象）或 book-distiller（论文 / 教材） |

push back 是设计如此。一份不合身的报告比没有报告更糟。

---

## 与其他 skill 协作

domain-onboarding 不是孤岛，它会在合适的时候调度别的工具：

- **Web search** — 补 cutoff 之后的最新事实，特别是新兴领域。
- **context7** — 涉及具体框架 / SDK 时校验文档（避免编 API）。
- **huashu-design** — 复用反 AI slop 清单和典雅 HTML 模板的设计语言。
- **book-distiller / prism-research** — push back 时直接给用户指路。

---

## 开发与测试

跑 evals：

```bash
# 在 Claude Code 里
> 用 skill-creator 跑 domain-onboarding 的 evals

# 或手动
cat evals/evals.json
```

`evals/evals.json` 包含 8 个测试用例，覆盖：
- 4 个 preset（技术 / 商业 / 金融 / 文化）× 中等颗粒度
- 新兴领域成熟度边缘（World Model）
- 衰退领域成熟度边缘（BlackBerry）
- 超广领域 push back（AI）
- 超窄领域 push back（HNSW 算法）

---

## 致谢

设计灵感与基因来源：

- [book-distiller](https://github.com/daizhouchen/book-distiller) — 事实系统化、典雅 HTML、A/B/C/D 来源分级、反 AI slop 守则
- [prism-research](https://github.com/daizhouchen/prism-research) — 棱镜双轴、跨领域同构、反身性元透镜、已知的未知清单

通过 Claude Code 的 `skill-creator` + `ccpm` + `pua` skill 协作完成。

---

## License

MIT — 见 [LICENSE](./LICENSE)。

随便改、随便用、商用也行，原始版权声明保留即可。
