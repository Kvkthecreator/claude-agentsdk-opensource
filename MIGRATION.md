# Migration Guide

**Upgrading from YARNNN-specific to Generic Claude Agent SDK**

This guide helps you migrate existing code to the new generic architecture.

## What Changed?

### Before (v0.0.x - YARNNN-specific)
- Package: `yarnnn_agents`
- Hardcoded YARNNN integration
- No clear provider separation
- Limited extensibility

### After (v0.1.0 - Generic)
- Package: `claude_agent_sdk`
- Pluggable provider architecture
- YARNNN is one of many integrations
- Highly extensible

## Breaking Changes

### 1. Package Name

```python
# OLD
from yarnnn_agents import BaseAgent, MemoryLayer, GovernanceLayer

# NEW
from claude_agent_sdk import BaseAgent
from claude_agent_sdk.integrations.yarnnn import YarnnnMemory, YarnnnGovernance
```

### 2. Agent Initialization

```python
# OLD
from yarnnn_agents import BaseAgent

class MyAgent(BaseAgent):
    def __init__(self, basket_id):
        super().__init__(
            basket_id=basket_id,
            anthropic_api_key="sk-ant-..."
        )

# NEW
from claude_agent_sdk import BaseAgent
from claude_agent_sdk.integrations.yarnnn import YarnnnMemory, YarnnnGovernance

class MyAgent(BaseAgent):
    def __init__(self, agent_id, basket_id):
        memory = YarnnnMemory(basket_id=basket_id)
        governance = YarnnnGovernance(basket_id=basket_id)
        
        super().__init__(
            agent_id=agent_id,           # NEW: agent identity
            agent_type="custom",          # NEW: agent type
            memory=memory,                # NEW: injected provider
            governance=governance,        # NEW: injected provider
            anthropic_api_key="sk-ant-..."
        )
```

### 3. Memory Operations

```python
# OLD
context = await self.memory.query("AI governance")
# Returns: formatted string

# NEW
contexts = await self.memory.query("AI governance")
# Returns: List[Context]
context_str = "\n".join([c.content for c in contexts])
```

### 4. Governance Operations

```python
# OLD
proposal_id = await self.governance.propose_insight(
    title="New insight",
    body="Content"
)

# NEW (still works)
proposal = await self.governance.propose_insight(
    title="New insight",
    body="Content"
)
proposal_id = proposal.id

# NEW (generic way)
from claude_agent_sdk.interfaces import Change

changes = [Change(
    operation="create",
    target="block",
    data={"title": "New insight", "body": "Content"}
)]

proposal = await self.governance.propose(
    changes=changes,
    confidence=0.8,
    reasoning="Adding new insight"
)
```

## Step-by-Step Migration

### Step 1: Update Imports

```python
# Replace all yarnnn_agents imports
# OLD
from yarnnn_agents import BaseAgent, MemoryLayer, GovernanceLayer
from integrations.yarnnn import YarnnnClient

# NEW
from claude_agent_sdk import BaseAgent
from claude_agent_sdk.integrations.yarnnn import (
    YarnnnClient,
    YarnnnMemory,
    YarnnnGovernance
)
```

### Step 2: Update Agent Class

```python
# OLD
class MyAgent(BaseAgent):
    def __init__(self, basket_id, **kwargs):
        super().__init__(basket_id=basket_id, **kwargs)

# NEW
class MyAgent(BaseAgent):
    def __init__(self, agent_id, basket_id, **kwargs):
        # Setup providers
        memory = YarnnnMemory(basket_id=basket_id)
        governance = YarnnnGovernance(basket_id=basket_id)
        
        # Initialize with providers
        super().__init__(
            agent_id=agent_id,
            agent_type="custom",  # or "knowledge", "content", etc.
            memory=memory,
            governance=governance,
            **kwargs
        )
```

### Step 3: Update execute() Method

```python
# OLD
async def execute(self, task: str):
    context = await self.memory.query(task)  # Returns string
    response = await self.reason(task, context)
    return response

# NEW
async def execute(self, task: str):
    # Start session if not active
    if not self.current_session:
        self.current_session = self._start_session()
    
    # Query returns List[Context]
    contexts = await self.memory.query(task)
    context_str = "\n".join([c.content for c in contexts])
    
    response = await self.reason(task, context_str)
    
    # Track in session
    self.current_session.tasks_completed += 1
    
    return response
```

### Step 4: Update Instantiation

```python
# OLD
agent = MyAgent(
    basket_id="basket_123",
    anthropic_api_key="sk-ant-..."
)

# NEW
agent = MyAgent(
    agent_id="my_agent_001",      # NEW: persistent ID
    basket_id="basket_123",
    anthropic_api_key="sk-ant-..."
)
```

## Backward Compatibility

The old `yarnnn_agents` package is still included for backward compatibility but is **deprecated**. It will be removed in v0.2.0.

### Using Old Package (Deprecated)

```python
# Still works, but deprecated
from yarnnn_agents import BaseAgent

agent = BaseAgent(basket_id="basket_123")
```

**Warning:** This will print a deprecation warning. Please migrate to the new structure.

## Migration Checklist

- [ ] Update imports to `claude_agent_sdk`
- [ ] Add agent_id to all agent instantiations
- [ ] Update memory operations to handle `List[Context]`
- [ ] Update governance operations to use new `Proposal` model
- [ ] Inject providers instead of hardcoding
- [ ] Update tests to use new structure
- [ ] Update documentation/README
- [ ] Test all agent functionality

## Example: Full Migration

### Before

```python
from yarnnn_agents import BaseAgent

class ResearchAgent(BaseAgent):
    def __init__(self, basket_id):
        super().__init__(
            basket_id=basket_id,
            anthropic_api_key="sk-ant-..."
        )
    
    async def execute(self, task: str):
        # Query memory
        context = await self.memory.query(task)
        
        # Reason
        response = await self.reason(task, context)
        
        return response

# Usage
agent = ResearchAgent(basket_id="research")
result = await agent.execute("Research AI")
```

### After

```python
from claude_agent_sdk import BaseAgent
from claude_agent_sdk.integrations.yarnnn import YarnnnMemory, YarnnnGovernance

class ResearchAgent(BaseAgent):
    def __init__(self, agent_id, basket_id):
        # Setup providers
        memory = YarnnnMemory(basket_id=basket_id)
        governance = YarnnnGovernance(basket_id=basket_id)
        
        super().__init__(
            agent_id=agent_id,
            agent_type="research",
            memory=memory,
            governance=governance,
            anthropic_api_key="sk-ant-..."
        )
    
    async def execute(self, task: str):
        # Start session
        if not self.current_session:
            self.current_session = self._start_session()
        
        # Query memory (returns List[Context])
        contexts = await self.memory.query(task)
        context_str = "\n".join([c.content for c in contexts])
        
        # Reason
        response = await self.reason(task, context_str)
        
        # Track
        self.current_session.tasks_completed += 1
        
        return response

# Usage
agent = ResearchAgent(
    agent_id="research_bot_001",  # Persistent ID
    basket_id="research"
)
result = await agent.execute("Research AI")
```

## Benefits of Migrating

1. **Flexibility**: Swap YARNNN for other providers (Notion, GitHub, etc.)
2. **Agent Identity**: Track agents across multiple sessions
3. **Session Management**: Resume conversations, audit trail
4. **Extensibility**: Easy to add new integrations
5. **Type Safety**: Better type hints and validation
6. **Future-proof**: Built for long-term evolution

## Getting Help

If you encounter issues during migration:

1. Check [examples/simple_usage.py](./examples/simple_usage.py) for patterns
2. Review [docs/QUICK_START.md](./docs/QUICK_START.md)
3. Open an issue: [GitHub Issues](https://github.com/Kvkthecreator/claude-agentsdk-yarnnn/issues)

## Timeline

- **v0.1.0** (Current): New architecture introduced, old package deprecated
- **v0.2.0** (ETA: 2-3 months): Old package removed, migration required
- **v1.0.0** (ETA: 6 months): Stable API, production-ready
