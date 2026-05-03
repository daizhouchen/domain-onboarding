# 已知的未知 · Known Unknowns

> 这是入门最大的价值——不是"知道得更多"，是"知道哪里还不知道"。

## 为什么这是入门的核心价值

入门一个领域最大的陷阱叫 **Dunning-Kruger 效应**：知道得少的时候自我评估最高，知道得多反而越知道自己不知道。

```
信心 ▲
  │     ╱╲
  │    ╱  ╲___________________
  │   ╱    "愚蠢之巅"
  │  ╱       ↓
  │ ╱   "绝望之谷"
  │╱        ↓
  │     "开悟之坡"
  │      ↓
  └─────────────────────────► 知识量
```

**愚蠢之巅**就是用户读完一份"看上去专业"的水稿后到达的位置——以为自己懂了，所以做出错误决策。

**已知的未知清单**强制把用户从"愚蠢之巅"推到"绝望之谷"——这才是入门一个领域应该停留的位置。一份合格的领域报告不是让用户**自信地说话**，而是让用户**有底气地闭嘴**。

> 一份诚实的"我不知道"比一份编出来的"看上去专业"更有价值。

## 五类 Known Unknowns

每条 known unknown 都属于以下五类之一：

### 1. 概念边界模糊点

**定义**：领域内某个术语，圈内不同人用法不同，外行以为是同一个东西。

**例**：

> "AI Agent"在 2024 年至少有三种用法：
> - 派系 A（LangChain 系）：function-calling 编排循环
> - 派系 B（Anthropic computer use 系）：跑在虚拟机里操作 GUI
> - 派系 C（Devin 系）：自主长期任务执行
>
> 想搞懂去哪：分别读 LangGraph 文档、Anthropic computer-use cookbook、Devin technical report——你会发现"Agent"指的不是同一个东西。

### 2. 流派分歧未决点

**定义**：圈内有公开撕逼的流派，至今没结论。

**例**：

> 具身智能：是否需要"显式世界模型"？
> - 派系 A（李飞飞 World Labs / Yann LeCun）：必须有
> - 派系 B（Google RT-2/RT-X）：直接 VLA 端到端，不需要
>
> 想搞懂去哪：李飞飞 2024 TED Talk + LeCun 的 V-JEPA 论文 + Google RT-X 论文，三家对着读。

### 3. 数据缺口

**定义**：客观上没人有数据/数据不公开/采样有偏。

**例**：

> Pinecone 真实 ARR：所有报道（包括 The Information）都是单点 B 级源，公司本身从未在财报披露过准确数字（公司未上市）。所有"5000 万 ARR"都是估算。
>
> 想搞懂去哪：等 IPO 招股书；或者通过 AWS marketplace 用量逆推（需要内部信息）。

### 4. 未来不确定性

**定义**：依赖未来事件，目前不可知。

**例**：

> EU AI Act 2026 全面生效后对 foundation model 公司的实际影响。
> - 文本上要求很严
> - 但执法强度不明（参考 GDPR 早期执行宽松）
>
> 想搞懂去哪：跟 IAPP（隐私律师协会）的 EU AI Act tracker；订阅 European Commission AI Office 的官方更新。

### 5. 元问题（这个领域还有哪些子领域我没接触）

**定义**：你这次没覆盖到的相邻领域，但和当前领域强相关。

**例**：

> 向量数据库报告里没覆盖的元问题：
> - "稀疏向量检索"（SPLADE 系）和稠密向量混合检索（hybrid search）的趋势
> - "Reranker"作为向量检索后的二次排序——这是工程上几乎必备的步骤但本份报告没覆盖
> - 多模态向量（图像 / 视频 embedding）的存储和稠密检索差异
>
> 想搞懂去哪：Cohere reranker 文档；多模态 embedding 看 CLIP 系列论文。

## 每档位最少条数

| 档位 | 最少 known unknowns | 五类必须覆盖 |
|------|---------------------|--------------|
| 闪研 ⚡ | ≥5 | 至少覆盖 3 类 |
| 精研 📖 | ≥8 | 至少覆盖 4 类 |
| 深研 🔬 | ≥12 | 五类全覆盖 + 至少 1 个"局外人完全想不到的元问题" |

## 写法（每条 known unknown 必含两要素）

每条至少包括两个要素：

```
1. 这是个问题，因为：[为什么这个未知重要]
2. 想搞懂去：[具体的下一步行动 — 读什么/查什么/问谁]
```

**反例（不合格的 known unknown）**：

> ❌ "向量数据库未来发展不确定" — 太空泛
> ❌ "我不知道 PGVector 是否会赢" — 没说为什么这是个问题，也没说去哪查

**正例**：

> ✅ "PGVector 在 1B+ 向量规模上的真实 recall@10 数字至今没有第三方独立 benchmark。
>     - 为什么这是个问题：决定了'专用 vs 通用'之争未来 2 年的胜负
>     - 想搞懂去：自己跑 ANN-Benchmarks 上的 PGVector + 联系 Crunchy Data（PGVector 商业支持方）要客户案例数据"

## 8 条具身智能领域示范 known unknowns

具身智能（Embodied AI）2024-2026 视角的 known unknowns 示范：

> **1.（流派分歧未决）VLA 端到端 vs 显式世界模型，哪条路线 5 年内胜出？**
> - 为什么是个问题：决定了 Tesla Optimus（端到端）和 Figure（更结构化）路线选择
> - 想搞懂去：RT-X 论文 + LeCun V-JEPA + Tesla AI Day 2024 + Figure 公开 demo 对比 task generality

> **2.（概念边界模糊）"World Model"在 LeCun、李飞飞、Tesla 三家口里指的不是同一个东西。**
> - 为什么是个问题：你和别人讨论 world model，可能根本不在同一个对象上
> - 想搞懂去：LeCun JEPA 系列论文 vs 李飞飞 World Labs 官网定义 vs Tesla AI Day 中"World Model"的具体含义

> **3.（数据缺口）Figure / Apptronik / Sanctuary 的真实 demo 成功率（不是 cherry-pick 视频里的）。**
> - 为什么是个问题：人形机器人融资估值很大程度上靠 demo，但 demo 是否可重复至关重要
> - 想搞懂去：找前员工访谈（The Information / Bloomberg 偶有报道）；自己去机器人 conference 看 live demo

> **4.（未来不确定）2026 年是否会出现"机器人版 ChatGPT 时刻"？**
> - 为什么是个问题：这是整个赛道资金涌入的真正前提
> - 想搞懂去：跟 RT-X 后续工作 + 关注 Pi（Physical Intelligence）的产品节奏 + Skild AI 的 demo

> **5.（元问题）这次报告没覆盖：仿真到现实的 sim2real gap 实际工程现状。**
> - 为什么是个问题：所有训练靠仿真的路线都被 sim2real 卡脖子，但市场叙事经常忽略
> - 想搞懂去：Nvidia Isaac Sim 案例 + 阅读《Sim-to-Real Transfer in Deep Reinforcement Learning》综述

> **6.（流派分歧）数据来源之争：人类示教（teleop） vs 仿真生成 vs 互联网视频 vs 机器人自采集。**
> - 为什么是个问题：哪种数据 scaling 更快决定了谁先到 scaling law 拐点
> - 想搞懂去：1X / Tesla（teleop 派）vs Skild（互联网视频派）vs Nvidia（仿真派）三家公开访谈

> **7.（数据缺口）BOM 成本：人形机器人本体硬件实际成本是不是真的能降到 2 万美金以下？**
> - 为什么是个问题：决定了 to C 市场是否成立——超过 2 万美金没有大众市场
> - 想搞懂去：拆机视频（YouTube 上 Optimus 拆解）+ 中国电机/谐波减速器供应商访谈

> **8.（未来不确定）监管与责任分配——机器人在家里把人撞了谁负责？**
> - 为什么是个问题：to C 商业化的法律前置条件，没解决就不可能进家庭
> - 想搞懂去：跟踪美国 NHTSA 自动驾驶责任判例做类比；欧盟 Product Liability Directive 2024 修订

注意这 8 条的特点：

- 五类全覆盖（1=流派分歧、2=概念边界、3=数据缺口、4=未来不确定、5=元问题、6=流派分歧、7=数据缺口、8=未来不确定）
- 每条都有"为什么是个问题"
- 每条"想搞懂去哪"都是**具体的下一步动作**——不是"多读一些资料"

这就是合格的 known unknowns 清单。

---

## 反 AI 自反性的最后一道闸

写完一份领域报告，最后一步**强制写 known unknowns**——这一步是**对抗 AI 自身的过度自信**的关键。

模型默认状态会避免说"我不知道"——因为训练数据里大量"专业回答"都很自信。强制写 known unknowns 是在显式打开"我不知道什么"的开关。

如果你写完一份报告后写不出 ≥5 条 known unknowns——那不是这个领域真的没有 known unknowns，而是你**还没真正进入这个领域**。降档输出 + 标注"对此领域 cutoff 后不掌握，known unknowns 数量不达标"。
