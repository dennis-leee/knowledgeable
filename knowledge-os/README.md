# Knowledge OS

**AI 知识图谱自生长系统** - 自动从 URL 提取知识、构建知识图谱、生成 AI 可用的 Skills/MCP 格式。

## 特性

- **自动知识提取**: 从任意 URL 自动提取实体、关系、洞察
- **知识图谱构建**: 自动构建可查询的知识图谱
- **多格式输出**: 支持 Markdown、JSON Graph、Vector Embeddings
- **AI Skills 生成**: 输出 AI Agent 可直接使用的 Skills 格式
- **MCP 兼容**: 支持 Model Context Protocol 标准
- **自我修复**: Validation + LLM Repair 自动修复数据质量问题
- **人类介入**: 仅在低置信度时触发人工审核

## 系统架构

```
URL Input
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│                    LangGraph Pipeline                        │
│                                                             │
│  ┌──────────┐    ┌───────────┐    ┌────────┐    ┌─────────┐  │
│  │Ingestion│───▶│Summarizer│───▶│ Entity │───▶│Relation│  │
│  └──────────┘    └───────────┘    └────────┘    └─────────┘  │
│                                               │             │
│  ┌────────┐    ┌──────────┐         ┌────────▼────────┐    │
│  │ Skills │◀──│  Memory  │◀───────│   Validation    │    │
│  └────────┘    └──────────┘         └────────┬────────┘    │
│                                               │             │
│                                         ┌─────▼─────┐     │
│                                         │  Repair   │─────┘
│                                         └───────────┘  (retry)
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│ Markdown   │  │ JSON Graph │  │   Skills   │
│ (Human)   │  │  (Graph)   │  │ (AI Agent) │
└─────────────┘  └─────────────┘  └─────────────┘
```

## 目录结构

```
knowledge-os/
├── app/
│   ├── main.py                    # CLI 入口
│   ├── config.yaml                # 配置文件
│   ├── agents/                    # Agent 实现
│   │   ├── base.py               # BaseAgent 基类
│   │   ├── ingestion.py          # URL 内容抓取
│   │   ├── summarizer.py         # 摘要生成
│   │   ├── entity.py             # 实体抽取
│   │   ├── relation.py           # 关系抽取
│   │   ├── insight.py            # 洞察提取
│   │   ├── structuring.py        # 知识组装
│   │   ├── validation.py         # 质量验证
│   │   ├── repair.py             # LLM 自修复
│   │   ├── memory.py             # 持久化存储
│   │   └── skills.py            # Skills 生成
│   ├── schemas/                   # Pydantic 数据模型
│   │   ├── knowledge.py          # Knowledge 模型
│   │   └── skill.py              # Skill 模型
│   ├── storage/                   # 存储适配器
│   │   ├── markdown.py           # Markdown 存储
│   │   ├── graph.py              # JSON Graph 存储
│   │   └── vector.py             # Vector 存储 (Chroma)
│   ├── orchestrator/            # 编排层
│   │   ├── graph.py             # KnowledgePipeline
│   │   └── state.py              # PipelineState
│   ├── config/                   # 配置管理
│   │   └── manager.py           # ConfigManager
│   ├── utils/                    # 工具函数
│   │   ├── llm.py               # LLM 接口
│   │   ├── retry.py              # 重试机制
│   │   └── confidence.py        # 置信度计算
│   └── prompts/                  # LLM Prompt 模板
│       ├── summarizer.txt
│       ├── entity.txt
│       ├── relation.txt
│       ├── insight.txt
│       └── repair.txt
├── tests/
│   ├── unit/                     # 单元测试
│   │   ├── test_schemas.py
│   │   ├── test_agents.py
│   │   ├── test_storage.py
│   │   ├── test_config.py
│   │   ├── test_confidence.py
│   │   └── test_llm.py
│   └── integration/              # 集成测试
│       └── test_pipeline.py
├── data/                        # 数据目录
│   ├── md/                      # Markdown 输出
│   ├── graph/                   # JSON Graph
│   ├── skills/                  # Skills 文件
│   └── vectors/                 # Vector Embeddings
└── pyproject.toml              # 项目配置
```

## 快速开始

### 安装

```bash
cd knowledge-os
pip install -e ".[dev]"
```

### 运行

```bash
# 处理单个 URL
python -m app.main --url "https://example.com"

# 输出 JSON 格式
python -m app.main --url "https://example.com" --json

# 处理文件中的多个 URL
python -m app.main --file urls.txt
```

### 配置

编辑 `app/config.yaml`:

```yaml
model:
  summarizer: "gpt-4o-mini"
  extractor: "gpt-4o"
  embedding: "text-embedding-3-small"

pipeline:
  max_tokens: 8000
  retry_limit: 3

confidence:
  threshold: 0.7
  low_confidence_action: "human_review"

storage:
  markdown_path: "./data/md"
  graph_path: "./data/graph"
  skills_path: "./data/skills"
```

## 输出示例

### Knowledge 对象

```json
{
  "id": "abc123",
  "title": "Machine Learning Basics",
  "summary": "An introduction to machine learning fundamentals...",
  "entities": [
    {"name": "Neural Network", "type": "technology", "confidence": 0.9},
    {"name": "Backpropagation", "type": "method", "confidence": 0.85}
  ],
  "relations": [
    {"source": "Neural Network", "target": "Backpropagation", "type": "uses", "confidence": 0.8}
  ],
  "insights": [
    {"text": "Deep learning has revolutionized computer vision", "insight_type": "implication", "confidence": 0.75}
  ],
  "tags": ["machine-learning", "neural-networks"]
}
```

### Skill 格式

```json
{
  "name": "knowledge-machine-learning",
  "version": "1.0.0",
  "description": "Provides knowledge about Machine Learning...",
  "category": "knowledge",
  "actions": [
    {"step": 1, "description": "Recall relevant information"},
    {"step": 2, "description": "Identify key entities"}
  ],
  "context_refs": ["knowledge:abc123"]
}
```

## 测试

```bash
# 运行所有测试
python -m pytest tests/ -v

# 运行单元测试
python -m pytest tests/unit/ -v

# 运行集成测试
python -m pytest tests/integration/ -v

# 带覆盖率
python -m pytest tests/ --cov=app --cov-report=html
```

## 设计原则

1. **模块化**: 每个 Agent 独立，可单独测试
2. **可扩展**: 插件式存储和输出适配器
3. **自修复**: Validation + LLM Repair 自动处理数据质量问题
4. **最小人工介入**: 仅在低置信度时触发人工审核
5. **配置驱动**: 单一 YAML 配置文件

## 技术栈

- **Python 3.11+**
- **Pydantic**: 数据验证
- **httpx**: 异步 HTTP 客户端
- **BeautifulSoup4**: HTML 解析
- **ChromaDB**: 向量存储
- **pytest**: 测试框架

## 扩展开发

### 添加新 Agent

```python
from app.agents.base import BaseAgent
from app.orchestrator.state import PipelineState

class NewAgent(BaseAgent):
    async def run(self, state: PipelineState) -> PipelineState:
        # 实现逻辑
        state["new_field"] = value
        return state
```

### 添加新存储适配器

```python
from app.storage.base import BaseStorage

class NewStorage(BaseStorage):
    async def save(self, knowledge: Knowledge) -> None:
        # 实现存储逻辑
        pass
```

## License

MIT
