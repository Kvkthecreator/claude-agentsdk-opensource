"""
Example 03: Lifecycle Hooks

Demonstrates how to use lifecycle hooks to implement custom orchestration,
monitoring, and governance patterns.

This example shows:
- Step-level hooks (on_step_start, on_step_end)
- Checkpoint hooks (on_checkpoint_opportunity)
- Interrupt handling (on_interrupt_signal)
- Error handling (on_error)

Run: python examples/03_lifecycle_hooks.py
"""

import asyncio
import os
from datetime import datetime
from typing import Dict, Any

from claude_agent_sdk import BaseAgent, AgentState, StepContext, StepResult, InterruptDecision
from claude_agent_sdk.integrations.memory import InMemoryProvider


# === Example 1: Simple Logging Hooks ===

class LoggingHooks:
    """Simple hooks that log execution flow"""

    def __init__(self):
        self.log = []

    async def on_step_start(self, state: AgentState, context: StepContext):
        timestamp = datetime.now().isoformat()
        self.log.append(f"[{timestamp}] Step START: {context.step_name}")
        print(f"▶ Starting step: {context.step_name}")

    async def on_step_end(self, state: AgentState, result: StepResult):
        timestamp = datetime.now().isoformat()
        status = "✓" if result.success else "✗"
        self.log.append(
            f"[{timestamp}] Step END: {result.step_name} "
            f"({status}, {result.duration:.2f}s)"
        )
        print(f"{status} Completed step: {result.step_name} ({result.duration:.2f}s)")

    async def on_error(self, state: AgentState, error: Exception, context: str):
        timestamp = datetime.now().isoformat()
        self.log.append(f"[{timestamp}] ERROR in {context}: {error}")
        print(f"✗ Error in {context}: {error}")


# === Example 2: Checkpoint Hooks ===

class CheckpointHooks:
    """Hooks that pause for review at checkpoints"""

    def __init__(self, auto_approve: bool = False):
        self.auto_approve = auto_approve
        self.checkpoints = []

    async def on_checkpoint_opportunity(
        self,
        state: AgentState,
        checkpoint_name: str,
        data: Dict[str, Any]
    ):
        print(f"\n🔔 Checkpoint: {checkpoint_name}")
        print(f"   Data: {data}")

        self.checkpoints.append({
            "name": checkpoint_name,
            "data": data,
            "timestamp": datetime.now().isoformat()
        })

        if self.auto_approve:
            print("   ✓ Auto-approved")
            return

        # Simulate human review (in real app, would wait for API call)
        print("   Waiting for approval... (auto-approving after 1s)")
        await asyncio.sleep(1)
        print("   ✓ Approved")


# === Example 3: Interrupt Handling ===

class InterruptHooks:
    """Hooks that handle interrupt signals"""

    def __init__(self):
        self.interrupts = []

    async def on_interrupt_signal(
        self,
        state: AgentState,
        reason: str,
        data: Dict[str, Any]
    ) -> InterruptDecision:
        print(f"\n⚠️  Interrupt received: {reason}")
        print(f"   Data: {data}")

        self.interrupts.append({
            "reason": reason,
            "data": data,
            "timestamp": datetime.now().isoformat()
        })

        # Decision logic
        if reason == "user_interrupt":
            print("   Decision: PAUSE")
            return InterruptDecision.PAUSE

        elif reason == "error":
            print("   Decision: ABORT")
            return InterruptDecision.ABORT

        else:
            print("   Decision: CONTINUE")
            return InterruptDecision.CONTINUE


# === Example Agent with Hook Support ===

class DemoAgent(BaseAgent):
    """
    Demo agent that uses execute_step() and offer_checkpoint()
    to demonstrate hook invocation.
    """

    async def execute(self, task: str, **kwargs):
        # Start session
        if not self.current_session:
            self.current_session = self._start_session()

        print(f"\n{'='*60}")
        print(f"Executing task: {task}")
        print(f"{'='*60}\n")

        # Step 1: Planning
        plan = await self.execute_step(
            "plan",
            self._create_plan,
            inputs={"task": task}
        )

        # Checkpoint: Review plan
        await self.offer_checkpoint("plan_ready", {"plan": plan})

        # Step 2: Execution
        result = await self.execute_step(
            "execute",
            self._do_work,
            inputs={"plan": plan}
        )

        # Step 3: Finalization
        final_output = await self.execute_step(
            "finalize",
            self._finalize,
            inputs={"result": result}
        )

        # Checkpoint: Review final output
        await self.offer_checkpoint("output_ready", {"output": final_output})

        print(f"\n{'='*60}")
        print(f"Task completed successfully")
        print(f"{'='*60}\n")

        return final_output

    async def _create_plan(self, context: StepContext):
        """Create execution plan"""
        await asyncio.sleep(0.5)  # Simulate planning
        return {
            "task": context.inputs["task"],
            "steps": ["analyze", "synthesize", "format"],
            "estimated_duration": "5min"
        }

    async def _do_work(self, context: StepContext):
        """Execute the plan"""
        await asyncio.sleep(0.7)  # Simulate work
        return {
            "plan": context.inputs["plan"],
            "status": "completed",
            "outputs": ["finding_1", "finding_2", "finding_3"]
        }

    async def _finalize(self, context: StepContext):
        """Finalize outputs"""
        await asyncio.sleep(0.3)  # Simulate finalization
        return {
            "result": context.inputs["result"],
            "formatted": True,
            "ready_for_review": True
        }


# === Example Runs ===

async def example_1_logging():
    """Example 1: Simple logging hooks"""
    print("\n" + "="*60)
    print("EXAMPLE 1: LOGGING HOOKS")
    print("="*60)

    hooks = LoggingHooks()

    agent = DemoAgent(
        agent_id="demo_logging",
        memory=InMemoryProvider(),
        on_step_start=hooks.on_step_start,
        on_step_end=hooks.on_step_end,
        on_error=hooks.on_error,
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", "dummy_key_for_demo")
    )

    result = await agent.execute("Analyze market trends")

    print("\n📋 Execution Log:")
    for entry in hooks.log:
        print(f"  {entry}")


async def example_2_checkpoints():
    """Example 2: Checkpoint hooks"""
    print("\n" + "="*60)
    print("EXAMPLE 2: CHECKPOINT HOOKS")
    print("="*60)

    checkpoint_hooks = CheckpointHooks(auto_approve=False)
    logging_hooks = LoggingHooks()

    agent = DemoAgent(
        agent_id="demo_checkpoints",
        memory=InMemoryProvider(),
        on_step_start=logging_hooks.on_step_start,
        on_step_end=logging_hooks.on_step_end,
        on_checkpoint_opportunity=checkpoint_hooks.on_checkpoint_opportunity,
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", "dummy_key_for_demo")
    )

    result = await agent.execute("Research competitor strategy")

    print("\n📍 Checkpoints:")
    for cp in checkpoint_hooks.checkpoints:
        print(f"  - {cp['name']}: {cp['data']}")


async def example_3_interrupts():
    """Example 3: Interrupt handling"""
    print("\n" + "="*60)
    print("EXAMPLE 3: INTERRUPT HANDLING")
    print("="*60)

    interrupt_hooks = InterruptHooks()

    agent = DemoAgent(
        agent_id="demo_interrupts",
        memory=InMemoryProvider(),
        on_interrupt_signal=interrupt_hooks.on_interrupt_signal,
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", "dummy_key_for_demo")
    )

    # Test different interrupt types
    print("\nTest 1: User interrupt")
    decision = await agent.send_interrupt(
        "user_interrupt",
        {"message": "Please review progress"}
    )
    print(f"Result: {decision}")

    print("\nTest 2: Error interrupt")
    decision = await agent.send_interrupt(
        "error",
        {"error": "Connection timeout"}
    )
    print(f"Result: {decision}")

    print("\nTest 3: Unknown interrupt")
    decision = await agent.send_interrupt(
        "unknown_reason",
        {}
    )
    print(f"Result: {decision}")


async def example_4_combined():
    """Example 4: Combined hooks (realistic scenario)"""
    print("\n" + "="*60)
    print("EXAMPLE 4: COMBINED HOOKS (REALISTIC)")
    print("="*60)

    logging_hooks = LoggingHooks()
    checkpoint_hooks = CheckpointHooks(auto_approve=True)
    interrupt_hooks = InterruptHooks()

    agent = DemoAgent(
        agent_id="demo_combined",
        memory=InMemoryProvider(),
        on_step_start=logging_hooks.on_step_start,
        on_step_end=logging_hooks.on_step_end,
        on_checkpoint_opportunity=checkpoint_hooks.on_checkpoint_opportunity,
        on_interrupt_signal=interrupt_hooks.on_interrupt_signal,
        on_error=logging_hooks.on_error,
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", "dummy_key_for_demo")
    )

    result = await agent.execute("Generate quarterly report")

    print("\n📊 Summary:")
    print(f"  Steps executed: {len([l for l in logging_hooks.log if 'Step END' in l])}")
    print(f"  Checkpoints: {len(checkpoint_hooks.checkpoints)}")
    print(f"  Interrupts: {len(interrupt_hooks.interrupts)}")


async def main():
    """Run all examples"""
    await example_1_logging()
    await example_2_checkpoints()
    await example_3_interrupts()
    await example_4_combined()

    print("\n" + "="*60)
    print("✓ All examples completed")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
