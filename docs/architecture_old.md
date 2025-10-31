# Architecture

Complete architectural overview of YARNNN Agents framework.

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    YARNNN Agents Framework                   │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │              Your Custom Agent                     │    │
│  │  (KnowledgeAgent, ContentAgent, CodeAgent, etc.)  │    │
│  └────────────────────────────────────────────────────┘    │
│                         ↓                                    │
│  ┌────────────────────────────────────────────────────┐    │
│  │                   BaseAgent                        │    │
│  │  - Autonomous operation loop                       │    │
│  │  - Tool use orchestration                          │    │
│  │  - Error handling & retry                          │    │
│  └────────────────────────────────────────────────────┘    │
│          ↓                              ↓                   │
│  ┌──────────────┐             ┌──────────────────┐         │
│  │ MemoryLayer  │             │ GovernanceLayer  │         │
│  │              │             │                  │         │
│  │ - Query      │             │ - Propose        │         │
│  │ - Retrieve   │             │ - Monitor        │         │
│  │ - Traverse   │             │ - Approve        │         │
│  └──────────────┘             └──────────────────┘         │
│          ↓                              ↓                   │
│  ┌─────────────────────────────────────────────────┐       │
│  │            YARNNN Client                        │       │
│  │  - API/MCP integration                          │       │
│  │  - Request/response handling                    │       │
│  │  - Authentication                               │       │
│  └─────────────────────────────────────────────────┘       │
└──────────────────────────────────────────────────────────┘
                         ↓
        ┌────────────────────────────────┐
        │      External Systems           │
        │                                 │
        │  ┌──────────────────────────┐  │
        │  │   Claude (Anthropic)     │  │
        │  │  - Reasoning             │  │
        │  │  - Tool calling          │  │
        │  │  - Session memory        │  │
        │  └──────────────────────────┘  │
        │             ↓                   │
        │  ┌──────────────────────────┐  │
        │  │   YARNNN Substrate       │  │
        │  │  - Long-term memory      │  │
        │  │  - Governed knowledge    │  │
        │  │  - Versioning            │  │
        │  │  - Timeline/events       │  │
        │  └──────────────────────────┘  │
        └─────────────────────────────────┘
```

## Core Components

### 1. BaseAgent

Foundation for all agents providing:

**Responsibilities:**
- Claude SDK integration for reasoning
- Tool use orchestration
- Autonomous operation loop
- Error handling and retry logic
- Logging and observability

**Key Methods:**
```python
async def execute(task: str) -> Any:
    """Execute a single task (implemented by subclass)"""

async def reason(task: str, context: str) -> Response:
    """Use Claude to reason about task with context"""

async def autonomous_loop(tasks: List[str]) -> List[Any]:
    """Execute multiple tasks autonomously"""
```

**Configuration:**
- Model selection (Claude 3.5 Sonnet by default)
- Auto-approval settings
- Confidence thresholds
- Retry limits

### 2. MemoryLayer

High-level interface to YARNNN substrate for memory operations.

**Responsibilities:**
- Semantic querying
- Context retrieval
- Anchor-based organization
- Relationship traversal (future)

**Key Methods:**
```python
async def query(query: str, limit: int) -> str:
    """Semantic search across substrate"""

async def get_anchor(anchor: str) -> str:
    """Get all knowledge under a category"""

async def get_all_blocks() -> List[Block]:
    """Get all building blocks"""

async def summarize_substrate() -> str:
    """Get high-level summary"""
```

**Memory Operations:**
- **Query**: Semantic search for relevant context
- **Retrieve**: Get specific blocks/concepts
- **Traverse**: Navigate relationships
- **Summarize**: Get overview statistics

### 3. GovernanceLayer

Interface to YARNNN governance for change management.

**Responsibilities:**
- Proposal creation
- Approval monitoring
- Auto-approval logic (if enabled)
- Change tracking

**Key Methods:**
```python
async def propose(
    blocks: List[Dict],
    context_items: List[str],
    reasoning: str,
    confidence: float
) -> Proposal:
    """Propose substrate changes"""

async def wait_for_approval(proposal_id: str) -> bool:
    """Wait for human approval"""

async def get_status(proposal_id: str) -> Dict:
    """Check proposal status"""
```

**Governance Workflow:**
1. Agent creates proposal with ops (block creates, etc.)
2. Proposal enters governance queue
3. Human reviews in YARNNN UI
4. Approve/reject decision
5. If approved, committed to substrate
6. Agent notified of outcome

### 4. YarnnnClient

Low-level client for YARNNN API/MCP integration.

**Responsibilities:**
- HTTP request/response handling
- Authentication
- Error handling
- Request retries

**Key Methods:**
```python
async def query_substrate(basket_id, query) -> List[Dict]:
    """Query substrate via API"""

async def create_proposal(basket_id, ops) -> Proposal:
    """Create governance proposal"""

async def get_proposal(proposal_id) -> Proposal:
    """Get proposal status"""

async def create_dump(basket_id, text_dump) -> Dict:
    """Create raw dump"""
```

**Integration Modes:**
- **API Mode** (default): HTTP requests to YARNNN API
- **MCP Mode** (future): Model Context Protocol integration

### 5. Claude Tools

Tool definitions for Claude to interact with YARNNN.

**Available Tools:**

**`query_memory`**
- Search substrate for relevant context
- Parameters: query, limit
- Returns: Formatted context string

**`propose_to_memory`**
- Propose substrate changes
- Parameters: blocks, context_items, reasoning, confidence
- Returns: Proposal ID and status

**`check_proposal_status`**
- Check if proposal approved
- Parameters: proposal_id
- Returns: Current status

**`get_anchor_context`**
- Get knowledge under anchor
- Parameters: anchor
- Returns: Formatted anchor knowledge

## Data Flow

### Request Flow

```
User Request
    ↓
Agent.execute(task)
    ↓
1. Query Memory
   MemoryLayer.query(task)
       ↓
   YarnnnClient.query_substrate(basket_id, query)
       ↓
   YARNNN API /api/baskets/{id}/query
       ↓
   Context returned to agent
    ↓
2. Reason with Claude
   BaseAgent.reason(task, context)
       ↓
   Claude API with tools
       ↓
   Tool use: propose_to_memory
    ↓
3. Propose Changes
   GovernanceLayer.propose(blocks, reasoning)
       ↓
   YarnnnClient.create_proposal(basket_id, ops)
       ↓
   YARNNN API /api/baskets/{id}/proposals
       ↓
   Proposal created in governance queue
    ↓
4. Wait for Approval (optional)
   GovernanceLayer.wait_for_approval(proposal_id)
       ↓
   Poll YARNNN API /api/proposals/{id}
       ↓
   Return approved/rejected status
```

### Governance Flow

```
Agent Proposes Changes
    ↓
Proposal Created (PROPOSED status)
    ↓
Appears in YARNNN UI
    - /workspace/change-requests (workspace-level)
    - /baskets/{id}/change-requests (basket-level)
    ↓
Human Reviews Proposal
    - Views ops (block creates, etc.)
    - Sees validation report
    - Checks confidence score
    - Reads reasoning
    ↓
Human Decision
    ↓           ↓
Approve      Reject
    ↓           ↓
APPROVED    REJECTED
    ↓           ↓
Commit      Archive
to Substrate
    ↓
Timeline Event Emitted
    ↓
Agent Notified
    ↓
Agent Continues
```

## Memory Architecture

### Dual-Layer Memory

**Claude's Layer (Fast):**
- Session continuity across conversation
- Working context for reasoning
- Tool use history
- Latency: Milliseconds

**YARNNN's Layer (Deep):**
- Long-term governed knowledge
- Versioned building blocks
- Semantic relationships
- Latency: 2-30 seconds (acceptable for durability)

**Why Separation?**
- Claude excels at fast reasoning with session context
- YARNNN excels at durable, governed, evolving knowledge
- Agents get best of both: fast + deep memory

### Memory Query Patterns

**1. Semantic Search**
```python
context = await agent.memory.query(
    "What do we know about AI governance?"
)
```
Uses vector embeddings to find relevant blocks.

**2. Anchor-Based Retrieval**
```python
ethics_knowledge = await agent.memory.get_anchor("AI Ethics")
```
Gets all blocks under a specific category.

**3. Concept Traversal**
```python
related = await agent.memory.find_related(
    "Machine Learning",
    depth=2
)
```
Navigates relationship graph.

**4. Substrate Summary**
```python
summary = await agent.memory.summarize_substrate()
```
High-level overview of knowledge state.

## Governance Architecture

### Proposal Structure

```typescript
{
  id: "prop-xxx",
  basket_id: "basket-123",
  status: "PROPOSED",  // DRAFT, PROPOSED, UNDER_REVIEW, APPROVED, REJECTED, COMMITTED
  ops: [
    {
      type: "block_create",
      data: {
        title: "New Insight",
        body: "Details...",
        semantic_type: "knowledge",
        confidence: 0.85
      }
    },
    {
      type: "context_item_create",
      data: {
        name: "AI Ethics",
        context_type: "concept"
      }
    }
  ],
  validation_report: {
    confidence: 0.85,
    reasoning: "Research findings from today",
    origin: "agent",
    ops_count: 2
  }
}
```

### Auto-Approval Logic

If enabled (not recommended for production):

```python
if agent.auto_approve and confidence >= agent.confidence_threshold:
    # Proposal auto-approved
    # Note: Backend support required
```

**Confidence Scoring:**
- `0.9-1.0`: Facts, established knowledge, high-quality sources
- `0.7-0.9`: Well-researched insights, reasonable confidence
- `0.5-0.7`: Preliminary findings, needs validation
- `<0.5`: Speculative, uncertain

## Security Model

### Authentication

**Agent Authentication:**
```python
YarnnnClient(
    api_url="http://yarnnn-api:3000",
    api_key="agent_key_xxx",  # Agent-specific API key
    workspace_id="workspace_123"
)
```

**Headers:**
```
Authorization: Bearer agent_key_xxx
Content-Type: application/json
```

### Authorization

**Workspace Isolation:**
- Agents scoped to specific workspace
- Can only access baskets within workspace
- RLS policies enforce boundaries

**API Key Permissions:**
- Read: Query substrate
- Write: Create proposals (not direct substrate writes)
- Governance: Submit proposals only (not approve)

### Safety Mechanisms

1. **Governance Required**: Agents can't directly modify substrate
2. **Human Approval**: Changes require human review
3. **Confidence Scoring**: Track agent certainty
4. **Auditability**: Full timeline of operations
5. **Versioning**: All changes tracked

## Scalability

### Horizontal Scaling

```yaml
# Deploy multiple agent instances
services:
  knowledge-agent-1:
    image: yarnnn-agent
    environment:
      - BASKET_ID=basket-1

  knowledge-agent-2:
    image: yarnnn-agent
    environment:
      - BASKET_ID=basket-2
```

### Performance Characteristics

**Agent Operations:**
- Query substrate: 100-500ms
- Create proposal: 200-800ms
- Wait for approval: Variable (human-dependent)

**Throughput:**
- Queries: ~10-50/second (limited by YARNNN API)
- Proposals: ~1-10/minute (governance bottleneck)

**Resource Usage:**
- Memory: ~100-500MB per agent
- CPU: Low (mostly waiting for APIs)

## Extension Points

### Custom Agents

```python
class MyCustomAgent(BaseAgent):
    def __init__(self, basket_id, **kwargs):
        super().__init__(basket_id, **kwargs)
        self.custom_config = self._load_config()

    async def execute(self, task: str):
        # Custom implementation
        pass

    def _get_default_system_prompt(self):
        return "Your custom system prompt"
```

### Custom Tools

```python
def get_custom_tools():
    return [
        {
            "name": "search_web",
            "description": "Search the web",
            "input_schema": {...},
            "function": search_web_func
        }
    ]

agent = BaseAgent(basket_id="...")
agent.yarnnn_tools.extend(get_custom_tools())
```

### Custom Memory Operations

```python
class EnhancedMemoryLayer(MemoryLayer):
    async def smart_query(self, query: str):
        # Custom query logic
        pass

agent = BaseAgent(basket_id="...")
agent.memory = EnhancedMemoryLayer(agent.yarnnn, agent.basket_id)
```

## Observability

### Logging

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Agent logs:
# - Task execution start/end
# - Memory queries
# - Proposals created
# - Approvals received
# - Errors and retries
```

### Metrics (Future)

- Agent operation latency
- Proposal approval rate
- Memory query performance
- Error rate
- Agent uptime

### Timeline Integration

All agent operations visible in YARNNN timeline:
- Query events
- Proposal events
- Approval events
- Execution events

## Future Enhancements

### Phase 1: Execution Layer
- Claude Computer Use integration
- Multi-step workflows
- Action execution & monitoring

### Phase 2: Multi-Agent Coordination
- Agent-to-agent communication
- Shared knowledge protocols
- Conflict resolution

### Phase 3: Advanced Memory
- Relationship traversal
- Temporal queries
- Memory consolidation

### Phase 4: Production Readiness
- Health checks
- Graceful shutdown
- State persistence
- Monitoring dashboards

---

**This architecture provides a foundation for governed autonomous agents that operate safely, transparently, and effectively over extended time periods.**
