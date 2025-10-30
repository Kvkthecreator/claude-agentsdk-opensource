# YARNNN Agents

**Governed autonomous agents powered by Claude Agent SDK and YARNNN substrate**

Build AI agents that operate autonomously for days or weeks with human governance, not micromanagement. This reference implementation demonstrates how to combine Claude's capabilities with YARNNN's governed substrate for long-term agent memory and work management.

## Why YARNNN + Claude Agents?

Traditional agents struggle with:
- **Memory fragmentation**: Lost context across sessions
- **Trust issues**: No governance for autonomous operations
- **Work visibility**: Can't track what agents are doing
- **Knowledge evolution**: Static RAG with no learning

YARNNN Agents solve this by providing:
- **Governed substrate**: Human-approved knowledge that agents build on
- **Dual-layer memory**: Claude handles fast (session/working), YARNNN handles deep (long-term/governed)
- **Work management**: Proposal-based changes with review workflows
- **Auditability**: Complete timeline of agent operations

## Architecture

```
┌─────────────────────────────────────────┐
│   Your Agent (Knowledge/Content/Code)    │
│                                          │
│   ├─ Claude SDK (reasoning + tools)     │
│   ├─ YARNNN Client (memory + governance)│
│   └─ Computer Use (execution - optional) │
└─────────────────────────────────────────┘
           ↓                   ↓
    ┌──────────┐        ┌──────────────┐
    │  Claude  │        │   YARNNN     │
    │  (Fast)  │        │  (Deep)      │
    │          │        │              │
    │ Session  │        │ Governed     │
    │ Working  │        │ Long-term    │
    └──────────┘        └──────────────┘
```

**Memory Layer Separation:**
- **Claude's built-in memory**: Session continuity, working context (seconds-hours)
- **YARNNN substrate**: Long-term governed knowledge (days-weeks-months)

**Work Management:**
1. Agent queries YARNNN for relevant context
2. Claude reasons and proposes changes
3. Human reviews proposals in YARNNN UI
4. Agent executes approved work
5. Results committed to substrate

## Quick Start

### Prerequisites

- Python 3.10+
- Docker & Docker Compose (for local YARNNN instance)
- Anthropic API key
- YARNNN instance (local or hosted)

### Installation

```bash
# Clone the repository
git clone https://github.com/Kvkthecreator/claude-agentsdk-yarnn.git
cd claude-agentsdk-yarnn

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your API keys
```

### Run Your First Agent

```python
from yarnnn_agents import KnowledgeAgent

# Initialize agent with YARNNN basket
agent = KnowledgeAgent(
    basket_id="your-basket-id",
    anthropic_api_key="your-key",
    yarnnn_api_url="http://localhost:3000"
)

# Agent operates autonomously
result = await agent.execute(
    "Research AI governance frameworks and add findings to memory"
)

# Agent will:
# 1. Query existing knowledge from YARNNN
# 2. Research and synthesize new information
# 3. Propose changes to substrate
# 4. Wait for your approval in YARNNN UI
# 5. Execute and commit approved work
```

## Examples

### Knowledge Agent
Autonomous research and knowledge accumulation:
- Queries web, documents, and existing substrate
- Synthesizes information into building blocks
- Proposes additions with confidence scoring
- Builds connected knowledge graphs

**See:** `examples/knowledge-agent/`

### Content Agent (Coming Soon)
Content creation with brand memory:
- Uses substrate for brand voice and guidelines
- Generates content aligned with history
- Proposes drafts for review
- Publishes approved content

### Code Agent (Coming Soon)
Code analysis and generation with codebase memory:
- Analyzes patterns across your projects
- Proposes refactorings based on standards
- Generates code following learned patterns

## Project Structure

```
claude-agentsdk-yarnn/
├── yarnnn_agents/           # Core framework
│   ├── base.py             # BaseAgent class
│   ├── memory.py           # Memory layer tools
│   ├── governance.py       # Governance layer tools
│   └── execution.py        # Execution layer tools (future)
├── integrations/
│   └── yarnnn/             # YARNNN client
│       ├── client.py       # API/MCP client
│       └── tools.py        # Claude tools for YARNNN
├── examples/
│   ├── knowledge-agent/    # Research & accumulation
│   ├── content-agent/      # Content creation
│   └── code-agent/         # Code analysis
├── docs/
│   ├── getting-started.md  # Setup guide
│   ├── architecture.md     # System design
│   └── creating-agents.md  # Build your own
├── tests/
└── docker-compose.yml      # Local development
```

## Configuration

### Environment Variables

```bash
# Anthropic
ANTHROPIC_API_KEY=sk-ant-...

# YARNNN
YARNNN_API_URL=http://localhost:3000  # or your hosted instance
YARNNN_API_KEY=your_yarnnn_api_key
YARNNN_WORKSPACE_ID=your_workspace_id

# Agent Behavior
AGENT_AUTO_APPROVE=false  # Require human approval (recommended)
AGENT_CONFIDENCE_THRESHOLD=0.8  # Auto-approve above this score
```

### Local Development with Docker

```bash
# Start YARNNN locally
docker-compose up -d

# Your YARNNN instance will be available at http://localhost:3000
# Create a workspace and basket, then use the IDs in your agent config
```

## How It Works

### 1. Dual-Layer Memory

**Claude's Layer (Fast):**
- Session continuity across turns
- Working context for reasoning
- Tool use and function calling
- Milliseconds latency

**YARNNN's Layer (Deep):**
- Long-term governed knowledge
- Versioned building blocks
- Semantic relationships
- Change proposals and approval
- 2-30s write latency (acceptable for durability)

### 2. Governance Workflow

```
Agent Proposes Change
        ↓
Validation Report Generated
        ↓
Human Reviews in YARNNN UI
        ↓
    Approve? ──→ Yes ──→ Committed to Substrate
        ↓                         ↓
       No                  Agent Continues
        ↓                         ↓
    Rejected              Timeline Recorded
```

### 3. Memory Query Patterns

Agents query YARNNN substrate using semantic search:

```python
# Get relevant context for agent reasoning
context = await agent.query_memory(
    query="What do we know about AI governance?",
    limit=20,
    filters={"anchor": "AI Ethics"}
)

# Claude uses this context for reasoning
response = await agent.claude.messages.create(
    model="claude-3-5-sonnet-20241022",
    messages=[{
        "role": "user",
        "content": f"Context: {context}\n\nTask: {user_intent}"
    }]
)
```

## YARNNN Setup

This framework requires a YARNNN instance. You can:

1. **Run locally** with Docker (see `docker-compose.yml`)
2. **Deploy your own** following [YARNNN docs](https://github.com/Kvkthecreator/rightnow-agent-app-fullstack)
3. **Use hosted** (coming soon)

### Key YARNNN Concepts

- **Basket**: Container for related knowledge (project, topic, domain)
- **Building Blocks**: Units of knowledge (insights, concepts, themes)
- **Substrate**: The governed memory layer agents build on
- **Proposals**: Change requests that require human approval
- **Timeline**: Audit trail of all agent operations

See [YARNNN documentation](https://github.com/Kvkthecreator/rightnow-agent-app-fullstack/tree/main/docs) for detailed architecture.

## Contributing

This is a reference implementation to demonstrate YARNNN + Claude Agents integration. Contributions welcome:

- **New agent types**: Content, code, research, coordination
- **Integration improvements**: Better MCP support, streaming, etc.
- **Documentation**: Tutorials, guides, examples
- **Testing**: Test coverage for core framework

## Roadmap

### Phase 1: Foundation (Weeks 1-2)
- [x] Repository structure
- [ ] BaseAgent framework
- [ ] YARNNN client (API + MCP)
- [ ] Knowledge Agent example

### Phase 2: Memory Validation (Weeks 3-4)
- [ ] Memory layer testing
- [ ] Quality metrics (does substrate improve agent output?)
- [ ] Performance benchmarks

### Phase 3: Work Management (Weeks 5-6)
- [ ] Governance workflow testing
- [ ] Proposal UI integration
- [ ] Trust metrics (does governance enable autonomy?)

### Phase 4: Execution Layer (Weeks 7-8)
- [ ] Computer Use integration
- [ ] Multi-step workflows
- [ ] Error handling and recovery

### Phase 5: Production Ready (Weeks 9-10)
- [ ] Complete loop dogfooding
- [ ] Production deployment guides
- [ ] Performance optimization

### Phase 6: Launch (Weeks 11-12)
- [ ] Open source announcement
- [ ] Community building
- [ ] Example agent gallery

## Philosophy

**Human-as-Governor, Not Micromanager:**

Traditional agents require constant oversight. YARNNN Agents shift the model:
- Agents operate autonomously within governed substrate
- Humans review proposals, not every action
- Trust builds through auditability and governance
- Knowledge evolves through human-approved changes

**Memory Types Matter:**

Not all memory is equal. This framework recognizes:
- **Working memory**: LLM context (ephemeral)
- **Session memory**: Conversation continuity (TTL hours)
- **Long-term memory**: Governed substrate (durable)
- **Organizational memory**: Versioned, evolving knowledge

**Governance Enables Trust:**

Autonomous agents need:
- Visibility (what are they doing?)
- Auditability (what did they change?)
- Control (approve/reject proposals)
- Evolution (learn from approved changes)

YARNNN provides the infrastructure for governed autonomous operation.

## License

MIT License - see [LICENSE](LICENSE) file

## Learn More

- **YARNNN Core**: [github.com/Kvkthecreator/rightnow-agent-app-fullstack](https://github.com/Kvkthecreator/rightnow-agent-app-fullstack)
- **Claude Agent SDK**: [docs.anthropic.com/agent-sdk](https://docs.anthropic.com)
- **Documentation**: [docs/](./docs/)
- **Examples**: [examples/](./examples/)

---

**Built with Claude Agent SDK + YARNNN Substrate**
*Governed autonomous agents for long-term operation*
