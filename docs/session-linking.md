# Session Linking Guide

**Connecting Agent SDK Sessions with External Task Systems**

This guide explains how to link Agent SDK execution sessions with external work management systems like YARNNN, GitHub Issues, Jira, or custom task trackers.

## Table of Contents

- [Concepts](#concepts)
- [Architecture](#architecture)
- [Implementation Guide](#implementation-guide)
- [YARNNN Integration Example](#yarnnn-integration-example)
- [Best Practices](#best-practices)

---

## Concepts

### Two Types of Sessions

The Agent SDK maintains a clear separation between execution tracking and business workflows:

#### **AgentSession** (Technical Execution)
- **Purpose**: Track agent execution details
- **Managed by**: Agent SDK
- **Contains**: Claude session ID, tasks completed, proposals created, errors
- **Scope**: Single execution instance
- **Location**: `claude_agent_sdk.session.AgentSession`

**Example:**
```python
AgentSession(
    id="session_a3f9c2b1",
    agent_id="research_bot",
    claude_session_id="claude_xyz789",
    started_at=datetime.utcnow(),
    tasks_completed=5,
    proposals_created=["prop_001", "prop_002"]
)
```

#### **WorkSession** (Business Workflow)
- **Purpose**: Track business-level work and deliverables
- **Managed by**: External system (YARNNN, Jira, etc.)
- **Contains**: User assignments, iterations, work artifacts, approvals
- **Scope**: Entire work engagement (may span multiple agent executions)
- **Location**: External task management system

**Example (YARNNN):**
```python
WorkSession(
    id="work_session_123",
    workspace_id="ws_001",
    basket_id="basket_research",
    assigned_user="user_alice",
    status="IN_PROGRESS",
    artifacts=["document_draft", "analysis_report"]
)
```

### Relationship

```
WorkSession (YARNNN)
  ├─ AgentSession 1 (Monday 9am-10am)
  ├─ AgentSession 2 (Monday 2pm-3pm)
  └─ AgentSession 3 (Tuesday 10am-11am)
```

One WorkSession can have multiple AgentSessions over time as the agent works on the task.

---

## Architecture

### Loose Coupling via Metadata

The Agent SDK uses **metadata linking** rather than schema dependencies:

```python
# Agent SDK Session (with optional task linking)
AgentSession(
    id="session_xyz",
    agent_id="bot_001",
    task_id="work_session_123",        # Link to external system
    task_metadata={                     # Pass-through metadata
        "workspace_id": "ws_001",
        "basket_id": "basket_abc",
        "custom_field": "custom_value"
    }
)
```

**Benefits:**
- ✅ Agent SDK remains generic (no YARNNN dependencies)
- ✅ Works with any task system (GitHub, Jira, custom)
- ✅ Optional (can use Agent SDK standalone)
- ✅ Flexible metadata structure

### Data Flow

```
1. External System creates WorkSession
   └─ work_session_id: "work_session_123"
   └─ workspace_id: "ws_001"

2. Agent SDK starts execution
   └─ Creates AgentSession
   └─ Links via task_id and task_metadata

3. Agent creates proposals
   └─ Includes session metadata
   └─ External system can trace back to WorkSession

4. Agent completes
   └─ AgentSession.to_dict() includes task_id
   └─ External system updates WorkSession
```

---

## Implementation Guide

### Step 1: Update Agent Execution

When executing tasks, pass task context to link sessions:

```python
from claude_agent_sdk import BaseAgent
from claude_agent_sdk.integrations.yarnnn import YarnnnMemory, YarnnnGovernance

class MyAgent(BaseAgent):
    async def execute(
        self,
        task: str,
        task_id: Optional[str] = None,
        task_metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        # Start session with task linking
        if not self.current_session:
            self.current_session = self._start_session(
                task_id=task_id,
                task_metadata=task_metadata
            )

        # Your agent logic here...
        contexts = await self.memory.query(task)
        response = await self.reason(task, context=contexts)

        return {
            "session_id": self.current_session.id,
            "task_id": self.current_session.task_id,
            "result": response
        }
```

### Step 2: Call Agent with Task Context

```python
# External system (e.g., YARNNN Work Orchestration)
work_session_id = "work_session_123"
workspace_id = "ws_001"
basket_id = "basket_research"

# Execute agent with task linking
result = await agent.execute(
    task="Research AI governance principles",
    task_id=work_session_id,              # Links to WorkSession
    task_metadata={
        "workspace_id": workspace_id,
        "basket_id": basket_id,
        "work_type": "research"
    }
)

# Extract linked session ID
agent_session_id = result["session_id"]
linked_task_id = result["task_id"]  # Same as work_session_id

# Store link in external system
await work_system.update_session(
    work_session_id,
    agent_session_id=agent_session_id
)
```

### Step 3: Link Proposals to Sessions

When creating proposals, include session metadata:

```python
from claude_agent_sdk.integrations.yarnnn import YarnnnGovernance

# Create standardized session metadata
metadata = YarnnnGovernance.create_session_metadata(
    agent_session_id=agent.current_session.id,
    agent_id=agent.agent_id,
    work_session_id="work_session_123",
    workspace_id="ws_001",
    basket_id="basket_research"
)

# Create proposal with session linking
proposal = await governance.propose(
    changes=[...],
    confidence=0.85,
    reasoning="Adding research insights",
    metadata=metadata
)

# Proposal now contains full traceability:
# - agent_session_id: Which AgentSession created it
# - work_session_id: Which WorkSession it belongs to
# - workspace_id/basket_id: Business context
```

---

## YARNNN Integration Example

Complete example of linking Agent SDK with YARNNN Work Orchestration:

### Scenario

User initiates research work in YARNNN → Agent SDK executes → Results flow back to YARNNN

### Implementation

```python
import asyncio
from claude_agent_sdk.integrations.yarnnn import YarnnnMemory, YarnnnGovernance
from knowledge_agent.agent_v2 import KnowledgeAgent

async def execute_yarnnn_work(work_session_data: dict):
    """
    Execute agent work linked to YARNNN WorkSession.

    Args:
        work_session_data: WorkSession data from YARNNN
            - work_session_id: WorkSession identifier
            - workspace_id: Workspace context
            - basket_id: Knowledge basket to use
            - task_description: What to do
            - user_id: User who initiated work
    """
    # 1. Extract WorkSession details
    work_session_id = work_session_data["work_session_id"]
    workspace_id = work_session_data["workspace_id"]
    basket_id = work_session_data["basket_id"]
    task = work_session_data["task_description"]

    # 2. Initialize YARNNN providers
    memory = YarnnnMemory(
        basket_id=basket_id,
        workspace_id=workspace_id,
        api_key=os.getenv("YARNNN_API_KEY")
    )

    governance = YarnnnGovernance(
        basket_id=basket_id,
        workspace_id=workspace_id,
        api_key=os.getenv("YARNNN_API_KEY")
    )

    # 3. Create agent
    agent = KnowledgeAgent(
        agent_id="yarnnn_research_bot",
        agent_name="YARNNN Research Assistant",
        memory=memory,
        governance=governance,
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY")
    )

    # 4. Execute with session linking
    result = await agent.execute(
        task=task,
        task_id=work_session_id,           # Link to WorkSession
        task_metadata={
            "workspace_id": workspace_id,
            "basket_id": basket_id,
            "user_id": work_session_data["user_id"]
        }
    )

    # 5. Extract session details
    agent_session = agent.current_session

    # 6. Return results with full traceability
    return {
        "work_session_id": work_session_id,
        "agent_session_id": agent_session.id,
        "claude_session_id": agent_session.claude_session_id,
        "proposals_created": agent_session.proposals_created,
        "tasks_completed": agent_session.tasks_completed,
        "errors": agent_session.errors,
        "result": result
    }

# Usage from YARNNN Work Orchestration
async def main():
    # YARNNN creates WorkSession
    work_session = {
        "work_session_id": "work_session_123",
        "workspace_id": "ws_001",
        "basket_id": "basket_research",
        "task_description": "Research AI governance principles and add insights to knowledge base",
        "user_id": "user_alice"
    }

    # Execute agent work with session linking
    result = await execute_yarnnn_work(work_session)

    print(f"WorkSession: {result['work_session_id']}")
    print(f"AgentSession: {result['agent_session_id']}")
    print(f"Proposals: {result['proposals_created']}")

    # YARNNN Work Orchestration can now:
    # 1. Store agent_session_id in WorkSession record
    # 2. Query proposals by agent_session_id
    # 3. Trace all work artifacts back to WorkSession
    # 4. Show user full execution history

if __name__ == "__main__":
    asyncio.run(main())
```

### Traceability Flow

```
YARNNN UI (User perspective)
  ├─ WorkSession: "Research AI Governance"
  │   ├─ Status: IN_PROGRESS
  │   ├─ Agent: "research_bot"
  │   ├─ AgentSessions: ["session_a1", "session_a2"]
  │   └─ Artifacts: [...]
  │
  └─ Proposals (filtered by work_session_id metadata)
      ├─ Proposal 1: "AI Safety Principles" (session_a1)
      └─ Proposal 2: "Governance Frameworks" (session_a2)
```

---

## Best Practices

### 1. Always Link Sessions When Possible

```python
# ✅ Good: Explicit session linking
result = await agent.execute(
    task="Research AI trends",
    task_id="work_session_123",
    task_metadata={"workspace_id": "ws_001"}
)

# ❌ Bad: No linking (loses traceability)
result = await agent.execute("Research AI trends")
```

### 2. Use Standardized Metadata Helpers

```python
# ✅ Good: Use helper for consistency
from claude_agent_sdk.integrations.yarnnn import YarnnnGovernance

metadata = YarnnnGovernance.create_session_metadata(
    agent_session_id=agent.current_session.id,
    agent_id=agent.agent_id,
    work_session_id=work_session_id
)

# ❌ Bad: Manual metadata (inconsistent structure)
metadata = {
    "agentSessionID": agent.current_session.id,  # Wrong naming
    "workSession": work_session_id,              # Inconsistent
}
```

### 3. Store Bidirectional Links

```python
# External system (YARNNN)
work_session = {
    "id": "work_session_123",
    "agent_sessions": ["session_a1", "session_a2"],  # Link to agent sessions
    ...
}

# Agent SDK session
agent_session = AgentSession(
    id="session_a1",
    task_id="work_session_123",  # Link back to work session
    ...
)
```

### 4. Include Session IDs in Proposals

```python
# When creating proposals, always include session context
proposal = await governance.propose(
    changes=[...],
    confidence=0.85,
    reasoning="Research insights",
    metadata=YarnnnGovernance.create_session_metadata(
        agent_session_id=agent.current_session.id,
        work_session_id=work_session_id,
        workspace_id=workspace_id
    )
)
```

### 5. Handle Missing Task Context Gracefully

```python
# Agent should work with or without task linking
async def execute(
    self,
    task: str,
    task_id: Optional[str] = None,
    task_metadata: Optional[Dict[str, Any]] = None,
    **kwargs
):
    # Start session (with or without task linking)
    if not self.current_session:
        self.current_session = self._start_session(
            task_id=task_id,
            task_metadata=task_metadata
        )

    # Agent logic works regardless of task_id
    # ...
```

---

## Advanced: Multi-System Integration

You can link Agent SDK sessions to multiple external systems:

```python
# Link to both YARNNN and GitHub
result = await agent.execute(
    task="Fix authentication bug",
    task_id="work_session_123",
    task_metadata={
        # YARNNN context
        "workspace_id": "ws_001",
        "basket_id": "basket_code",

        # GitHub context
        "github_issue": "#456",
        "github_repo": "org/repo",

        # Custom tracking
        "sprint_id": "sprint_2024_01",
        "priority": "high"
    }
)
```

---

## Summary

**Session linking enables:**
- ✅ Full traceability from user work to agent execution
- ✅ Business context in technical sessions
- ✅ Multi-agent coordination via shared work sessions
- ✅ Rich audit trails and debugging
- ✅ Integration with any task management system

**Key principles:**
- Loose coupling via metadata (not schema dependencies)
- Optional (Agent SDK works standalone)
- Flexible (works with any external system)
- Standardized helpers for consistency

For more information:
- [Architecture Overview](./architecture.md)
- [Quick Start Guide](./QUICK_START.md)
- [YARNNN Integration](../examples/yarnnn_integration.py)
