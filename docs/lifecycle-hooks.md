# Lifecycle Hooks

Lifecycle hooks provide extension points for implementing custom orchestration, monitoring, and governance patterns on top of the Claude Agent SDK.

## Philosophy

The SDK provides **mechanisms** (hook registration and invocation), while applications implement **policies** (what happens at each hook).

**SDK's Role**: Call hooks at the right moments
**Your Role**: Implement hooks to add custom behavior

This separation allows the SDK to stay generic while enabling applications like YARNNN to build sophisticated workflow orchestration on top.

---

## Available Hooks

### Step Lifecycle Hooks

#### `on_step_start`

Called before each step execution.

**Signature:**
```python
async def on_step_start(state: AgentState, context: StepContext) -> None
```

**Parameters:**
- `state`: Current agent state (agent_id, session_id, current_step, metadata)
- `context`: Step context (step_name, inputs, metadata)

**Use Cases:**
- Log step execution
- Check for interrupts before starting
- Validate step preconditions
- Notify external systems

**Example:**
```python
async def log_step_start(state: AgentState, context: StepContext):
    print(f"[{state.agent_id}] Starting step: {context.step_name}")

agent = ResearchAgent(
    on_step_start=log_step_start,
    memory=memory_provider,
    anthropic_api_key="sk-ant-..."
)
```

---

#### `on_step_end`

Called after each step execution (success or failure).

**Signature:**
```python
async def on_step_end(state: AgentState, result: StepResult) -> None
```

**Parameters:**
- `state`: Current agent state
- `result`: Step result (step_name, output, success, error, duration, metadata)

**Use Cases:**
- Save step artifacts
- Update progress tracking
- Trigger checkpoint reviews
- Record metrics

**Example:**
```python
async def save_step_artifact(state: AgentState, result: StepResult):
    if result.success:
        await db.save_artifact(
            session_id=state.session_id,
            step_name=result.step_name,
            output=result.output
        )

agent = ResearchAgent(
    on_step_end=save_step_artifact,
    memory=memory_provider,
    anthropic_api_key="sk-ant-..."
)
```

---

### Execution Lifecycle Hooks

#### `before_execute`

Called before agent.execute() starts.

**Signature:**
```python
async def before_execute(state: AgentState, task: str) -> None
```

**Parameters:**
- `state`: Current agent state
- `task`: Task description

**Use Cases:**
- Initialize resources
- Validate task parameters
- Create work session records
- Log task initiation

**Example:**
```python
async def init_work_session(state: AgentState, task: str):
    session = await db.work_sessions.create({
        "agent_id": state.agent_id,
        "session_id": state.session_id,
        "task_intent": task,
        "status": "in_progress"
    })
    print(f"Created work session: {session.id}")

agent = ResearchAgent(
    before_execute=init_work_session,
    memory=memory_provider,
    anthropic_api_key="sk-ant-..."
)
```

---

#### `after_execute`

Called after agent.execute() completes.

**Signature:**
```python
async def after_execute(state: AgentState, result: Any) -> None
```

**Parameters:**
- `state`: Current agent state
- `result`: Execution result

**Use Cases:**
- Finalize work sessions
- Apply outputs to substrate
- Send completion notifications
- Cleanup resources

**Example:**
```python
async def finalize_work_session(state: AgentState, result: Any):
    await db.work_sessions.update(
        session_id=state.session_id,
        status="completed",
        result=result
    )

agent = ResearchAgent(
    after_execute=finalize_work_session,
    memory=memory_provider,
    anthropic_api_key="sk-ant-..."
)
```

---

### Interrupt Handling

#### `on_interrupt_signal`

Called when external system signals an interrupt.

**Signature:**
```python
async def on_interrupt_signal(
    state: AgentState,
    reason: str,
    data: Dict[str, Any]
) -> InterruptDecision
```

**Parameters:**
- `state`: Current agent state
- `reason`: Interrupt reason ("user_interrupt", "error", "timeout")
- `data`: Additional interrupt data

**Returns:**
- `InterruptDecision.PAUSE`: Save state and pause execution
- `InterruptDecision.CONTINUE`: Acknowledge but keep running
- `InterruptDecision.ABORT`: Stop execution immediately

**Use Cases:**
- User requests review mid-execution
- External timeout triggers
- Error recovery decisions

**Example:**
```python
async def handle_interrupt(
    state: AgentState,
    reason: str,
    data: Dict[str, Any]
) -> InterruptDecision:
    if reason == "user_interrupt":
        # Save state and wait for user review
        await save_checkpoint(state)
        await notify_user("Execution paused for review")
        return InterruptDecision.PAUSE

    elif reason == "timeout":
        # Log and abort
        await log_timeout(state)
        return InterruptDecision.ABORT

    else:
        # Unknown reason, continue
        return InterruptDecision.CONTINUE

agent = ResearchAgent(
    on_interrupt_signal=handle_interrupt,
    memory=memory_provider,
    anthropic_api_key="sk-ant-..."
)

# Later, from API endpoint:
await agent.send_interrupt(
    reason="user_interrupt",
    data={"message": "Please review progress"}
)
```

---

### Error Handling

#### `on_error`

Called when step execution fails.

**Signature:**
```python
async def on_error(
    state: AgentState,
    error: Exception,
    context: Optional[str]
) -> None
```

**Parameters:**
- `state`: Current agent state
- `error`: The exception that occurred
- `context`: Optional context (step name, operation)

**Use Cases:**
- Log errors to external system
- Send error notifications
- Update work session status
- Trigger retry logic

**Example:**
```python
async def log_error(
    state: AgentState,
    error: Exception,
    context: Optional[str]
):
    await error_tracker.log({
        "agent_id": state.agent_id,
        "session_id": state.session_id,
        "error_type": type(error).__name__,
        "error_message": str(error),
        "context": context
    })

    await notify_admin(f"Agent error in {context}: {error}")

agent = ResearchAgent(
    on_error=log_error,
    memory=memory_provider,
    anthropic_api_key="sk-ant-..."
)
```

---

### Checkpoint Opportunities

#### `on_checkpoint_opportunity`

Called when agent offers a checkpoint for review.

**Signature:**
```python
async def on_checkpoint_opportunity(
    state: AgentState,
    checkpoint_name: str,
    data: Dict[str, Any]
) -> None
```

**Parameters:**
- `state`: Current agent state
- `checkpoint_name`: Name of checkpoint ("plan_ready", "findings_ready")
- `data`: Data for review (plan, findings, etc.)

**Use Cases:**
- Pause for human review
- Auto-approve based on confidence
- Save checkpoint state
- Notify reviewers

**Example:**
```python
async def handle_checkpoint(
    state: AgentState,
    checkpoint_name: str,
    data: Dict[str, Any]
):
    # Create checkpoint record
    checkpoint = await db.checkpoints.create({
        "session_id": state.session_id,
        "name": checkpoint_name,
        "data": data,
        "status": "pending_review"
    })

    # Notify user
    await notify_user(
        f"Checkpoint '{checkpoint_name}' ready for review",
        checkpoint_id=checkpoint.id
    )

    # Wait for approval
    approved = await wait_for_approval(checkpoint.id, timeout=3600)

    if not approved:
        raise CheckpointRejectedError(f"Checkpoint '{checkpoint_name}' rejected")

agent = ResearchAgent(
    on_checkpoint_opportunity=handle_checkpoint,
    memory=memory_provider,
    anthropic_api_key="sk-ant-..."
)

# In agent implementation:
await agent.offer_checkpoint("plan_ready", {"plan": monitoring_plan})
```

---

## Using Hooks in Agent Implementations

### Step-Based Execution

Agents should structure their execution using `execute_step()` to enable hook invocation:

```python
class ResearchAgent(BaseAgent):
    async def monitor(self, task: str):
        # Start session
        if not self.current_session:
            self.current_session = self._start_session()

        # Step 1: Planning (with checkpoint)
        plan = await self.execute_step(
            "plan",
            self._create_plan,
            inputs={"task": task}
        )
        await self.offer_checkpoint("plan_ready", {"plan": plan})

        # Step 2: Web monitoring
        findings = await self.execute_step(
            "web_monitor",
            lambda ctx: self.subagents.execute("web_monitor", task)
        )

        # Step 3: Analysis
        insights = await self.execute_step(
            "analyze",
            self._analyze_findings,
            inputs={"findings": findings}
        )

        await self.offer_checkpoint("insights_ready", {"insights": insights})

        return insights
```

**Key Points:**
- Use `execute_step()` for each logical step
- Use `offer_checkpoint()` at review points
- Hooks are automatically invoked
- Step functions receive `StepContext` as parameter

---

## Complete Example: YARNNN Integration

Here's how YARNNN implements workflow orchestration using hooks:

```python
from claude_agent_sdk import (
    BaseAgent,
    AgentState,
    StepContext,
    StepResult,
    InterruptDecision
)

class YarnnnOrchestrator:
    """YARNNN-specific orchestration layer using SDK hooks"""

    def __init__(self, work_session_id: str, db: Database):
        self.work_session_id = work_session_id
        self.db = db

    async def on_step_start(self, state: AgentState, context: StepContext):
        """Log step start and check for interrupts"""
        # Update work session
        await self.db.work_sessions.update(
            id=self.work_session_id,
            current_step=context.step_name,
            status="in_progress"
        )

        # Check for pending interrupts
        interrupt = await self.db.check_pending_interrupt(self.work_session_id)
        if interrupt:
            raise InterruptPendingError(interrupt.reason)

    async def on_step_end(self, state: AgentState, result: StepResult):
        """Save step artifacts"""
        if result.success:
            await self.db.work_artifacts.create({
                "work_session_id": self.work_session_id,
                "step_name": result.step_name,
                "artifact_data": result.output,
                "status": "pending_review"
            })

    async def on_checkpoint_opportunity(
        self,
        state: AgentState,
        checkpoint_name: str,
        data: Dict[str, Any]
    ):
        """Pause for checkpoint review"""
        # Create checkpoint
        checkpoint = await self.db.work_checkpoints.create({
            "work_session_id": self.work_session_id,
            "name": checkpoint_name,
            "data": data,
            "status": "pending"
        })

        # Notify user via websocket
        await notify_user_websocket(
            work_session_id=self.work_session_id,
            message=f"Checkpoint '{checkpoint_name}' ready",
            checkpoint_id=checkpoint.id
        )

        # Wait for approval (blocks execution)
        approved = await wait_for_checkpoint_approval(
            checkpoint.id,
            timeout=3600
        )

        if not approved:
            raise CheckpointRejectedError()

    async def on_interrupt_signal(
        self,
        state: AgentState,
        reason: str,
        data: Dict[str, Any]
    ) -> InterruptDecision:
        """Handle interrupt signals"""
        if reason == "user_interrupt":
            # Save current state
            await self.save_checkpoint(state)

            # Update work session
            await self.db.work_sessions.update(
                id=self.work_session_id,
                status="paused"
            )

            return InterruptDecision.PAUSE

        elif reason == "error":
            return InterruptDecision.ABORT

        return InterruptDecision.CONTINUE

# Use with agent
orchestrator = YarnnnOrchestrator(work_session_id="ws_123", db=db)

agent = ResearchAgent(
    agent_id="research_001",
    memory=YarnnnMemory(basket_id="basket_456"),
    governance=YarnnnGovernance(basket_id="basket_456"),
    on_step_start=orchestrator.on_step_start,
    on_step_end=orchestrator.on_step_end,
    on_checkpoint_opportunity=orchestrator.on_checkpoint_opportunity,
    on_interrupt_signal=orchestrator.on_interrupt_signal,
    anthropic_api_key="sk-ant-..."
)

# Execute
result = await agent.monitor("Monitor healthcare AI space")
```

---

## Hook Best Practices

### 1. Hooks Should Be Fast

Hooks are called synchronously during execution. Avoid long-running operations:

**Bad:**
```python
async def on_step_end(state, result):
    # Blocking - waits for external API
    await slow_external_api.process(result.output)
```

**Good:**
```python
async def on_step_end(state, result):
    # Non-blocking - queue for background processing
    await task_queue.enqueue("process_artifact", result.output)
```

### 2. Handle Hook Errors Gracefully

If a hook raises, it will abort execution. Only raise if you want to stop:

```python
async def on_checkpoint_opportunity(state, name, data):
    try:
        await notify_user(name, data)
    except NotificationError:
        # Log but don't abort - notification failure shouldn't stop agent
        logger.warning("Failed to send notification")
```

### 3. Use Hooks for Cross-Cutting Concerns

Hooks are perfect for:
- ✅ Logging
- ✅ Metrics
- ✅ Notifications
- ✅ State persistence
- ✅ Governance checkpoints

Hooks are NOT for:
- ❌ Core business logic (put in agent implementation)
- ❌ Long-running computations
- ❌ Modifying agent behavior (hooks observe, not control)

### 4. Keep State Minimal

`AgentState` is intentionally minimal. Access agent properties directly if needed:

```python
async def on_step_end(state, result):
    # Access agent directly (passed via closure)
    memory_summary = await agent.memory.summarize()
    session_data = agent.current_session.to_dict()
```

---

## Testing Hooks

Use simple hooks for testing:

```python
# Test hook
execution_log = []

async def log_execution(state, context):
    execution_log.append(("start", context.step_name))

agent = ResearchAgent(
    on_step_start=log_execution,
    memory=InMemoryProvider(),
    anthropic_api_key="sk-ant-..."
)

await agent.monitor("Test task")

assert execution_log == [
    ("start", "plan"),
    ("start", "web_monitor"),
    ("start", "analyze")
]
```

---

## Next Steps

- **Examples**: See `examples/03_lifecycle_hooks.py` for complete examples
- **Reference**: See `examples/hooks/` for specific hook implementations
- **Architecture**: See `docs/architecture.md` for how hooks fit in the SDK

---

## Comparison: SDK vs Application

| Concern | SDK (Mechanism) | YARNNN (Policy) |
|---------|-----------------|-----------------|
| **When hooks are called** | SDK decides | - |
| **What hooks do** | - | YARNNN decides |
| **Hook registration** | SDK provides API | YARNNN registers |
| **State objects** | SDK defines minimal state | YARNNN accesses DB |
| **Checkpoints** | SDK calls hook | YARNNN pauses/waits |
| **Interrupts** | SDK invokes hook | YARNNN handles decision |

This separation keeps the SDK generic while enabling sophisticated orchestration patterns.
