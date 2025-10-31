# Architecture Overview

**Claude Agent SDK - Generic Framework for Autonomous Agents**

The Claude Agent SDK provides a clean, extensible architecture for building autonomous agents with pluggable integrations.

## Core Philosophy

This is a **generic framework**, not a YARNNN-specific tool. YARNNN is just one of many possible integrations.

### Key Principles

1. **Provider-Agnostic**: Works with any memory/governance/task provider
2. **Agent Identity**: Persistent agents with multiple sessions over time
3. **Dependency Injection**: Providers are injected, not hardcoded
4. **Optional Components**: Use only the providers you need
5. **Extensible**: Easy to add new integrations

## High-Level Architecture

```
┌─────────────────────────────────────────┐
│      Your Custom Agent                  │
│   (KnowledgeAgent, ContentAgent, etc.)  │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│       BaseAgent (Generic Core)          │
│  • Agent identity & sessions            │
│  • Claude integration                   │
│  • Provider orchestration               │
└─────────────────────────────────────────┘
                  ↓
┌──────────────┬─────────────┬────────────┐
│ Memory       │ Governance  │ Tasks      │
│ Provider     │ Provider    │ Provider   │
│ (Abstract)   │ (Abstract)  │ (Abstract) │
└──────────────┴─────────────┴────────────┘
                  ↓
┌─────────────────────────────────────────┐
│      Pluggable Integrations             │
│  • YARNNN (memory + governance)         │
│  • Notion (memory)                      │
│  • GitHub (tasks)                       │
│  • Custom (your service)                │
└─────────────────────────────────────────┘
```

## Core Components

### 1. BaseAgent (`claude_agent_sdk/base.py`)

Generic foundation for all agents. Completely provider-agnostic.

**Key Features:**
- Agent identity management (persistent `agent_id`)
- Session creation and tracking
- Claude API integration
- Provider orchestration
- Error handling and retry logic

**Usage:**
```python
from claude_agent_sdk import BaseAgent

class MyAgent(BaseAgent):
    async def execute(self, task: str):
        # Your agent logic
        pass

agent = MyAgent(
    agent_id="my_bot_001",
    memory=MemoryProvider(...),
    anthropic_api_key="sk-ant-..."
)
```

### 2. Provider Interfaces (`claude_agent_sdk/interfaces.py`)

Abstract base classes defining contracts for integrations:

- **MemoryProvider**: Long-term memory (query, get_all, summarize)
- **GovernanceProvider**: Approval workflows (propose, wait_for_approval)
- **TaskProvider**: Task management (get_pending_tasks, update_status)

**Usage:**
```python
from claude_agent_sdk.interfaces import MemoryProvider

class MyMemory(MemoryProvider):
    async def query(self, query, filters, limit):
        # Your implementation
        pass
```

### 3. Session Management (`claude_agent_sdk/session.py`)

Tracks agent execution with full context:

- Session ID and agent ID
- Claude conversation ID (for resumption)
- Tasks completed, proposals created
- Error tracking
- Metadata

**Agent vs Session:**
- **Agent** = Persistent entity (e.g., "Research Bot")
- **Session** = Each execution instance

```
Agent: research_bot_001
  ├─ Session 1 (Monday): 3 tasks, 2 proposals
  ├─ Session 2 (Tuesday): 5 tasks, 1 proposal
  └─ Session 3 (Wednesday): 2 tasks, 0 proposals
```

### 4. Integrations (`claude_agent_sdk/integrations/`)

Pluggable implementations of provider interfaces.

#### YARNNN Integration

**Location:** `claude_agent_sdk/integrations/yarnnn/`

Provides governed long-term memory:

```python
from claude_agent_sdk.integrations.yarnnn import YarnnnMemory, YarnnnGovernance

memory = YarnnnMemory(basket_id="basket_123")
governance = YarnnnGovernance(basket_id="basket_123")

agent = MyAgent(memory=memory, governance=governance)
```

**Components:**
- `client.py`: HTTP client for YARNNN API
- `memory.py`: Implements MemoryProvider
- `governance.py`: Implements GovernanceProvider
- `tools.py`: Claude tools for YARNNN

## Execution Flow

```
1. User calls agent.execute("task")
   ↓
2. BaseAgent creates/resumes session
   ↓
3. Agent.execute() implementation:
   ├─ Query memory (if available)
   ├─ Reason with Claude
   ├─ Propose changes (if governance available)
   └─ Return result
   ↓
4. Session tracks:
   ├─ Tasks completed
   ├─ Proposals created
   └─ Errors (if any)
   ↓
5. Result returned to user
```

## Design Patterns

### 1. Dependency Injection

```python
# Providers injected, not hardcoded
memory = YarnnnMemory(...)
agent = MyAgent(memory=memory)  # ✅ Flexible

# NOT hardcoded
class MyAgent(BaseAgent):
    def __init__(self):
        self.memory = YarnnnMemory(...)  # ❌ Tight coupling
```

### 2. Optional Providers

```python
# Memory only (read-only agent)
agent = MyAgent(memory=YarnnnMemory(...), governance=None)

# Governance only (stateless approval agent)
agent = MyAgent(memory=None, governance=YarnnnGovernance(...))

# All providers
agent = MyAgent(
    memory=YarnnnMemory(...),
    governance=YarnnnGovernance(...),
    tasks=TaskProvider(...)
)
```

### 3. Multiple Agents

```python
# Agent 1: Research
research_agent = KnowledgeAgent(
    agent_id="research_bot",
    memory=shared_memory
)

# Agent 2: Content
content_agent = ContentAgent(
    agent_id="content_bot",
    memory=shared_memory  # Same memory!
)

# Agents can collaborate via shared memory
await research_agent.execute("Research AI trends")
await content_agent.execute("Write blog about AI trends")
```

## Data Models

All data models use Pydantic for type safety:

- **Context**: Memory query results
- **Change**: Proposed modifications
- **Proposal**: Governance proposals
- **Task**: Work items for agents
- **AgentSession**: Session metadata

## Extension Points

### Create Custom Agents

```python
from claude_agent_sdk import BaseAgent

class CustomAgent(BaseAgent):
    async def execute(self, task: str):
        # Your logic here
        pass
```

### Create Custom Providers

```python
from claude_agent_sdk.interfaces import MemoryProvider

class NotionMemory(MemoryProvider):
    async def query(self, query, filters, limit):
        # Your Notion integration
        pass
```

## Security

- API keys stored in environment variables
- Proposal-based governance (changes require approval)
- Provider isolation (errors don't cascade)
- Complete audit trail via session tracking

## Performance

- Async I/O throughout (non-blocking)
- Provider-level caching
- Efficient resource utilization
- Session persistence for recovery

## Further Reading

- **Quick Start**: [docs/QUICK_START.md](./QUICK_START.md)
- **Migration Guide**: [MIGRATION.md](../MIGRATION.md)
- **Examples**: [examples/](../examples/)
- **YARNNN Integration**: Documentation coming soon

---

For detailed technical architecture, see the old documentation: [architecture_old.md](./architecture_old.md)
