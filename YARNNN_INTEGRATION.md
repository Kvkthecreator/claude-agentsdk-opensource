# YARNNN Integration Guide

**Purpose**: This document serves as a bridge between the open-source Claude Agent SDK and proprietary YARNNN service integration. It tracks governance items, pending implementations, and refactoring needed on both sides.

**Audience**:
- Continued development in this SDK session
- Copy/paste to separate YARNNN service repo session for refactoring

---

## Current Agent SDK State

### Architecture Overview

**Open Source (claude-agentsdk-yarnnn)**
- Generic agent framework with provider interfaces
- Three production-ready archetypes with subagent support
- Abstract provider interfaces (MemoryProvider, GovernanceProvider, TaskProvider)
- In-memory provider for testing/demos
- YARNNN integration as one implementation option

**Proprietary (yarnnn-production-agents - to be created)**
- Business-specific agent implementations
- Production deployment configurations
- Environment-specific settings
- YARNNN API orchestration layer

### Agent Archetypes Implemented

#### 1. ResearchAgent
**Location**: `claude_agent_sdk/archetypes/research_agent.py`

**Capabilities**:
- `monitor()` - Continuous monitoring across configured domains
- `deep_dive(topic)` - On-demand comprehensive research

**Subagents** (4):
- `web_monitor` - Website/blog monitoring
- `competitor_tracker` - Competitor activity tracking
- `social_listener` - Social media monitoring
- `analyst` - Synthesis and insights generation

**Configuration**:
```python
ResearchAgent(
    memory: MemoryProvider,
    anthropic_api_key: str,
    governance: Optional[GovernanceProvider] = None,
    monitoring_domains: Optional[List[str]] = None,
    monitoring_frequency: Literal["hourly", "daily", "weekly"] = "daily",
    signal_threshold: float = 0.7,
    synthesis_mode: Literal["summary", "detailed", "insights"] = "insights"
)
```

#### 2. ContentCreatorAgent
**Location**: `claude_agent_sdk/archetypes/content_creator.py`

**Capabilities**:
- `create(platform, topic, content_type)` - Platform-specific content creation
- `repurpose(source_content, source_platform, target_platforms)` - Cross-platform adaptation

**Subagents** (5):
- `twitter_writer` - Twitter/X posts and threads
- `linkedin_writer` - LinkedIn posts and articles
- `blog_writer` - SEO-optimized blog posts
- `instagram_creator` - Visual content with captions
- `repurposer` - Cross-platform content adaptation

**Configuration**:
```python
ContentCreatorAgent(
    memory: MemoryProvider,
    anthropic_api_key: str,
    governance: Optional[GovernanceProvider] = None,
    enabled_platforms: Optional[List[str]] = None,
    brand_voice_mode: Literal["adaptive", "strict", "creative"] = "adaptive",
    voice_temperature: float = 0.7
)
```

**Key Feature**: Voice consistency tracking via `approved_content_count`

#### 3. ReportingAgent
**Location**: `claude_agent_sdk/archetypes/reporting_agent.py`

**Capabilities**:
- `generate(report_type, format, data)` - Multi-format document generation

**Subagents** (4):
- `excel_specialist` - Spreadsheet creation with formulas/charts
- `presentation_designer` - PowerPoint presentations
- `report_writer` - Professional PDF reports
- `data_analyst` - Data analysis and insights

**Configuration**:
```python
ReportingAgent(
    memory: MemoryProvider,
    anthropic_api_key: str,
    governance: Optional[GovernanceProvider] = None,
    template_library: Optional[Dict[str, str]] = None,  # Dynamic template learning!
    brand_guidelines: Optional[Dict[str, Any]] = None,
    default_formats: Optional[List[str]] = None
)
```

**Innovation**: Dynamic template learning from user's existing documents (not hardcoded styles)

### Subagent Infrastructure

**Location**: `claude_agent_sdk/subagents.py`

**Components**:
- `SubagentDefinition` - Pydantic model for subagent configuration
- `SubagentRegistry` - Manages subagent delegation
- `create_subagent_tool()` - Claude tool definition generator

**Key Methods**:
```python
# Register subagent
registry.register(SubagentDefinition(
    name="web_monitor",
    description="Monitor websites for changes",
    system_prompt="You are a web monitoring specialist...",
    tools=["web_search", "web_fetch"],
    metadata={"type": "monitor"}
))

# Delegate to subagent
result = await registry.delegate(
    subagent_name="web_monitor",
    task="Monitor AI news sites",
    context="Previous findings: ..."
)
```

### Provider Interfaces

**Location**: `claude_agent_sdk/interfaces.py`

All providers are **optional** - agents can work with subset of capabilities.

#### MemoryProvider (Abstract)
```python
async def query(query: str, filters: dict, limit: int) -> List[Context]
async def get_all(filters: dict, limit: int) -> List[Context]
async def summarize() -> Dict[str, Any]
```

#### GovernanceProvider (Abstract)
```python
async def propose(changes: List[Change], confidence: float, reasoning: str) -> Proposal
async def get_proposal_status(proposal_id: str) -> Proposal
async def wait_for_approval(proposal_id: str, timeout: int) -> bool
```

#### TaskProvider (Abstract)
```python
async def get_pending_tasks(agent_id: str, limit: int) -> List[Task]
async def update_task_status(task_id: str, status: str, result: Any) -> Task
async def create_task(agent_id: str, description: str) -> Task
```

---

## YARNNN Integration (Current State)

**Location**: `claude_agent_sdk/integrations/yarnnn/`

### Implemented Components

#### 1. YarnnnClient (`client.py`)
HTTP client for YARNNN API interactions.

**Status**: ✅ Implemented
**Key Methods**:
- `create_basket()`, `get_basket()`, `list_baskets()`
- `create_yarn()`, `search_yarns()`, `update_yarn()`
- `create_proposal()`, `get_proposal()`, `approve_proposal()`, `reject_proposal()`

#### 2. YarnnnMemory (`memory.py`)
MemoryProvider implementation using YARNNN baskets.

**Status**: ✅ Implemented
**Key Methods**:
- `query()` - Semantic search via YARNNN search
- `get_all()` - Fetch all yarns from basket
- `store()` - Create yarn in basket
- `summarize()` - Basket statistics

#### 3. YarnnnGovernance (`governance.py`)
GovernanceProvider implementation using YARNNN proposals.

**Status**: ✅ Implemented
**Key Methods**:
- `propose()` - Create governance proposal
- `get_proposal_status()` - Check approval status
- `wait_for_approval()` - Poll with timeout
- `_store_approved_changes()` - Execute approved changes

#### 4. YARNNN Tools (`tools.py`)
Claude tool definitions for direct YARNNN operations.

**Status**: ✅ Implemented
**Tools**:
- `store_knowledge` - Direct yarn creation
- `query_knowledge` - Direct search
- `propose_changes` - Direct proposal creation
- `check_proposal_status` - Direct status check

### Configuration

**Environment Variables**:
```bash
YARNNN_API_URL=https://api.yarnnn.com
YARNNN_API_KEY=ynk_...
YARNNN_WORKSPACE_ID=ws_...
YARNNN_BASKET_ID=basket_...  # Can specify per-agent
```

**Usage**:
```python
from claude_agent_sdk.integrations.yarnnn import YarnnnMemory, YarnnnGovernance

memory = YarnnnMemory(
    basket_id="research_basket",
    api_key=os.getenv("YARNNN_API_KEY"),
    workspace_id=os.getenv("YARNNN_WORKSPACE_ID"),
    api_url=os.getenv("YARNNN_API_URL")
)

governance = YarnnnGovernance(
    basket_id="research_basket",
    api_key=os.getenv("YARNNN_API_KEY"),
    workspace_id=os.getenv("YARNNN_WORKSPACE_ID")
)
```

---

## Governance Items (Discussion Needed)

### 1. Tool Governance (`canUseTool` Pattern)

**Status**: 🔴 Not Implemented

**From Official Claude SDK (TypeScript)**:
```typescript
async canUseTool(tool: Tool): Promise<boolean> {
  // Custom approval logic before tool execution
}
```

**Question**: Should YARNNN governance include pre-tool-execution approval?

**Options**:
1. **Post-execution only** (current): Agent acts, proposes results, waits for approval
2. **Pre-execution**: Agent requests permission before each tool use
3. **Hybrid**: Pre-approval for high-risk tools, post-approval for others

**Recommendation**: Start with post-execution (current), add pre-execution hooks in Phase 2

**Action Needed**:
- User decision on governance model
- If hybrid, define which tools require pre-approval
- Implement `canUseTool()` method in BaseAgent if needed

### 2. Voice Learning Sophistication

**Status**: 🟡 Deferred

**ContentCreator** currently:
- Queries approved content from memory
- Passes examples as context to subagents
- Tracks `approved_content_count`

**Questions**:
1. Should voice learning be **supervised** (user approves/rejects) or **unsupervised** (learns from all content)?
2. Should we build voice profiles separately or rely on memory RAG?
3. How to handle multi-brand scenarios (user has multiple brand voices)?

**User's Position**: "Want on-brand quality from start, not progressive learning"

**Recommendation**: Test governance workflow first, then decide on voice learning complexity

**Action Needed**:
- Test ContentCreator with governance approval loops
- Collect user feedback on voice consistency
- Decide on voice profile storage strategy

### 3. Memory Architecture (Basket Strategy)

**Status**: 🟡 Deferred (YARNNN-specific)

**Questions**:
1. **Per-agent baskets** vs **shared baskets**?
   - Research Agent → `research_basket`
   - Content Creator → `brand_voice_basket`
   - Reporting Agent → `artifacts_basket`
   - OR all share `workspace_basket`?

2. **Per-platform baskets** for ContentCreator?
   - `twitter_content_basket`
   - `linkedin_content_basket`
   - OR unified `content_basket` with metadata filtering?

3. **Template storage** for ReportingAgent?
   - Store template references in basket metadata?
   - Separate `template_library_basket`?
   - File system + metadata only?

**Recommendation**: Start with per-agent baskets, migrate to shared if coordination needed

**Action Needed**:
- Define basket naming convention
- Document basket creation in YARNNN service
- Update agent initialization examples

### 4. Session Persistence

**Status**: 🟡 Partially Implemented

**Current**:
- Agents track `session_id` and `claude_session_id`
- Sessions stored in memory for resumption
- No cross-session context synthesis

**Questions**:
1. Should sessions be stored in YARNNN baskets?
2. How long to retain session history?
3. Should agents synthesize learnings across sessions automatically?

**Example Workflow**:
```python
# Monday
agent = ResearchAgent(...)
result = await agent.monitor()
session_1_id = result["session_id"]

# Tuesday - resume
agent = ResearchAgent(
    session_id=session_1_id,  # Resume from yesterday
    ...
)
result = await agent.monitor()
```

**Action Needed**:
- Define session storage schema for YARNNN
- Implement session query/retrieval
- Add cross-session synthesis to archetypes

### 5. Error Handling and Retries

**Status**: 🔴 Not Implemented

**Questions**:
1. What happens when YARNNN API is down?
2. Should agents retry failed proposals?
3. How to handle partial failures in monitoring (some subagents succeed, others fail)?

**Recommendation**: Add retry logic with exponential backoff

**Action Needed**:
- Add retry decorator to YARNNN client
- Define error recovery strategies per agent type
- Add graceful degradation (e.g., continue monitoring if one domain fails)

---

## Pending Implementations

### SDK Side (Open Source)

#### 1. Streaming Support
**Status**: 🔴 Not Started
**Priority**: Medium

Current implementation uses non-streaming Claude API. Add streaming for:
- Real-time progress visibility
- Long-running research tasks
- Report generation progress

**Action**:
- Add `stream=True` parameter to `reason()` method
- Implement async generators for streaming responses
- Add streaming examples

#### 2. Computer Use Tools
**Status**: 🔴 Not Started
**Priority**: Low (Phase 2)

Official Claude SDK supports computer use (bash, editor, browser). Consider adding for:
- ResearchAgent web scraping
- ReportingAgent document generation
- ContentCreator screenshot capture

**Action**:
- Evaluate computer use vs direct tools trade-off
- Add computer use support to BaseAgent if needed
- Update archetype tool configurations

#### 3. Multi-Agent Coordination
**Status**: 🔴 Not Started
**Priority**: Medium

Agents currently independent. Add coordination for:
- Research → Content pipeline (ResearchAgent findings feed ContentCreator)
- Research → Reporting pipeline (ResearchAgent data feeds ReportingAgent)
- Shared memory as coordination mechanism

**Action**:
- Design coordination patterns (message passing vs shared memory)
- Add inter-agent communication examples
- Document orchestration strategies

#### 4. Testing Coverage
**Status**: 🟡 Partial (83 tests pass)

Current tests cover core functionality. Need:
- Archetype-specific tests
- Subagent delegation tests
- YARNNN integration tests (mocked)
- End-to-end workflow tests

**Action**:
- Add `tests/test_archetypes.py`
- Add `tests/test_subagents.py`
- Add `tests/test_yarnnn_integration.py`

#### 5. Documentation
**Status**: 🟡 Partial

**Completed**:
- README with archetype examples
- Inline docstrings
- Example scripts

**Pending**:
- Archetype design patterns doc
- Subagent creation guide
- YARNNN deployment guide
- Performance tuning guide

**Action**:
- Create `docs/ARCHETYPES.md`
- Create `docs/SUBAGENTS.md`
- Create `docs/YARNNN_DEPLOYMENT.md`

### YARNNN Service Side (Proprietary)

#### 1. Production Agent Deployment

**Status**: 🔴 Not Started

**Goal**: Create `yarnnn-production-agents` repository

**Structure**:
```
yarnnn-production-agents/
├── agents/
│   ├── research/
│   │   ├── monitor.py          # Scheduled monitoring
│   │   └── config.yaml         # Domain configurations
│   ├── content/
│   │   ├── scheduler.py        # Content calendar
│   │   └── platforms.yaml      # Platform credentials
│   └── reporting/
│       ├── templates/          # User template library
│       └── schedules.yaml      # Report schedules
├── deployment/
│   ├── docker-compose.yml
│   ├── kubernetes/
│   └── serverless/
├── config/
│   ├── production.env
│   └── staging.env
└── orchestration/
    ├── scheduler.py            # APScheduler or similar
    └── task_queue.py           # Celery or similar
```

**Action**:
- Create new private repo
- Copy agent configurations from SDK
- Add deployment manifests
- Set up CI/CD

#### 2. Basket Management Service

**Status**: 🔴 Not Started

**Goal**: Automate basket creation and organization

**Features**:
- Auto-create baskets per agent on first run
- Namespace baskets per workspace/user
- Implement basket lifecycle (archive old sessions)
- Add basket access control

**Action**:
- Add basket management endpoints to YARNNN API
- Implement basket provisioning logic
- Add basket cleanup job

#### 3. Governance UI

**Status**: 🔴 Not Started

**Goal**: Human approval interface for agent proposals

**Features**:
- Proposal dashboard (pending, approved, rejected)
- Diff view for proposed changes
- One-click approve/reject
- Bulk operations
- Notification system

**Action**:
- Design governance dashboard
- Add approval workflow UI
- Integrate with YARNNN frontend

#### 4. Scheduling Service

**Status**: 🔴 Not Started

**Goal**: Automated agent execution (monitoring, reports, content)

**Examples**:
- ResearchAgent: Daily monitoring at 6am
- ContentCreator: Weekly content generation
- ReportingAgent: Monthly report generation

**Options**:
1. APScheduler (Python)
2. Celery Beat (distributed)
3. Kubernetes CronJobs
4. Cloud scheduler (AWS EventBridge, GCP Cloud Scheduler)

**Action**:
- Choose scheduling solution
- Implement agent task queue
- Add schedule configuration interface

#### 5. Agent Monitoring & Observability

**Status**: 🔴 Not Started

**Goal**: Track agent health, performance, costs

**Metrics**:
- Agent execution success/failure rates
- Claude API usage and costs
- Proposal approval rates
- Session duration
- Memory growth

**Action**:
- Add telemetry to agents
- Implement metrics collection
- Build monitoring dashboard
- Set up alerts

#### 6. Multi-Tenancy Support

**Status**: 🔴 Not Started

**Goal**: Isolated agents per workspace/user

**Requirements**:
- Workspace-scoped baskets
- User-scoped API keys
- Agent configuration per workspace
- Cost tracking per workspace

**Action**:
- Add workspace isolation to YARNNN API
- Implement user-agent associations
- Add workspace-level settings

---

## Refactoring Needed (YARNNN Service)

### 1. API Client Consolidation

**Current**: `claude_agent_sdk/integrations/yarnnn/client.py` duplicates YARNNN API logic

**Issue**: Two sources of truth for YARNNN API interactions
- Agent SDK has HTTP client
- YARNNN service has internal API

**Recommendation**:
- YARNNN service provides official Python client package
- Agent SDK depends on `yarnnn-client-python` (separate package)
- Reduces duplication, ensures API compatibility

**Action**:
- Extract `client.py` to `yarnnn-client-python` package
- Publish to PyPI (private or public)
- Update Agent SDK to depend on client package

### 2. Basket Schema Standardization

**Current**: No enforced schema for basket metadata

**Needed**:
```json
{
  "basket_id": "research_basket_001",
  "agent_id": "research_agent",
  "agent_type": "research",
  "purpose": "market_intelligence",
  "retention_days": 90,
  "auto_archive": true
}
```

**Action**:
- Define basket metadata schema
- Add schema validation to YARNNN API
- Update agent initialization to set metadata

### 3. Yarn Schema for Agent Content

**Current**: Generic yarn storage, no agent-specific fields

**Needed**:
```json
{
  "yarn_id": "yarn_123",
  "basket_id": "research_basket_001",
  "content": "Research findings...",
  "metadata": {
    "agent_id": "research_agent",
    "session_id": "session_abc",
    "subagent": "web_monitor",
    "domain": "competitors",
    "confidence": 0.85,
    "timestamp": "2025-01-01T00:00:00Z",
    "tags": ["research", "competitor_analysis"]
  }
}
```

**Action**:
- Define yarn schema for agent content
- Add schema validation
- Update YarnnnMemory to populate agent metadata

### 4. Proposal Workflow Refinement

**Current**: Basic propose → approve/reject flow

**Needed**:
- Proposal comments/feedback
- Partial approval (approve some changes, reject others)
- Expiration (auto-reject old proposals)
- Delegation (assign to reviewer)

**Action**:
- Extend proposal schema
- Add review workflow to governance UI
- Implement proposal lifecycle management

### 5. Authentication & Authorization

**Current**: API key authentication only

**Needed** (if multi-tenant):
- User authentication (OAuth, SSO)
- Role-based access control (admin, reviewer, viewer)
- Agent-level permissions (which agents can user access?)
- Workspace-level isolation

**Action**:
- Add auth layer to YARNNN API
- Implement RBAC for agents
- Add workspace access controls

---

## Testing Strategy

### SDK Testing (Open Source)

**Unit Tests**:
```bash
# Core functionality
tests/test_base.py          # BaseAgent
tests/test_interfaces.py    # Provider interfaces
tests/test_session.py       # Session management

# Archetypes
tests/test_research_agent.py
tests/test_content_creator.py
tests/test_reporting_agent.py

# Subagents
tests/test_subagents.py     # Registry and delegation

# Integrations
tests/test_memory_provider.py      # InMemory
tests/test_yarnnn_integration.py   # Mocked YARNNN
```

**Integration Tests**:
```bash
# Requires running YARNNN service
tests/integration/test_yarnnn_memory.py
tests/integration/test_yarnnn_governance.py
tests/integration/test_end_to_end.py
```

**Run All Tests**:
```bash
pytest tests/ -v
pytest tests/integration/ -v --yarnnn-url=http://localhost:8000
```

### YARNNN Service Testing (Proprietary)

**Agent Deployment Tests**:
```bash
# Test agent initialization
tests/test_agent_deployment.py

# Test scheduled execution
tests/test_scheduler.py

# Test governance workflow
tests/test_governance_ui.py
```

**Load Tests**:
```bash
# Simulate multiple agents
tests/load/test_concurrent_agents.py

# Test API limits
tests/load/test_rate_limiting.py
```

---

## Deployment Patterns

### Local Development

```bash
# Terminal 1: YARNNN service
cd yarnnn-core-service
docker-compose up

# Terminal 2: Agent
cd claude-agentsdk-yarnnn
python examples/02_research_agent.py
```

### Production Deployment Options

#### Option 1: Serverless (AWS Lambda)
```yaml
# serverless.yml
functions:
  research-monitor:
    handler: agents.research.monitor.handler
    events:
      - schedule: cron(0 6 * * ? *)  # Daily at 6am
    environment:
      YARNNN_API_URL: ${env:YARNNN_API_URL}
      YARNNN_API_KEY: ${env:YARNNN_API_KEY}
```

#### Option 2: Kubernetes CronJob
```yaml
# research-monitor-cronjob.yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: research-monitor
spec:
  schedule: "0 6 * * *"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: research-agent
            image: yarnnn/research-agent:latest
            env:
            - name: YARNNN_API_URL
              valueFrom:
                secretKeyRef:
                  name: yarnnn-secrets
                  key: api-url
```

#### Option 3: Docker Compose (Simple)
```yaml
# docker-compose.yml
services:
  research-agent:
    build: ./agents/research
    environment:
      - YARNNN_API_URL=http://yarnnn-api:8000
      - SCHEDULE=0 6 * * *  # Daily at 6am
    depends_on:
      - yarnnn-api
```

---

## Next Steps

### Immediate (This Session)
1. ✅ Finalize open-source repo hardening
2. ✅ Create this YARNNN integration guide
3. ⏳ Run final test validation
4. ⏳ Mark development sequence complete

### Short-term (Next 1-2 Weeks)
1. **YARNNN Service Refactoring**:
   - Extract Python client to separate package
   - Standardize basket and yarn schemas
   - Add agent-specific metadata fields

2. **Governance Testing**:
   - Test approval workflow with ContentCreator
   - Gather feedback on voice consistency
   - Decide on voice learning sophistication

3. **Production Deployment**:
   - Create `yarnnn-production-agents` repo
   - Set up ResearchAgent monitoring schedule
   - Deploy governance UI for approvals

### Medium-term (Next 1-2 Months)
1. **Additional Archetypes**:
   - CodeAgent (code analysis and generation)
   - AnalyticsAgent (data analysis and visualization)
   - MonitoringAgent (system health and alerts)

2. **Advanced Features**:
   - Streaming support
   - Multi-agent coordination
   - Computer use tools

3. **Observability**:
   - Agent monitoring dashboard
   - Cost tracking
   - Performance metrics

---

## Open Questions

1. **Tool Governance**: Pre-execution approval vs post-execution approval?
2. **Voice Learning**: Supervised vs unsupervised content learning?
3. **Basket Strategy**: Per-agent vs shared baskets?
4. **Session Retention**: How long to keep session history?
5. **Scheduling**: APScheduler vs Celery vs Cloud scheduler?
6. **Multi-tenancy**: Required for initial launch or Phase 2?

---

## Resources

**Agent SDK (Open Source)**:
- Repo: `claude-agentsdk-yarnnn`
- Examples: `examples/02_research_agent.py`
- Tests: `pytest tests/` (83 passing)

**YARNNN Service (Proprietary)**:
- Repo: `rightnow-agent-app-fullstack` (current)
- New Repo: `yarnnn-production-agents` (to be created)
- API Docs: TBD

**Official Documentation**:
- Claude Agent SDK (TypeScript): https://docs.anthropic.com/en/docs/agents
- Anthropic API: https://docs.anthropic.com/

---

**End of Integration Guide**

*This document will be deleted after transition to YARNNN service session*
