# Claude Agent SDK

**Generic framework for building autonomous AI agents with pluggable integrations**

> 🔌 **Truly Generic**: Use in-memory storage, YARNNN, Notion, or build your own providers.
> No vendor lock-in. Works standalone or with any backend.

Build agents that can work for extended periods (days, weeks) with long-term memory, governance workflows, and seamless integration with external services. This SDK provides a clean, extensible architecture for creating production-ready autonomous agents.

## Why Claude Agent SDK?

Traditional agents struggle with:
- **No long-term memory**: Context lost across sessions
- **No governance**: Can't trust agents for autonomous operation
- **Vendor lock-in**: Tied to specific memory/storage providers
- **Poor extensibility**: Hard to add new integrations

Claude Agent SDK solves this by providing:
- **Generic architecture**: Build once, plug in any provider (YARNNN, Notion, GitHub, etc.)
- **Agent identity**: Persistent agents with multiple sessions over time
- **Session management**: Resume conversations, track work across sessions
- **Provider interfaces**: MemoryProvider, GovernanceProvider, TaskProvider
- **Production-ready**: Type safety, async/await, error handling, logging

## Architecture

```
┌─────────────────────────────────────────────────┐
│         Your Custom Agent                       │
│    (KnowledgeAgent, ContentAgent, etc.)        │
└─────────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────┐
│              BaseAgent (Generic)                │
│  • Agent identity & sessions                    │
│  • Claude integration                           │
│  • Provider orchestration                       │
└─────────────────────────────────────────────────┘
                     ↓
┌──────────────────────┬──────────────────────────┐
│   MemoryProvider     │   GovernanceProvider     │
│   (Abstract)         │   (Abstract)             │
└──────────────────────┴──────────────────────────┘
                     ↓
┌──────────────────────────────────────────────────┐
│          Pluggable Integrations                  │
│                                                   │
│  ┌──────────┐  ┌───────────┐  ┌─────────────┐  │
│  │ YARNNN   │  │  Notion   │  │   GitHub    │  │
│  │ (Memory  │  │ (Memory)  │  │   (Tasks)   │  │
│  │  + Gov)  │  │           │  │             │  │
│  └──────────┘  └───────────┘  └─────────────┘  │
└──────────────────────────────────────────────────┘
```

### Key Concepts

**Agent** = Persistent conceptual entity (e.g., "Research Bot")
**Session** = Each time the agent runs (tracks work, proposals, errors)
**Provider** = Pluggable integration (memory, governance, tasks)

```python
# One agent, multiple sessions over time
Workspace
  └─ Agent: "Research Bot" (agent_id: research_bot_001)
      ├─ Session 1: Monday research
      ├─ Session 2: Tuesday research
      └─ Session 3: Wednesday research
```

## Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### 1. Minimal Agent (No Backend Required)

Try the SDK immediately with in-memory storage - only needs Claude API key:

```python
from claude_agent_sdk import BaseAgent
from claude_agent_sdk.integrations.memory import InMemoryProvider


class SimpleAgent(BaseAgent):
    async def execute(self, task: str, **kwargs):
        # Start session
        if not self.current_session:
            self.current_session = self._start_session()

        # Query memory
        contexts = await self.memory.query(task, limit=5)
        context_str = "\n".join([c.content for c in contexts])

        # Reason with Claude
        response = await self.reason(task, context=context_str)

        return response


# Create agent with in-memory provider
memory = InMemoryProvider()
memory.add("Python is a high-level programming language")
memory.add("Rust focuses on safety and performance")

agent = SimpleAgent(
    agent_id="demo_agent",
    memory=memory,
    anthropic_api_key="sk-ant-..."
)

# Execute
result = await agent.execute("Tell me about Python")
```

**Try it now**: `python examples/00_minimal_agent.py`

### 2. With Persistent Memory (YARNNN)

For production use with durable memory and governance:

```python
from claude_agent_sdk import BaseAgent
from claude_agent_sdk.integrations.yarnnn import YarnnnMemory, YarnnnGovernance


class MyAgent(BaseAgent):
    async def execute(self, task: str, **kwargs):
        # Same implementation as above
        pass


# YARNNN providers for persistent storage
memory = YarnnnMemory(
    basket_id="basket_123",
    api_key="ynk_...",
    workspace_id="ws_123"
)

governance = YarnnnGovernance(
    basket_id="basket_123",
    api_key="ynk_...",
    workspace_id="ws_123"
)

agent = MyAgent(
    agent_id="production_agent",
    memory=memory,
    governance=governance,
    anthropic_api_key="sk-ant-..."
)

result = await agent.execute("Research AI governance")
```

**Try it**: `python examples/01_with_yarnnn.py`

### 3. Build Your Own Provider

Create custom providers for your backend:

```python
from claude_agent_sdk.interfaces import MemoryProvider, Context


class MyCustomProvider(MemoryProvider):
    async def query(self, query: str, **kwargs) -> List[Context]:
        # Connect to your database, API, or service
        results = await my_backend.search(query)
        return [Context(content=r.text, metadata=r.meta) for r in results]

    async def store(self, context: Context) -> str:
        return await my_backend.save(context)


# Use your custom provider
agent = MyAgent(
    agent_id="custom_agent",
    memory=MyCustomProvider(),
    anthropic_api_key="sk-ant-..."
)
```

**Learn more**: [Building Providers Guide](docs/BUILDING_PROVIDERS.md)

## Agent Archetypes

The SDK includes three production-ready agent archetypes with specialized subagents:

### ResearchAgent
Continuous monitoring and deep-dive research capabilities.

```python
from claude_agent_sdk.archetypes import ResearchAgent

agent = ResearchAgent(
    memory=memory_provider,
    anthropic_api_key="sk-ant-...",
    monitoring_domains=["competitors", "market_trends"],
    monitoring_frequency="daily"
)

# Continuous monitoring
await agent.monitor()

# Deep dive research
result = await agent.deep_dive("AI agent market landscape")
```

**Subagents**: web_monitor, competitor_tracker, social_listener, analyst

### ContentCreatorAgent
Multi-platform content creation with brand voice consistency.

```python
from claude_agent_sdk.archetypes import ContentCreatorAgent

agent = ContentCreatorAgent(
    memory=memory_provider,
    anthropic_api_key="sk-ant-...",
    enabled_platforms=["twitter", "linkedin", "blog"]
)

# Create platform-specific content
result = await agent.create(
    platform="twitter",
    topic="AI agent trends",
    content_type="thread"
)

# Repurpose content across platforms
result = await agent.repurpose(
    source_content="My latest blog post...",
    target_platforms=["twitter", "linkedin"]
)
```

**Subagents**: twitter_writer, linkedin_writer, blog_writer, instagram_creator, repurposer

### ReportingAgent
Professional document generation with template learning.

```python
from claude_agent_sdk.archetypes import ReportingAgent

agent = ReportingAgent(
    memory=memory_provider,
    anthropic_api_key="sk-ant-...",
    template_library={"excel": "path/to/template.xlsx"},
    default_formats=["pdf", "xlsx"]
)

# Generate reports
result = await agent.generate(
    report_type="monthly_metrics",
    format="xlsx",
    data=metrics_data
)
```

**Subagents**: excel_specialist, presentation_designer, report_writer, data_analyst

**See**: `examples/02_research_agent.py` for complete archetype usage.

## Features

### 1. Agent Identity & Sessions

Each agent has a persistent identity and creates sessions for each execution:

```python
# Create agent with identity
agent = MyAgent(
    agent_id="research_bot_001",  # Persistent
    agent_name="Research Assistant",
    memory=memory,
    anthropic_api_key="sk-ant-..."
)

# Execute creates a session
result = await agent.execute("Research AI governance")
print(result["session_id"])  # e.g., "session_abc123"

# Resume session later
agent_resumed = MyAgent(
    agent_id="research_bot_001",  # Same agent!
    claude_session_id=result["claude_session_id"],
    memory=memory,
    anthropic_api_key="sk-ant-..."
)

await agent_resumed.execute(
    "Continue the AI governance research",
    resume_session=True
)
```

### 2. Multiple Agents

Run multiple agents simultaneously, each with their own identity:

```python
# Research agent
research_agent = KnowledgeAgent(
    agent_id="research_specialist",
    memory=shared_memory,
    anthropic_api_key="sk-ant-..."
)

# Content agent
content_agent = ContentAgent(
    agent_id="content_writer",
    memory=shared_memory,  # Can share memory!
    anthropic_api_key="sk-ant-..."
)

# Run independently or coordinated
await research_agent.execute("Research AI trends")
await content_agent.execute("Write blog about AI trends")
```

### 3. Pluggable Providers

Swap providers without changing agent code:

```python
# YARNNN provider
memory = YarnnnMemory(basket_id="basket_123")

# Future: Notion provider
# memory = NotionMemory(database_id="db_456")

# Future: Vector store provider
# memory = PineconeMemory(index_name="knowledge")

# Agent works with any provider!
agent = MyAgent(memory=memory, ...)
```

### 4. Optional Providers

Not all agents need all providers:

```python
# Read-only agent (memory only, no governance)
readonly_agent = MyAgent(
    memory=memory,
    governance=None,  # No governance
    anthropic_api_key="sk-ant-..."
)

# Task-based agent (tasks only, no memory)
task_agent = MyAgent(
    tasks=task_provider,
    memory=None,
    governance=None,
    anthropic_api_key="sk-ant-..."
)
```

## Provider Interfaces

The SDK defines three abstract provider interfaces:

### MemoryProvider

```python
class MemoryProvider(ABC):
    @abstractmethod
    async def query(self, query: str, filters: dict, limit: int) -> List[Context]:
        """Semantic search for context"""

    @abstractmethod
    async def get_all(self, filters: dict, limit: int) -> List[Context]:
        """Get all items with optional filtering"""

    async def summarize(self) -> Dict[str, Any]:
        """Get summary statistics"""
```

### GovernanceProvider

```python
class GovernanceProvider(ABC):
    @abstractmethod
    async def propose(self, changes: List[Change], confidence: float, reasoning: str) -> Proposal:
        """Create governance proposal"""

    @abstractmethod
    async def get_proposal_status(self, proposal_id: str) -> Proposal:
        """Check proposal status"""

    @abstractmethod
    async def wait_for_approval(self, proposal_id: str, timeout: int) -> bool:
        """Wait for human approval"""
```

### TaskProvider

```python
class TaskProvider(ABC):
    @abstractmethod
    async def get_pending_tasks(self, agent_id: str, limit: int) -> List[Task]:
        """Get tasks for agent"""

    @abstractmethod
    async def update_task_status(self, task_id: str, status: str, result: Any) -> Task:
        """Update task status"""

    @abstractmethod
    async def create_task(self, agent_id: str, description: str) -> Task:
        """Create new task"""
```

## Available Providers

### InMemory (Included)

Simple in-memory storage - no external dependencies:

```python
from claude_agent_sdk.integrations.memory import InMemoryProvider

memory = InMemoryProvider()
memory.add("Your knowledge here")
memory.add("More context", metadata={"topic": "AI"})

# Query
results = await memory.query("AI context")
```

**Perfect for**: Prototyping, demos, testing, learning the SDK

### YARNNN (Included)

Governed long-term memory with human approval workflows:

```python
from claude_agent_sdk.integrations.yarnnn import YarnnnMemory, YarnnnGovernance

memory = YarnnnMemory(
    basket_id="basket_123",
    api_url="https://yarnnn.example.com",
    api_key="ynk_...",
    workspace_id="ws_123"
)

governance = YarnnnGovernance(
    basket_id="basket_123",
    api_url="https://yarnnn.example.com",
    api_key="ynk_...",
    workspace_id="ws_123"
)
```

**Perfect for**: Production agents, durable memory, governed operations

See [YARNNN Integration Guide](./docs/integrations/yarnnn.md) for details.

### Build Your Own

Create providers for any backend - see [Building Providers Guide](docs/BUILDING_PROVIDERS.md):

- **Notion**: Database-based memory
- **GitHub**: Repository-based tasks
- **PostgreSQL**: Database with pgvector
- **Pinecone/Weaviate**: Vector stores
- **File System**: JSON file storage
- **Any API**: Custom integration

## Example Agents

### Knowledge Agent

Specialized for research and knowledge accumulation:

```python
from examples.knowledge_agent.agent_v2 import KnowledgeAgent

agent = KnowledgeAgent(
    agent_id="research_bot",
    memory=YarnnnMemory(basket_id="research"),
    governance=YarnnnGovernance(basket_id="research"),
    anthropic_api_key="sk-ant-..."
)

result = await agent.execute("Research AI governance frameworks")
```

See `examples/knowledge-agent/` for full implementation.

### Content Agent (Coming Soon)

Content creation with brand memory and approval workflows.

### Code Agent (Coming Soon)

Code analysis and generation with codebase memory.

## Project Structure

```
claude-agent-sdk/
├── claude_agent_sdk/           # Core SDK (generic)
│   ├── __init__.py
│   ├── base.py                 # BaseAgent
│   ├── interfaces.py           # Provider interfaces
│   ├── session.py              # Session management
│   └── integrations/           # Provider implementations
│       ├── memory/             # In-memory provider
│       │   ├── __init__.py
│       │   └── simple.py       # InMemoryProvider
│       └── yarnnn/             # YARNNN integration
│           ├── client.py       # HTTP client
│           ├── memory.py       # MemoryProvider impl
│           ├── governance.py   # GovernanceProvider impl
│           └── tools.py        # Claude tools
├── examples/                    # Example agents
│   ├── 00_minimal_agent.py     # No backend required
│   ├── 01_with_yarnnn.py       # YARNNN integration examples
│   └── knowledge-agent/        # Full knowledge agent
├── docs/                        # Documentation
│   ├── architecture.md
│   ├── BUILDING_PROVIDERS.md   # Create custom providers
│   ├── session-linking.md      # Work management integration
│   └── QUICK_START.md
└── README.md
```

## Configuration

### Environment Variables

```bash
# Anthropic (required)
ANTHROPIC_API_KEY=sk-ant-...

# YARNNN (if using YARNNN integration)
YARNNN_API_URL=https://yarnnn.example.com
YARNNN_API_KEY=ynk_...
YARNNN_WORKSPACE_ID=ws_...
YARNNN_BASKET_ID=basket_...  # Optional, can specify per agent

# Agent Behavior
AGENT_AUTO_APPROVE=false  # Auto-approve high-confidence proposals
AGENT_CONFIDENCE_THRESHOLD=0.8  # Threshold for auto-approval

# Logging
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
```

## Creating Custom Agents

```python
from claude_agent_sdk import BaseAgent
from claude_agent_sdk.interfaces import MemoryProvider, GovernanceProvider

class MyCustomAgent(BaseAgent):
    """Custom agent with specialized behavior"""

    def __init__(
        self,
        agent_id: str,
        memory: MemoryProvider,
        governance: GovernanceProvider,
        anthropic_api_key: str,
        # Add custom parameters
        custom_setting: str = "default"
    ):
        super().__init__(
            agent_id=agent_id,
            agent_type="custom",
            memory=memory,
            governance=governance,
            anthropic_api_key=anthropic_api_key
        )

        self.custom_setting = custom_setting

    async def execute(self, task: str):
        """Implement custom execution logic"""

        # 1. Query memory if available
        if self.memory:
            contexts = await self.memory.query(task)
            context_str = "\\n".join([c.content for c in contexts])
        else:
            context_str = ""

        # 2. Reason with Claude
        response = await self.reason(
            task=task,
            context=context_str,
            system_prompt=self._get_custom_prompt()
        )

        # 3. Propose changes if needed
        if self.governance:
            # ... create proposal logic
            pass

        return response

    def _get_custom_prompt(self) -> str:
        """Custom system prompt"""
        return f"""You are a specialized agent for {self.custom_setting}..."""
```

See [Creating Custom Agents](./docs/creating-agents.md) for detailed guide.

## Creating Custom Integrations

```python
from claude_agent_sdk.interfaces import MemoryProvider, Context

class MyMemoryProvider(MemoryProvider):
    """Custom memory provider implementation"""

    async def query(self, query: str, filters: dict, limit: int) -> List[Context]:
        # Your implementation
        # Query your service (Notion, database, vector store, etc.)
        results = await self.client.search(query)

        # Convert to Context objects
        return [
            Context(
                content=result.text,
                metadata=result.metadata,
                confidence=result.score
            )
            for result in results
        ]

    async def get_all(self, filters: dict, limit: int) -> List[Context]:
        # Your implementation
        pass
```

See [Creating Integrations](./docs/creating-integrations.md) for detailed guide.

## Roadmap

### Phase 1: Foundation ✅
- [x] Generic BaseAgent architecture
- [x] Provider interfaces (Memory, Governance, Task)
- [x] Agent identity and session tracking
- [x] InMemoryProvider (no dependencies)
- [x] YARNNN integration
- [x] Knowledge Agent example
- [x] Provider building guide

### Phase 2: Additional Integrations (Weeks 3-4)
- [ ] Notion memory provider
- [ ] GitHub task provider
- [ ] Vector store memory provider (Pinecone/Weaviate)
- [ ] Slack governance provider

### Phase 3: Advanced Features (Weeks 5-6)
- [ ] Agent-to-agent communication
- [ ] Workflow orchestration
- [ ] Performance monitoring
- [ ] Cost tracking

### Phase 4: Production Ready (Weeks 7-8)
- [ ] Comprehensive testing
- [ ] Deployment guides (local, cloud, serverless)
- [ ] Production best practices
- [ ] Security hardening

### Phase 5: Community (Weeks 9-10)
- [ ] Plugin marketplace
- [ ] Community integrations
- [ ] Example agent gallery
- [ ] Video tutorials

## Contributing

We welcome contributions! Areas of interest:

- **New integrations**: Notion, GitHub, Airtable, etc.
- **New agent types**: Code agents, content agents, monitoring agents
- **Documentation**: Tutorials, guides, examples
- **Testing**: Test coverage, integration tests
- **Performance**: Optimization, caching, streaming

See [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

## Philosophy

**Generic, Not Opinionated**: This SDK provides the structure, you bring the specifics. Whether you use YARNNN, Notion, or a custom backend, the agent code stays the same.

**Agents are Workers, Not Tools**: Agents have persistent identity, learn over time, and build organizational knowledge. They're team members, not one-off scripts.

**Governance Enables Autonomy**: Human oversight through approval workflows enables true autonomous operation. Agents can work for days/weeks without constant supervision.

**Extensibility First**: Clean interfaces, dependency injection, and pluggable providers make it easy to add new capabilities without changing core code.

## License

MIT License - see [LICENSE](LICENSE) file

## Learn More

- **Documentation**: [docs/](./docs/)
- **Examples**: [examples/](./examples/)
- **YARNNN Core**: [github.com/Kvkthecreator/rightnow-agent-app-fullstack](https://github.com/Kvkthecreator/rightnow-agent-app-fullstack)
- **Claude Agent SDK**: [docs.anthropic.com](https://docs.anthropic.com)

---

**Built with Claude Agent SDK + Pluggable Integrations**
*Generic framework for autonomous agents*
