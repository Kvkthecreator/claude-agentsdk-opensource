# Knowledge Agent Example

An autonomous agent that researches topics, accumulates knowledge, and proposes additions to YARNNN substrate.

## What It Does

The Knowledge Agent:
1. **Queries existing knowledge** from YARNNN substrate
2. **Researches new information** (simulated in this example)
3. **Synthesizes insights** from research
4. **Proposes changes** to substrate via governance
5. **Waits for approval** before committing
6. **Builds connected knowledge graphs** over time

## Architecture

```
User Request: "Research AI governance frameworks"
         ↓
    [Knowledge Agent]
         ↓
    Query Memory (existing AI governance knowledge)
         ↓
    Research (web, docs, etc.) ← NOT IMPLEMENTED YET
         ↓
    Synthesize Insights
         ↓
    Propose to Memory (governance proposal)
         ↓
    Wait for Human Approval
         ↓
    Execute Approved Changes
```

## Quick Start

### 1. Set Up Environment

```bash
# From repository root
cp .env.example .env

# Edit .env with your credentials:
# - ANTHROPIC_API_KEY
# - YARNNN_API_URL
# - YARNNN_API_KEY
# - YARNNN_WORKSPACE_ID
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the Agent

```python
python examples/knowledge-agent/run.py \
  --basket-id YOUR_BASKET_ID \
  --task "Research AI governance frameworks and add to memory"
```

## Usage Examples

### Basic Research

```python
from examples.knowledge_agent import KnowledgeAgent

agent = KnowledgeAgent(basket_id="basket_123")

result = await agent.execute(
    "Research the latest developments in constitutional AI"
)

# Agent will:
# 1. Query existing knowledge about constitutional AI
# 2. Synthesize new insights (from research)
# 3. Propose additions to substrate
# 4. Wait for your approval in YARNNN UI
```

### Multi-Topic Research

```python
topics = [
    "AI alignment techniques",
    "AI governance frameworks",
    "Constitutional AI methods",
    "AI safety research"
]

results = await agent.autonomous_loop(
    tasks=[f"Research {topic}" for topic in topics],
    delay_between_tasks=10  # 10 seconds between tasks
)

# Agent operates autonomously across all topics
# All proposals sent to governance queue for batch review
```

### Continuous Operation

```python
# Agent runs continuously, checking for new research tasks
await agent.continuous_operation(
    check_interval=300,  # Check every 5 minutes
    max_runtime=86400   # Run for 24 hours
)
```

## Configuration

### Agent Behavior

```python
agent = KnowledgeAgent(
    basket_id="basket_123",
    model="claude-3-5-sonnet-20241022",  # Claude model
    auto_approve=False,  # Require human approval (recommended)
    confidence_threshold=0.8,  # Auto-approve above this (if enabled)
    max_retries=3  # Retry failed operations
)
```

### Custom System Prompt

```python
agent = KnowledgeAgent(
    basket_id="basket_123",
    system_prompt="""
    You are a research agent specializing in AI safety.
    Focus on technical accuracy and cite sources.
    Be conservative in confidence scores.
    """
)
```

## Governance Workflow

### 1. Agent Proposes Changes

Agent creates a proposal with:
- Building blocks (insights, concepts)
- Context items (entities, topics)
- Confidence score
- Reasoning explanation

### 2. Review in YARNNN UI

Navigate to:
- Workspace-level: `/workspace/change-requests`
- Basket-level: `/baskets/{id}/change-requests`

You'll see:
- Proposed changes
- Validation report
- Confidence score
- Impact analysis

### 3. Approve or Reject

Click "Approve" to commit to substrate, or "Reject" to decline.

### 4. Agent Continues

Agent receives approval status and proceeds with next task.

## Extending the Agent

### Add Real Research Capabilities

```python
class EnhancedKnowledgeAgent(KnowledgeAgent):
    async def _research_topic(self, topic: str) -> str:
        # Add real research logic:
        # - Web scraping
        # - API calls
        # - Document analysis
        # - Database queries

        results = await self.web_scraper.search(topic)
        return self._synthesize_results(results)
```

### Add Source Tracking

```python
async def propose_with_sources(
    self,
    insights: List[Dict],
    sources: List[str]
):
    for insight in insights:
        insight["metadata"] = {
            "sources": sources,
            "researched_at": datetime.now().isoformat()
        }

    await self.governance.propose(blocks=insights)
```

### Add Quality Filters

```python
def _validate_insight(self, insight: Dict) -> bool:
    # Add validation logic:
    # - Minimum length
    # - Source requirements
    # - Novelty check
    # - Quality scoring

    if len(insight["body"]) < 100:
        return False

    if not insight.get("sources"):
        return False

    return True
```

## Integration with YARNNN

### Memory Query Patterns

```python
# Semantic search
context = await agent.memory.query(
    query="What do we know about AI alignment?",
    limit=20
)

# Anchor-based retrieval
ethics = await agent.memory.get_anchor("AI Ethics")

# Concept-based search
concepts = await agent.memory.get_concepts(
    context_type="concept"
)
```

### Proposal Patterns

```python
# Single insight
proposal = await agent.governance.propose_insight(
    title="Constitutional AI Overview",
    body="Constitutional AI is...",
    tags=["AI Safety", "Alignment"],
    confidence=0.85
)

# Multiple concepts
proposal = await agent.governance.propose_concepts(
    concepts=["RLHF", "Constitutional AI", "Value Alignment"],
    confidence=0.9
)

# Complex proposal
proposal = await agent.governance.propose(
    blocks=[...],
    context_items=[...],
    relationships=[...],
    reasoning="Research findings from today"
)
```

## Troubleshooting

### Agent Not Proposing Changes

Check:
- Is confidence threshold too high?
- Is auto_approve enabled but proposals rejected?
- Are there errors in synthesis logic?

### Proposals Not Approved

Check:
- YARNNN UI for pending proposals
- Governance settings (workspace vs basket level)
- User notifications

### Memory Queries Return Nothing

Check:
- Basket has existing substrate
- Query is semantically relevant
- Semantic search is configured in YARNNN

## Next Steps

1. **Add real research capabilities** (web scraping, APIs)
2. **Integrate with Claude Computer Use** for execution
3. **Add source tracking and citation**
4. **Build quality validation pipeline**
5. **Add continuous monitoring and health checks**

## Learn More

- [BaseAgent API](../../docs/api/base-agent.md)
- [YARNNN Integration](../../docs/yarnnn-integration.md)
- [Governance Workflow](../../docs/governance.md)
- [Creating Custom Agents](../../docs/creating-agents.md)
