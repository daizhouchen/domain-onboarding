# 技术领域 Preset · Tech Domain

> 本 preset 用于"看技术栈、看论文、看 benchmark"的领域。例：向量数据库 / 具身智能（embodied AI）/ 大模型 / 自动驾驶 / 量子计算 / 边缘计算 / 操作系统 / 编译器 / 数据库 / RTOS / 分布式系统 / 图形学。

技术领域和商业/金融/文化领域最大的不同是：**技术有 ground truth**——一个算法跑得快就是快，benchmark 数字不会骗人。所以技术领域的骨架可以更"硬"，但同时**最容易被 AI 写成 wikipedia**——因为 AI 训练数据里这种领域的"百科叙事"最厚。

> 入门一个技术领域，**先找到三件事**：(1) 这领域当前的 SOTA benchmark 是什么、谁在打榜；(2) 这领域的 v1.0 / v2.0 是哪一年、什么事件触发的；(3) 这领域的"开源 vs 闭源"裂缝在哪。三件找齐了，骨架就不会跑偏。

## 骨架五件套 · 技术领域适配

### 1. 核心概念图（Concept Map）

技术领域的概念图必须分**三层**展示，否则一定写成黑话堆。

```
┌──────────────────────────────────────────────────┐
│ 应用层    └─ 终端产品 / SDK / API / 用户场景      │
├──────────────────────────────────────────────────┤
│ 中间件层  └─ 框架 / 调度 / 索引 / 编排 / 协议      │
├──────────────────────────────────────────────────┤
│ 基础设施  └─ 硬件 / 内核 / 算法原语 / 数学基础     │
└──────────────────────────────────────────────────┘
        ＋ 评测 benchmark（横切三层）
        ＋ 关键算法（横切三层）
```

强制内容清单：

- [ ] 10-30 个必懂术语，分类到三层
- [ ] 每个术语配一句"圈外人解释" + 一句"圈内人才知道的潜台词"
- [ ] 至少 3 个核心算法（含发表年份 + 第一作者）
- [ ] 至少 1 个权威 benchmark（含当前 SOTA 数值 + cutoff 日期）

**反例（不要这样写）**：

> "向量数据库支持近似最近邻搜索（ANN），常用算法包括 HNSW、IVF、LSH 等。"

这是百科。圈外人看不懂"近似"为什么重要，圈内人看不到任何信息增量。

**正例**：

> HNSW（Hierarchical Navigable Small World，2016 Malkov）是当前向量库的事实标准索引。**圈外人解释**：建一个分层的图，让搜索像查字典——先在稀疏顶层粗搜，再下到稠密底层精搜。**圈内潜台词**：HNSW 的内存占用是 IVF 的 2-4 倍——这意味着"内存够不够"是工业部署的第一道决策门槛，不是"算法够不够准"。

### 2. 玩家地图（Player Map）

技术领域的玩家分四象限，**不能漏任何一象限**：

| 象限 | 玩家类型 | 例（向量数据库） |
|------|---------|------------------|
| 开源专用 | 单一垂直开源项目 | Milvus / Qdrant / Weaviate / Chroma |
| 商业闭源 | SaaS / managed service | Pinecone / Vespa（部分）|
| 大厂内嵌 | 通用平台的功能下沉 | PGVector / Mongo Atlas Vector / Elastic |
| 论文实验室 | 学术源头 | Microsoft Research / Meta FAIR / 各高校 IR 实验室 |

强制内容清单：

- [ ] 每象限至少 2 个玩家，含一句话定位
- [ ] 关键人物 ≥3（CTO / 首席科学家 / 知名 contributor），附 X / Twitter handle
- [ ] 主要会议 / 顶会 ≥2（NeurIPS / ICML / SIGGRAPH / SOSP / OSDI / VLDB / SIGMOD 视领域而定）
- [ ] 旗舰社区 ≥2（Discord / Slack / 邮件列表 / GitHub Discussion）

### 3. 时间轴（Timeline）

技术领域的时间轴**必须三股线并轨**：

```
论文线   ─●──────●─────●──────────●──────●─→
           ↓      ↓     ↓                 ↓
产品线   ──○──○────○────●─────●──●────●──→
                  ↓     ↓        ↓
社区线   ────────△─────△─△──△──────△──→
        （v1.0 / 稳定版 / 重大重构 / fork）
```

- ● 论文：标志性论文发表年（含 arXiv 编号）
- ○ 产品：旗舰产品发布、关键版本
- △ 社区：v1.0、ASF 毕业、Apache top-level、重要 fork

强制内容清单：

- [ ] 至少 8 个事件、跨度 ≥5 年
- [ ] 每个事件标注精确到月
- [ ] 标出"拐点年"——之前和之后玩法不同的那一年（例：2017 Transformer / 2022 ChatGPT）
- [ ] 标出"假拐点"——当时被吹爆但事后冷却的事件（自反性练习）

### 4. 矛盾结构（Tensions）

技术领域的核心矛盾通常落在四组对立轴上：

| 矛盾轴 | A 极 | B 极 | 撕裂点 |
|--------|------|------|--------|
| 开放度 | 开源 | 闭源 | 商业可持续性 vs 社区信任 |
| 出身 | 学术 | 工业 | 论文 ≠ 产品，谁的定义算数 |
| 规模 | 大模型 / 大集群 | 小模型 / 边缘 | 算力 / 隐私 / 延迟 |
| 部署 | 端 | 云 | 数据主权 / 成本 / 推理速度 |

强制内容清单：

- [ ] 至少 3 组矛盾，每组给 ≥2 个事实锚点
- [ ] 每组矛盾标"当前局势"——是 A 在赢、B 在赢，还是僵持
- [ ] 标"未解之谜"——这组矛盾的胜负条件是什么、目前没人知道答案

### 5. 学习路径（Learning Path）

技术领域的学习路径**只给两个礼拜内能消化的量**，多了等于没给：

| 资源类型 | 数量 | 要求 |
|----------|:----:|------|
| 必读论文 | 5 | 含 1 篇综述、3 篇里程碑、1 篇当前 SOTA |
| X / Twitter 账号 | 5 | 至少 2 个一线工程师，1 个怀疑派 |
| 开源 repo | 3 | clone 下来能跑出第一个 demo |
| 关键社区 | 2 | Discord / Slack / 邮件列表 |
| 关键会议 | 2 | 一年内即将召开的，给具体日期 |

**论文清单的格式硬要求**：

```
[1] Title (Author et al., Year, Conference)
    arXiv:XXXX.XXXXX
    一句话价值：这篇为什么必读
    一句话警告：读这篇时别被作者夸大的部分骗了
```

## 推荐分析工具（来自 analytical-toolbox.md）

技术领域**默认调用**这三件套，但写正文时**不要念框架名**：

### Wardley Map · 技术演化象限

把技术堆栈画成「演化阶段 × 价值链位置」二维图。横轴：creation → custom-built → product → utility。纵轴：终端用户 → 底层组件。**用法**：把领域内核心组件全标到图上，越靠右下越商品化（无利润），越靠左上越分散（高利润）。看哪些组件在向右移动——那是当前领域的"赚钱区在迁移"。

### Christensen 创新者窘境

判断当前领域是 sustaining innovation（性能不断提升）还是 disruptive innovation（一开始性能更差但成本更低）。**用法**：找"刚出来时被嘲笑、但下沉到长尾市场后反杀"的玩家。例：PGVector 起初 recall 远不如 Pinecone，但因为"已经在数据库里"而吃掉了 60% 的"够用就好"市场。

### Carlota Perez 技术革命周期

把领域放到"导入期 → 转折点 → 部署期"框架里。**用法**：判断当前在哪个阶段——导入期是泡沫期（估值乱飞），转折点是泡沫破灭（清洗），部署期才是真正的产业化（boring 但赚钱）。AI 当前（2024-2025）大概率在导入期末尾。

## 必含特殊章节

### A. 技术成熟度曲线（Hype Cycle 落点）

把领域当前位置在 Gartner 五段曲线上标一个点：technology trigger / peak of inflated expectations / trough of disillusionment / slope of enlightenment / plateau of productivity。**附两个证据锚点**：一个支持当前位置、一个反驳。

### B. 性能 / 成本 / 精度 trade-off 三角

```
              性能（QPS / latency）
                    ▲
                    │
                    │
                    │
        ────────────●────────────
       ╱                          ╲
      ╱                            ╲
     ╱                              ╲
    成本                              精度
   （$/op）                        （recall@K / accuracy）
```

任何技术决策都在三角内取舍。强制要求：在 preset 应用 demo 里**给出三个真实玩家在三角内的位置**，并解释为什么这样选。

## 完整 Preset 应用 Demo · 向量数据库

### 概念图三层填充

```
应用层    │ RAG 系统 / 推荐系统 / 语义搜索 / 多模态检索
中间件层 │ Pinecone / Milvus / Weaviate / Qdrant / PGVector
基础设施 │ HNSW / IVF / LSH / Product Quantization / GPU 索引（CAGRA）
评测     │ ANN-Benchmarks / BEIR / MTEB（横切三层）
```

关键术语样例：

- **Recall@K**：查询返回 K 个结果，其中真正命中的比例。**潜台词**：单看 recall 没意义，必须配 QPS——recall 99% / QPS 10 和 recall 95% / QPS 1000 是完全不同的产品。

### 玩家四象限填充

| 象限 | 玩家 | 一句话定位 |
|------|------|------------|
| 开源专用 | Milvus（Zilliz）| 中文社区主导、企业级、生态最厚 |
| 商业闭源 | Pinecone | RAG 时代第一个被记住的名字、API 极简 |
| 大厂内嵌 | PGVector | 不是"最好"但"已经在那"——下沉攻击的范本 |
| 论文实验室 | Microsoft Research（DiskANN）| HNSW 之外的另一条技术路线 |

### 时间轴关键事件（拐点：2022 Q4 ChatGPT 上线）

```
2016 Mar  HNSW 论文发表（arXiv:1603.09320）
2019 Oct  Milvus 1.0 发布
2021 Jan  Pinecone 公开测试版上线
2022 Nov  ChatGPT 上线 → RAG 概念爆发 → 向量库需求量级跳变
2023 Apr  Pinecone 完成 1 亿美金 B 轮（估值 7.5 亿）
2023 Jul  PGVector 0.5 发布 HNSW 支持 → 下沉攻击开始
2024 Q1   Supabase 财报把 PGVector 列为主推卖点
```

假拐点：2022 年初的"向量数据库即将颠覆 ES"——事后看 ES 仍然主导大部分非 RAG 场景。

### 矛盾结构（举一组）

**矛盾**：专用向量库 vs 通用 DB 内嵌向量列。

- 事实锚点 1：Pinecone 2024 ARR 据 The Information 5000 万美金（B 级源）
- 事实锚点 2：PGVector 0.5 在 1M 向量量级 recall 已接近 HNSW 90%（A 级源：官方 benchmark）
- 事实锚点 3：Mongo Atlas Vector 2023 Q4 上线，6 个月内拿下 30% 内部用户
- **当前局势**：B 极（内嵌）在中小规模赢，A 极（专用）在 1B+ 向量、QPS>1000 的高端场景守住
- **未解之谜**：HNSW 的内存瓶颈被磁盘索引（DiskANN / SPANN）破解后，专用库的护城河还剩多少

### 三角 Trade-off 玩家位置

| 玩家 | 性能 | 成本 | 精度 | 取舍说明 |
|------|:----:|:----:|:----:|----------|
| Pinecone | 高 | 高 | 高 | "我贵但什么都给你" |
| PGVector | 中 | 低 | 中 | "够用就好，反正已经付了 PG 的钱" |
| Milvus 自托管 | 高 | 中 | 高 | 用运维复杂度换性价比 |

### 学习路径

**论文 5 篇**：

```
[1] Efficient and robust approximate nearest neighbor search using
    Hierarchical Navigable Small World graphs (Malkov & Yashunin, 2016)
    arXiv:1603.09320
    价值：向量库的事实标准算法，不读这篇你看不懂任何 benchmark
    警告：作者对 HNSW 内存开销的描述偏乐观

[2] Billion-scale similarity search with GPUs (Johnson et al., FAIR, 2017)
    arXiv:1702.08734
    价值：FAISS 的奠基论文、工业级 ANN 的起点
    ......
```

（剩余略，应用 demo 模板已展示）

**X 账号 5 个**：@hwchase17（LangChain）/ @jxmnop（vector retrieval researcher）/ @AlphaSignalAI（怀疑派）/ @milvusio / @pinecone

**开源 repo 3 个**：milvus-io/milvus、pgvector/pgvector、erikbern/ann-benchmarks

**社区**：Milvus Discord、ANN Benchmarks GitHub Issues

**会议**：VLDB 2025（每年 8-9 月）、SIGIR 2025（每年 7 月）

## 自反性警告（技术领域专属）

技术领域最容易踩两个坑：

1. **新算法陷阱**：AI 训练数据里 arXiv 偏多，写出来一定向"最新最炫"靠。但**工业落地通常落后论文 2-4 年**——HNSW 论文 2016 发表，Pinecone 2021 才商业化。写技术领域 preset 时，**对每个"最新算法"都要追问：现在哪家公司真的在生产环境跑？**

2. **benchmark 营销陷阱**：每个公司的 benchmark 都是自家配置最优的版本。**只信第三方独立 benchmark**（ANN-Benchmarks、MTEB），公司官网的对比图全部按"营销材料"对待。
