# AI 知识图谱自生长系统 - 技术设计规格

Feature Name: ai-knowledge-graph-auto-growth
Created: 2026-03-23
Version: 0.2.0 (Draft - Enhanced)

---

## 1. 系统架构

### 1.0 版本历史

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| 0.1.0 | 2026-03-23 | 初始版本 |
| 0.2.0 | 2026-03-23 | 整合 Self-Reflection、Entity Linking、Hybrid Retrieval、Enhanced Self-Healing、Knowledge Gap Detection |

### 1.1 整体架构图

```mermaid
graph TB
    subgraph Input Layer
        URL_Input[URL Input]
        Multi_Modal_Input[Multi-Modal Input]
    end

    subgraph Adapter Layer
        URL_Adapter[URL Adapter]
        PDF_Adapter[PDF Adapter]
        Image_Adapter[Image Adapter]
        Audio_Adapter[Audio Adapter]
    end

    subgraph Core Processing Layer
        Content_Normalizer[Content Normalizer]
        AI_Analyzer[AI Analyzer]
        Knowledge_Extractor[Knowledge Extractor]
        Security_Reviewer[Security Reviewer]
        Human_InLoop[Human In-Loop Handler]
    end

    subgraph Storage Layer
        Graph_DB[(Graph Database)]
        Vector_Store[(Vector Store)]
        File_System[File System]
        Config_Store[Config Store]
    end

    subgraph Output Layer
        Graph_Visualizer[Knowledge Graph Visualizer]
        Skill_Generator[Skill Generator]
        MCP_Server[MCP Server Generator]
        Report_Generator[Report Generator]
    end

    subgraph Intelligence Layer
        Active_Learner[Active Learner]
        Self_Healer[Self-Healing Engine]
        Audit_Logger[Audit Logger]
    end

    URL_Input --> URL_Adapter
    Multi_Modal_Input --> Adapter_Layer
    PDF_Adapter --> Content_Normalizer
    Image_Adapter --> Content_Normalizer
    URL_Adapter --> Content_Normalizer
    Content_Normalizer --> AI_Analyzer
    AI_Analyzer --> Knowledge_Extractor
    Knowledge_Extractor --> Security_Reviewer
    Security_Reviewer -->|Pass| Graph_DB
    Security_Reviewer -->|Block| Human_InLoop
    Human_InLoop -->|Approve| Graph_DB
    Human_InLoop -->|Reject| Audit_Logger
    Graph_DB --> Graph_Visualizer
    Graph_DB --> Skill_Generator
    Skill_Generator --> File_System
    File_System --> MCP_Server
    Active_Learner -->|Learn| Adapter_Layer
    Active_Learner -->|Sync| Graph_DB
    Self_Healer -->|Monitor| All_Components
```

### 1.2 核心处理流程

```mermaid
sequenceDiagram
    participant U as User
    participant F as URL Fetcher
    participant C as Content Analyzer
    participant K as Knowledge Extractor
    participant S as Security Reviewer
    participant G as Graph Builder
    participant O as Skill Generator
    participant H as Human Handler

    U->>F: Submit URL
    F->>C: Fetched Content
    C->>K: Analyzed Structure
    K->>S: Extracted Knowledge
    S->>S: Check Against Rules
    
    alt Content Passes
        S->>G: Approved Knowledge
        G->>O: Persisted Nodes
        O->>U: Generated Skills
    else Content Blocked
        S->>H: Flagged Content
        H->>U: Request Review
        U->>H: Review Decision
        H->>G: Apply Decision
    end
```

---

## 2. 组件设计

### 2.1 配置中心 (Configuration Manager)

**职责：** 统一管理系统全部配置

**接口：**
```python
class ConfigManager:
    def load(self, config_path: str = "config/config.yaml") -> Config
    def get(self, key: str, default: Any = None) -> Any
    def set(self, key: str, value: Any) -> None
    def reload(self) -> None  # 热重载
    def validate(self) -> ValidationResult
```

**配置结构 (config.yaml)：**
```yaml
system:
  name: "ai-knowledge-graph"
  mode: "development"  # development | production | minimal
  log_level: "INFO"

url_fetch:
  timeout: 30
  max_content_size: 1048576  # 1MB
  user_agents:
    - "Mozilla/5.0 (compatible; KnowledgeBot/1.0)"
  retry_count: 3
  retry_delay: 2.0

ai_analysis:
  provider: "openai"  # openai | anthropic | local
  model: "gpt-4o-mini"
  api_key_env: "OPENAI_API_KEY"
  temperature: 0.3
  max_tokens: 4096
  timeout: 60
  confidence_threshold: 0.6

knowledge_graph:
  database:
    type: "neo4j"  # neo4j | tidb
    uri: "bolt://localhost:7687"
    username: "neo4j"
    password_env: "NEO4J_PASSWORD"
  node_types:
    - "concept"
    - "entity"
    - "event"
    - "claim"
    - "relation"
  edge_types:
    - "implies"
    - "causes"
    - "similar_to"
    - "contrasts"
    - "part_of"
    - "happens_before"
  merge_threshold: 0.9

skill_generator:
  output_dir: "output/skills"
  format: "json"  # json | yaml
  version_scheme: "semver"
  mcp_compatible: true

security_review:
  enabled: true
  blacklist:
    harmful:
      - "violence"
      - "crime"
      - "illegal"
    privacy:
      - "pii"
      - "personal_data"
    misleading:
      - "disinformation"
      - "conspiracy"
  action_on_match: "flag"  # flag | block | approve
  require_secondary_review: false

human_inloop:
  pending_review_dir: "pending_review"
  confidence_threshold: 0.6
  merge_ambiguity_range: [0.7, 0.9]
  auto_continue_on_timeout: false
  timeout_hours: 72

active_learning:
  enabled: false
  trigger:
    type: "scheduled"  # scheduled | token_budget | goal_based
    cron: "0 2 * * *"  # 每天凌晨2点
    token_daily_limit: 100000
  require_approval: true
  termination_file: ".stop_learning"
  search_engines:
    - "arxiv"
    - "google_scholar"
    - "duckduckgo"

self_healing:
  enabled: true
  max_retries: 3
  backoff_multiplier: 2.0
  error_log: "logs/error_recovery.jsonl"

storage:
  graph_db: "data/graph.db"
  vector_store: "data/vectors"
  cache: "data/cache"
```

---

### 2.2 URL 抓取器 (URL Fetcher)

**职责：** 获取 URL 内容，提取主文本

**接口：**
```python
class URLFetcher:
    async def fetch(self, url: str) -> FetchResult
    def extract_main_content(self, html: str) -> ExtractedContent
    def detect_language(self, text: str) -> str
```

**输出结构：**
```python
@dataclass
class FetchResult:
    url: str
    status_code: int
    headers: Dict[str, str]
    content: bytes
    encoding: str
    final_url: str  # 重定向后URL

@dataclass
class ExtractedContent:
    title: str
    text: str
    images: List[str]
    links: List[str]
    language: str
    publish_date: Optional[str]
```

---

### 2.3 AI 分析器 (AI Analyzer) - 增强版 (含 Self-Reflection)

**职责：** 调用 LLM 分析内容，提取知识，并进行自我反思验证

**接口：**
```python
class AIAnalyzer:
    def __init__(self, config: AIAnalysisConfig)
    async def analyze(self, content: ExtractedContent) -> AnalysisResult
    async def extract_knowledge(self, content: str, context: Dict) -> List[KnowledgeUnit]
    async def self_reflect(self, knowledge_units: List[KnowledgeUnit]) -> ReflectionResult
```

**Self-Reflection 流程：**
```mermaid
flowchart TD
    A[提取的知识单元] --> B{Is Relevant?}
    B -->|高相关| C{Is Supported?}
    B -->|低相关| D[标记: 可跳过]
    C -->|有证据| E{Is Useful?}
    C -->|无证据| F[标记: 需验证]
    E -->|是| G[保留]
    E -->|否| H[标记: 重新提取]
    D --> I[过滤]
    F --> J[(待验证队列)]
    H --> K[重试]
    G --> L[知识入库]
```

**反射检查 Prompt：**
```
你是一个知识质量审计员。请审查以下提取的知识是否满足质量标准：

知识单元：
{knowledge_unit}

请回答以下问题并给出 JSON：
{
  "is_relevant": true/false,  // 内容是否与原文主题相关
  "relevance_score": 0.0-1.0,
  "is_supported": true/false,  // 是否有足够的文本证据支持
  "supporting_evidence": ["证据片段"],
  "is_useful": true/false,    // 是否是有价值的知识
  "quality_score": 0.0-1.0,
  "issues": ["问题描述"],
  "suggestion": "改进建议"
}
```

**Prompt 模板：**
```
你是一个知识提取专家。从以下内容中提取结构化的知识节点和关系。

内容：
{content}

请以 JSON 格式输出：
{
  "topics": ["核心主题列表"],
  "entities": [
    {
      "name": "实体名称",
      "type": "person|organization|location|technology|concept",
      "description": "实体描述",
      "confidence": 0.0-1.0
    }
  ],
  "knowledge": [
    {
      "id": "唯一ID",
      "type": "claim|fact|relationship",
      "content": "知识内容",
      "confidence": 0.0-1.0,
      "supporting_evidence": ["支持证据"]
    }
  ],
  "relationships": [
    {
      "source": "来源节点ID",
      "target": "目标节点ID",
      "type": "implies|causes|similar_to|contrasts|part_of",
      "confidence": 0.0-1.0
    }
  ]
}
```

---

### 2.4 知识图谱构建器 (Knowledge Graph Builder)

**职责：** 存储和管理知识图谱

**新增：Entity Linker（实体链接器）**
```python
class EntityLinker:
    """解决同一实体不同表述问题 (Entity Disambiguation)"""
    def __init__(self, config: EntityLinkerConfig)
    async def link_entity(self, mention: str, context: str) -> List[CandidateEntity]
    async def disambiguate(self, candidates: List[CandidateEntity]) -> CanonicalEntity
    async def create_alias(self, canonical_id: str, alias: str) -> None
    def get_canonical_name(self, entity_id: str) -> str
```

**Entity Linking 流程：**
```
实体提及 → 候选生成 → 上下文编码 → 消歧选择 → 规范实体
   ↓
"AI" / "人工智能" / "Artificial Intelligence" → 统一为 "Artificial Intelligence (AI)"
```

**接口：**
```python
class KnowledgeGraphBuilder:
    def __init__(self, config: KnowledgeGraphConfig)
    async def add_node(self, node: KnowledgeNode) -> str
    async def add_edge(self, edge: KnowledgeEdge) -> str
    async def merge_nodes(self, node_ids: List[str], strategy: str) -> KnowledgeNode
    async def link_entity(self, mention: str, context: str) -> CanonicalEntity  # 新增
    async def query(self, query: str) -> QueryResult
    async def query_hybrid(self, query: str, vector_store: VectorStore) -> HybridResult  # 新增
    async def get_subgraph(self, node_id: str, depth: int) -> SubGraph
    async def export(self, format: str) -> bytes
```

**数据模型：**
```python
@dataclass
class KnowledgeNode:
    id: str  # UUID + 内容指纹
    type: NodeType  # concept, entity, event, claim, relation
    name: str
    description: str
    source_url: str
    created_at: datetime
    updated_at: datetime
    confidence: float
    tags: List[str]
    metadata: Dict[str, Any]

@dataclass
class KnowledgeEdge:
    id: str
    source_id: str
    target_id: str
    relation_type: EdgeType
    confidence: float
    evidence: List[str]
    created_at: datetime
    metadata: Dict[str, Any]

@dataclass
class KnowledgeEntry:
    node: KnowledgeNode
    summary: str  # 供人类审核的摘要
    status: EntryStatus  # pending, approved, rejected
    reviewed_by: Optional[str]
    reviewed_at: Optional[datetime]
```

---

### 2.4.5 Hybrid Query Engine（混合检索引擎）

**职责：** 融合向量检索和图检索，提供更准确的查询结果

**架构：**
```mermaid
flowchart LR
    A[Query] --> B[Query Rewrite]
    B --> C[HyDE 生成假设答案]
    C --> D[并行检索]
    D --> E1[Vector Search]
    D --> E2[Graph Search]
    E1 --> F[Reranker]
    E2 --> F
    F --> G[LLM 合成]
    G --> H[最终答案]
```

**接口：**
```python
class HybridQueryEngine:
    def __init__(self, graph_db: GraphDatabase, vector_store: VectorStore)
    async def query(self, user_query: str, options: QueryOptions) -> HybridResult
    async def rewrite_query(self, query: str) -> List[str]  # 子查询分解
    async def rerank(self, vector_results: List, graph_results: List) -> List[RerankedResult]
```

**配置新增：**
```yaml
hybrid_retrieval:
  enabled: true
  vector_weight: 0.4  # 向量检索权重
  graph_weight: 0.6    # 图检索权重
  use_hyde: true       # 使用 HyDE 生成假设答案
  reranker_model: "cross-encoder/ms-marco-MiniLM-L-6-v2"
  top_k: 20            # 召回数量
```

---

### 2.5 Skill 生成器 (Skill Generator)

**职责：** 将知识条目转换为可执行的 Skills/MCP 格式

**接口：**
```python
class SkillGenerator:
    def __init__(self, config: SkillGeneratorConfig)
    def generate(self, knowledge_entry: KnowledgeEntry) -> Skill
    def generate_batch(self, entries: List[KnowledgeEntry]) -> List[Skill]
    def export_to_file(self, skill: Skill, path: str) -> None
    def generate_mcp_server(self, skills: List[Skill]) -> MCPServerDefinition
```

**Skill 输出格式：**
```json
{
  "name": "understand-[topic-name]",
  "version": "1.0.0",
  "description": "This skill provides knowledge about [topic]",
  "category": "knowledge",
  "tags": ["topic", "domain"],
  "parameters": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "The specific question about [topic]"
      }
    },
    "required": ["query"]
  },
  "actions": [
    {
      "step": 1,
      "description": "Recall relevant knowledge about [topic]",
      "instruction": "Search the knowledge graph for nodes related to [topic]"
    },
    {
      "step": 2,
      "description": "Synthesize information",
      "instruction": "Combine relevant nodes to form a comprehensive answer"
    }
  ],
  "examples": [
    {
      "input": "What is [topic]?",
      "output": "Detailed explanation based on knowledge graph"
    }
  ],
  "source_knowledge_ids": ["node_id_1", "node_id_2"],
  "confidence": 0.85,
  "generated_at": "2026-03-23T12:00:00Z"
}
```

---

### 2.6 安全审查器 (Security Reviewer)

**职责：** 检测有害内容，保护系统安全

**接口：**
```python
class SecurityReviewer:
    def __init__(self, config: SecurityReviewConfig)
    async def review(self, content: str) -> SecurityResult
    async def check_keywords(self, text: str) -> List[KeywordMatch]
    async def secondary_review(self, content: str) -> SecondaryResult  # AI 二次审查
```

**输出结构：**
```python
@dataclass
class SecurityResult:
    status: SecurityStatus  # passed, flagged, blocked
    matches: List[KeywordMatch]
    confidence: float
    reason: str
    action_taken: str
    reviewed_at: datetime

@dataclass
class KeywordMatch:
    category: str  # harmful, privacy, misleading
    keyword: str
    position: int  # 匹配位置
    context: str   # 上下文
```

---

### 2.7 主动学习器 (Active Learner) - 增强版 (含 Knowledge Gap Detection)

**职责：** 依据目标自动搜索和学习知识，并主动发现知识缺口

**接口：**
```python
class ActiveLearner:
    def __init__(self, config: ActiveLearningConfig)
    async def learn(self, goal: LearningGoal) -> LearningResult
    async def search_knowledge(self, query: str) -> List[SearchResult]
    async def evaluate_knowledge_gap(self) -> Dict[str, float]
    async def detect_gaps(self) -> List[KnowledgeGap]
    async def plan_learning(self, gaps: List[KnowledgeGap]) -> LearningPlan
    def should_terminate(self) -> bool  # 检查终止信号
```

**Knowledge Gap Detection 流程：**
```mermaid
flowchart TD
    A[知识图谱] --> B[Query Frequency Analysis]
    A --> C[Missing Entity Type Detection]
    A --> D[Weak Coverage Area]
    A --> E[Outdated Knowledge Check]
    B --> F[Gap Score Calculator]
    C --> F
    D --> F
    E --> F
    F --> G[Priority Queue]
    G --> H[Learning Plan]
    H --> I[执行学习]
```

**Knowledge Gap 数据模型：**
```python
@dataclass
class KnowledgeGap:
    gap_type: GapType  # missing_entity, weak_relation, outdated, low_coverage
    target: str  # 缺口目标描述
    impact_score: float  # 影响程度
    uncertainty: float  # 不确定性
    suggested_queries: List[str]  # 建议搜索词
    priority: float  # computed: impact × uncertainty / cost
```

---

### 2.8 自愈引擎 (Self-Healing Engine) - 增强版 (含 CRAG 外部验证)

**职责：** 自动处理可预测错误，并支持知识验证

**错误分类引擎：**
```python
class ErrorClassifier:
    """将错误分类为：瞬态 / 持久性 / 未知"""
    def classify(self, error: Exception) -> ErrorCategory
    def should_retry(self, error: Exception) -> bool
    def should_escalate(self, error: Exception) -> bool
```

**增强的恢复策略：**
```python
class SelfHealingStrategy(ABC):
    @abstractmethod
    def can_handle(self, error: Exception) -> bool
    @abstractmethod
    async def heal(self, error: Exception) -> HealingResult

class RetryStrategy(SelfHealingStrategy):
    """指数退避重试"""
    async def heal(self, error: Exception) -> HealingResult

class FallbackStrategy(SelfHealingStrategy):
    """降级到备用方案（备用模型/备用数据源）"""

class CircuitBreakerStrategy(SelfHealingStrategy):
    """熔断器模式（快速失败，防止雪崩）"""

class ExternalVerificationStrategy(SelfHealingStrategy):
    """CRAG 外部验证：当知识置信度低时，自动触发网页搜索验证"""

class HumanEscalationStrategy(SelfHealingStrategy):
    """人工升级：不可恢复错误升级给人工处理"""
```

**Self-Healing 流程：**
```mermaid
flowchart TD
    A[错误发生] --> B{错误分类}
    B -->|瞬态| C[Retry with Backoff]
    B -->|持久性| D[启用 Fallback]
    B -->|未知| E[分析错误模式]
    C --> F{恢复成功?}
    D --> G{恢复成功?}
    E --> H[更新规则库]
    F -->|是| I[继续执行]
    F -->|否| J[熔断]
    G -->|是| I
    G -->|否| J
    J --> K[Human Escalation]
    H --> C
```

**配置增强：**
```yaml
self_healing:
  enabled: true
  max_retries: 3
  backoff_multiplier: 2.0
  error_log: "logs/error_recovery.jsonl"
  
  # 新增：外部验证配置
  external_verification:
    enabled: true
    trigger_confidence_threshold: 0.6
    web_search_provider: "duckduckgo"  # or "serpapi"
    max_verification_results: 5
    
  # 新增：熔断器配置
  circuit_breaker:
    failure_threshold: 5
    recovery_timeout: 60
```

---

## 3. 目录结构

```
ai-knowledge-graph/
├── config/
│   └── config.yaml              # 主配置文件
├── src/
│   ├── __init__.py
│   ├── main.py                  # 入口文件
│   ├── config/
│   │   ├── __init__.py
│   │   └── manager.py           # 配置管理器
│   ├── adapters/
│   │   ├── __init__.py
│   │   ├── base.py              # Base Adapter
│   │   ├── url_adapter.py       # URL 抓取
│   │   ├── pdf_adapter.py       # PDF 解析
│   │   └── multimodal_adapter.py # 多模态
│   ├── core/
│   │   ├── __init__.py
│   │   ├── analyzer.py          # AI 分析器 (含 Self-Reflection)
│   │   ├── extractor.py         # 知识提取器
│   │   ├── normalizer.py        # 内容规范化
│   │   └── entity_linker.py    # Entity Linker (新增)
│   ├── graph/
│   │   ├── __init__.py
│   │   ├── builder.py           # 图谱构建器
│   │   ├── query.py             # 图谱查询
│   │   ├── hybrid_query.py      # Hybrid Query Engine (新增)
│   │   └── visualizer.py        # 可视化
│   ├── generation/
│   │   ├── __init__.py
│   │   ├── skill_generator.py   # Skill 生成
│   │   └── mcp_server.py        # MCP Server 生成
│   ├── security/
│   │   ├── __init__.py
│   │   ├── reviewer.py          # 安全审查
│   │   └── blacklist.py         # 黑名单管理
│   ├── intelligence/
│   │   ├── __init__.py
│   │   ├── active_learner.py     # 主动学习 (含 Gap Detection)
│   │   ├── self_healer.py      # 自愈引擎 (增强版)
│   │   └── error_classifier.py # 错误分类器 (新增)
│   ├── human_inloop/
│   │   ├── __init__.py
│   │   ├── handler.py           # 人工介入处理
│   │   └── pending_queue.py     # 待审核队列
│   └── storage/
│       ├── __init__.py
│       ├── graph_db.py          # 图数据库
│       ├── vector_store.py      # 向量存储
│       └── cache.py             # 缓存
├── output/
│   ├── skills/                  # 生成的 Skills
│   │   └── {category}/
│   ├── graph/                   # 知识图谱导出
│   │   ├── json/
│   │   └── html/
│   └── mcp_server/              # MCP Server 定义
├── pending_review/              # 待人工审核
├── logs/
│   ├── error_recovery.jsonl
│   ├── security_review.jsonl
│   └── active_learning.jsonl
├── data/
│   ├── graph.db/
│   ├── vectors/
│   └── cache/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── pyproject.toml
├── requirements.txt
└── README.md
```

---

## 4. 核心数据流

### 4.1 内容处理流程

```mermaid
flowchart LR
    A[URL] --> B[URL Fetcher]
    B --> C[Content Normalizer]
    C --> D[AI Analyzer]
    D --> E[Knowledge Extractor]
    E --> F{Security Review}
    F -->|Pass| G[Knowledge Graph Builder]
    F -->|Flag| H[Human In-Loop]
    G --> I[Skill Generator]
    I --> J[(File System)]
    G --> K[Graph Visualizer]
```

### 4.2 知识入库决策流程

```mermaid
flowchart TD
    A[New Content] --> B[Confidence Check]
    B -->|High > 0.8| G[Auto Approve]
    B -->|Medium 0.6-0.8| C[Security Check]
    B -->|Low < 0.6| D[Human Review]
    C -->|Pass| G
    C -->|Flag| D
    D -->|Approve| G
    D -->|Reject| E[(Log & Discard)]
    G --> F[Add to Knowledge Graph]
```

---

## 5. 错误处理策略

| 错误类型 | 处理策略 | 恢复方式 |
|----------|----------|----------|
| URL 抓取超时 | 重试 | 更换 User-Agent，降低并发 |
| LLM API 限流 | 队列 + 退避 | 指数退避，启用备用模型 |
| 图数据库断开 | 缓存 | 本地缓存，定期重连 |
| 解析格式错误 | 记录 + 标记 | 标记人工审核 |
| 安全审查不确定 | 升级 | 人工判断 |

---

## 6. MCP Server 集成（长远）

```mermaid
graph LR
    KG[Knowledge Graph] --> SG[Skill Generator]
    SG --> MC[MCPServer Config]
    MC --> RT[Runtime]
    RT --> AI[AI Agent]
    AI -->|Use Skill| RT
```

**MCP Server 配置文件：**
```json
{
  "mcp_version": "1.0.0",
  "name": "knowledge-graph-mcp",
  "description": "Access knowledge graph for AI agents",
  "tools": [
    {
      "name": "search_knowledge",
      "description": "Search knowledge graph by topic or entity",
      "inputSchema": {
        "type": "object",
        "properties": {
          "query": {"type": "string"},
          "limit": {"type": "integer", "default": 10}
        }
      }
    },
    {
      "name": "get_related",
      "description": "Get related knowledge nodes",
      "inputSchema": {
        "type": "object",
        "properties": {
          "node_id": {"type": "string"},
          "depth": {"type": "integer", "default": 1}
        }
      }
    }
  ]
}
```

---

## 7. 扩展性设计

### 7.1 插件式 Adapter

```python
class BaseAdapter(ABC):
    @abstractmethod
    def can_handle(self, input_type: str) -> bool
    @abstractmethod
    async def adapt(self, input_data: Any) -> ContentUnit

class AdapterRegistry:
    def register(self, adapter: BaseAdapter) -> None
    def get(self, input_type: str) -> BaseAdapter
    def list_all(self) -> List[BaseAdapter]
```

### 7.2 插件式 Output

```python
class BaseOutputAdapter(ABC):
    @abstractmethod
    def can_handle(self, output_type: str) -> bool
    @abstractmethod
    async def export(self, data: KnowledgeGraph, options: Dict) -> bytes

class OutputAdapterRegistry:
    def register(self, adapter: BaseOutputAdapter) -> None
    def get(self, output_type: str) -> BaseOutputAdapter
```

---

## 8. 安全考虑

1. **输入验证**：所有外部输入严格验证，防止注入攻击
2. **API 密钥**：存储在环境变量，不写入配置文件
3. **数据隔离**：不同租户数据逻辑隔离
4. **审计日志**：所有操作记录日志，可追溯
5. **内容过滤**：黑名单 + AI 二次审查
6. **速率限制**：API 调用限流，防止滥用

---

## 9. 性能优化

1. **并发处理**：使用 async/await 提高吞吐量
2. **缓存**：热门知识节点缓存到内存
3. **批处理**：小任务批量提交，减少 API 调用
4. **懒加载**：图可视化懒加载大图谱
5. **索引**：向量数据库索引优化检索

---

## 10. 测试策略

| 测试类型 | 覆盖内容 | 工具 |
|----------|----------|------|
| 单元测试 | 各模块独立逻辑 | pytest |
| 集成测试 | 模块间交互 | pytest + docker |
| E2E 测试 | 完整流程 | Playwright |
| 压力测试 | 高并发场景 | locust |
| 安全测试 | 注入攻击、绕过 | OWASP ZAP |

---

## 11. 部署建议

### 原型阶段
- 单机部署，Neo4j Community Edition
- Docker Compose 一键启动

### 生产阶段
- Kubernetes 集群部署
- Neo4j Enterprise + 因果集群
- Redis 缓存层
- CDN 加速静态资源

---

## 12. 依赖技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 语言 | Python 3.11+ | 生态丰富 |
| 框架 | FastAPI | 异步，高性能 |
| 图数据库 | Neo4j | 成熟，稳定 |
| 向量检索 | Qdrant | 轻量，易用 |
| LLM 集成 | LiteLLM | 统一接口 |
| URL 抓取 | Playwright | JS 渲染支持 |
| 配置 | Pydantic + YAML | 类型安全 |
| 可视化 | D3.js | 成熟，交互强 |

