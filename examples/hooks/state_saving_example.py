"""
State Saving Hook Example

Demonstrates state persistence using lifecycle hooks.

This example shows how to implement checkpoint/restore functionality
that allows pausing and resuming agent execution.
"""

import json
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from claude_agent_sdk import AgentState, StepResult, InterruptDecision


class StatePersistenceManager:
    """
    State persistence manager using lifecycle hooks.

    Saves execution state after each step, enabling pause/resume.
    """

    def __init__(
        self,
        session_id: str,
        state_dir: str = "./agent_state"
    ):
        """
        Initialize state persistence manager.

        Args:
            session_id: Work session ID
            state_dir: Directory for state files
        """
        self.session_id = session_id
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(exist_ok=True)

        self.state_file = self.state_dir / f"{session_id}.json"

        # Current execution state
        self.execution_state = {
            "session_id": session_id,
            "started_at": datetime.now().isoformat(),
            "status": "in_progress",
            "completed_steps": [],
            "current_step": None,
            "step_outputs": {},
            "paused_at": None,
            "resumed_at": None
        }

        # Load existing state if present
        if self.state_file.exists():
            self._load_state()

    async def on_step_start(self, state: AgentState, context):
        """Update state when step starts"""
        self.execution_state["current_step"] = context.step_name
        self._save_state()

    async def on_step_end(self, state: AgentState, result: StepResult):
        """Save state after step completes"""
        if result.success:
            # Record completed step
            self.execution_state["completed_steps"].append({
                "step_name": result.step_name,
                "completed_at": datetime.now().isoformat(),
                "duration": result.duration
            })

            # Save step output (serialize to JSON)
            self.execution_state["step_outputs"][result.step_name] = (
                self._serialize_output(result.output)
            )

            # Clear current step
            self.execution_state["current_step"] = None

            # Save to disk
            self._save_state()

    async def on_interrupt_signal(
        self,
        state: AgentState,
        reason: str,
        data: Dict[str, Any]
    ) -> InterruptDecision:
        """Handle interrupt by saving state and pausing"""
        if reason == "user_interrupt":
            print(f"\n⏸️  Pausing execution and saving state...")

            # Update state
            self.execution_state["status"] = "paused"
            self.execution_state["paused_at"] = datetime.now().isoformat()
            self._save_state()

            print(f"   State saved to: {self.state_file}")
            print(f"   Completed steps: {len(self.execution_state['completed_steps'])}")

            return InterruptDecision.PAUSE

        return InterruptDecision.CONTINUE

    def resume(self):
        """
        Resume execution from saved state.

        Returns:
            Execution state for resumption
        """
        if self.execution_state["status"] != "paused":
            raise ValueError("Cannot resume - execution not paused")

        self.execution_state["status"] = "in_progress"
        self.execution_state["resumed_at"] = datetime.now().isoformat()
        self._save_state()

        return self.execution_state

    def get_completed_steps(self):
        """Get list of completed step names"""
        return [step["step_name"] for step in self.execution_state["completed_steps"]]

    def get_step_output(self, step_name: str) -> Any:
        """Get output from a completed step"""
        return self.execution_state["step_outputs"].get(step_name)

    def _save_state(self):
        """Save state to disk"""
        with open(self.state_file, 'w') as f:
            json.dump(self.execution_state, f, indent=2)

    def _load_state(self):
        """Load state from disk"""
        with open(self.state_file, 'r') as f:
            self.execution_state = json.load(f)

    def _serialize_output(self, output: Any) -> Any:
        """Serialize output to JSON-compatible format"""
        # Handle complex objects
        if hasattr(output, 'dict'):
            return output.dict()
        elif hasattr(output, '__dict__'):
            return output.__dict__
        else:
            return output

    def print_state(self):
        """Print current state"""
        print("\n" + "="*60)
        print("EXECUTION STATE")
        print("="*60)
        print(f"Session ID: {self.execution_state['session_id']}")
        print(f"Status: {self.execution_state['status']}")
        print(f"Started: {self.execution_state['started_at']}")

        if self.execution_state['paused_at']:
            print(f"Paused: {self.execution_state['paused_at']}")

        if self.execution_state['resumed_at']:
            print(f"Resumed: {self.execution_state['resumed_at']}")

        print(f"\nCompleted Steps: {len(self.execution_state['completed_steps'])}")
        for step in self.execution_state['completed_steps']:
            print(f"  ✓ {step['step_name']} ({step['duration']:.2f}s)")

        if self.execution_state['current_step']:
            print(f"\nCurrent Step: {self.execution_state['current_step']}")

        print("="*60 + "\n")


# === Usage Example ===

async def main():
    """Example usage with pause/resume"""
    from claude_agent_sdk import BaseAgent, StepContext
    from claude_agent_sdk.integrations.memory import InMemoryProvider

    session_id = "pausable_session_001"

    # Create state manager
    state_manager = StatePersistenceManager(
        session_id=session_id,
        state_dir="./demo_state"
    )

    # Create agent with state persistence hooks
    class PausableAgent(BaseAgent):
        def __init__(self, state_manager, **kwargs):
            super().__init__(**kwargs)
            self.state_manager = state_manager

        async def execute(self, task: str, **kwargs):
            completed = self.state_manager.get_completed_steps()

            print(f"\nStarting execution (completed: {completed})")

            # Step 1: Planning (skip if already completed)
            if "plan" not in completed:
                plan = await self.execute_step(
                    "plan",
                    lambda ctx: {"steps": ["a", "b", "c"]},
                    inputs={"task": task}
                )
                await asyncio.sleep(1)
            else:
                plan = self.state_manager.get_step_output("plan")
                print("⏩ Skipping 'plan' (already completed)")

            # Step 2: Preparation (skip if already completed)
            if "prepare" not in completed:
                prep = await self.execute_step(
                    "prepare",
                    lambda ctx: {"status": "ready"},
                    inputs={}
                )
                await asyncio.sleep(1)
            else:
                prep = self.state_manager.get_step_output("prepare")
                print("⏩ Skipping 'prepare' (already completed)")

            # Step 3: Execution (skip if already completed)
            if "execute" not in completed:
                result = await self.execute_step(
                    "execute",
                    lambda ctx: {"status": "completed"},
                    inputs={}
                )
                await asyncio.sleep(1)
            else:
                result = self.state_manager.get_step_output("execute")
                print("⏩ Skipping 'execute' (already completed)")

            # Step 4: Finalization
            if "finalize" not in completed:
                final = await self.execute_step(
                    "finalize",
                    lambda ctx: {"result": result, "done": True},
                    inputs={}
                )
            else:
                final = self.state_manager.get_step_output("finalize")
                print("⏩ Skipping 'finalize' (already completed)")

            return final

    agent = PausableAgent(
        state_manager=state_manager,
        agent_id="pausable",
        memory=InMemoryProvider(),
        on_step_start=state_manager.on_step_start,
        on_step_end=state_manager.on_step_end,
        on_interrupt_signal=state_manager.on_interrupt_signal,
        anthropic_api_key="dummy"
    )

    # === Demo 1: Execute and pause ===
    print("\n" + "="*60)
    print("DEMO 1: EXECUTE AND PAUSE")
    print("="*60)

    # Start execution in background
    task = asyncio.create_task(agent.execute("Test task"))

    # Let it run for 2 seconds (will complete ~2 steps)
    await asyncio.sleep(2)

    # Send interrupt to pause
    await agent.send_interrupt("user_interrupt", {})

    # Wait a bit
    await asyncio.sleep(0.5)

    # Print state
    state_manager.print_state()

    # === Demo 2: Resume ===
    print("\n" + "="*60)
    print("DEMO 2: RESUME FROM SAVED STATE")
    print("="*60)

    # Create new state manager (loads from disk)
    state_manager_2 = StatePersistenceManager(
        session_id=session_id,
        state_dir="./demo_state"
    )

    # Resume
    state_manager_2.resume()
    state_manager_2.print_state()

    # Create new agent and continue
    agent_2 = PausableAgent(
        state_manager=state_manager_2,
        agent_id="pausable",
        memory=InMemoryProvider(),
        on_step_start=state_manager_2.on_step_start,
        on_step_end=state_manager_2.on_step_end,
        on_interrupt_signal=state_manager_2.on_interrupt_signal,
        anthropic_api_key="dummy"
    )

    result = await agent_2.execute("Test task")

    # Print final state
    state_manager_2.execution_state["status"] = "completed"
    state_manager_2.print_state()

    print("✓ Execution completed after resume")


if __name__ == "__main__":
    asyncio.run(main())
