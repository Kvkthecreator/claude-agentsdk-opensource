"""
Checkpoint Hook Example

Demonstrates a production-ready checkpoint hook implementation
that can pause execution for human review.

This example shows how YARNNN or similar applications can implement
checkpoint-based governance using SDK hooks.
"""

import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from claude_agent_sdk import AgentState


class CheckpointManager:
    """
    Production-ready checkpoint manager.

    In a real application, this would:
    - Store checkpoints in database
    - Send notifications to users (websocket, email, etc.)
    - Wait for approval via API endpoint
    - Implement timeout logic
    """

    def __init__(
        self,
        session_id: str,
        timeout: int = 3600,
        auto_approve_low_risk: bool = False
    ):
        """
        Initialize checkpoint manager.

        Args:
            session_id: Work session ID
            timeout: Max wait time for approval (seconds)
            auto_approve_low_risk: Auto-approve low-risk checkpoints
        """
        self.session_id = session_id
        self.timeout = timeout
        self.auto_approve_low_risk = auto_approve_low_risk

        # In-memory storage (would be database in production)
        self.checkpoints = {}
        self.checkpoint_counter = 0

    async def on_checkpoint_opportunity(
        self,
        state: AgentState,
        checkpoint_name: str,
        data: Dict[str, Any]
    ) -> None:
        """
        Handle checkpoint opportunity.

        This is the hook registered with the agent.

        Args:
            state: Current agent state
            checkpoint_name: Checkpoint identifier
            data: Data for review

        Raises:
            CheckpointRejectedError: If checkpoint is rejected
            CheckpointTimeoutError: If approval not received in time
        """
        # Create checkpoint
        checkpoint_id = await self._create_checkpoint(
            checkpoint_name=checkpoint_name,
            data=data,
            state=state
        )

        print(f"\n🔔 Checkpoint: {checkpoint_name} (ID: {checkpoint_id})")

        # Check if auto-approve
        if await self._should_auto_approve(checkpoint_name, data):
            print("   ✓ Auto-approved (low risk)")
            await self._approve_checkpoint(checkpoint_id)
            return

        # Notify reviewers
        await self._notify_reviewers(checkpoint_id, checkpoint_name, data)

        # Wait for approval
        print(f"   ⏳ Waiting for approval (timeout: {self.timeout}s)...")
        approved = await self._wait_for_approval(checkpoint_id)

        if not approved:
            raise CheckpointRejectedError(
                f"Checkpoint '{checkpoint_name}' was rejected"
            )

        print(f"   ✓ Approved")

    async def _create_checkpoint(
        self,
        checkpoint_name: str,
        data: Dict[str, Any],
        state: AgentState
    ) -> str:
        """Create checkpoint record"""
        self.checkpoint_counter += 1
        checkpoint_id = f"checkpoint_{self.checkpoint_counter:03d}"

        self.checkpoints[checkpoint_id] = {
            "id": checkpoint_id,
            "name": checkpoint_name,
            "data": data,
            "session_id": self.session_id,
            "agent_id": state.agent_id,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "approved_at": None,
            "rejected_at": None,
            "feedback": None
        }

        # In production: await db.checkpoints.create(...)
        return checkpoint_id

    async def _should_auto_approve(
        self,
        checkpoint_name: str,
        data: Dict[str, Any]
    ) -> bool:
        """Determine if checkpoint should be auto-approved"""
        if not self.auto_approve_low_risk:
            return False

        # Example logic (customize based on your risk model)
        low_risk_checkpoints = ["metadata_update", "minor_change"]
        return checkpoint_name in low_risk_checkpoints

    async def _notify_reviewers(
        self,
        checkpoint_id: str,
        checkpoint_name: str,
        data: Dict[str, Any]
    ):
        """Notify reviewers about pending checkpoint"""
        # In production:
        # - Send websocket message
        # - Send email notification
        # - Send Slack message
        # - etc.

        print(f"   📧 Notified reviewers")

    async def _wait_for_approval(
        self,
        checkpoint_id: str,
        poll_interval: int = 2
    ) -> bool:
        """
        Wait for checkpoint approval.

        In production, this would poll database or listen to event stream.

        Args:
            checkpoint_id: Checkpoint to wait for
            poll_interval: Polling frequency (seconds)

        Returns:
            True if approved, False if rejected

        Raises:
            CheckpointTimeoutError: If approval not received in time
        """
        elapsed = 0

        while elapsed < self.timeout:
            # In production: status = await db.checkpoints.get_status(checkpoint_id)
            checkpoint = self.checkpoints.get(checkpoint_id)

            if checkpoint["status"] == "approved":
                return True
            elif checkpoint["status"] == "rejected":
                return False

            # Simulate approval after 2 seconds (for demo)
            if elapsed >= 2:
                await self._approve_checkpoint(checkpoint_id)
                return True

            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

        raise CheckpointTimeoutError(
            f"Checkpoint '{checkpoint_id}' approval timeout ({self.timeout}s)"
        )

    async def _approve_checkpoint(self, checkpoint_id: str):
        """Approve checkpoint"""
        self.checkpoints[checkpoint_id].update({
            "status": "approved",
            "approved_at": datetime.now().isoformat()
        })

        # In production: await db.checkpoints.update(checkpoint_id, status="approved")

    def approve(self, checkpoint_id: str, feedback: Optional[str] = None):
        """
        Approve checkpoint (called from API endpoint).

        In production, this would be called from:
        POST /api/work-sessions/{id}/checkpoints/{checkpoint_id}/approve
        """
        if checkpoint_id in self.checkpoints:
            self.checkpoints[checkpoint_id].update({
                "status": "approved",
                "approved_at": datetime.now().isoformat(),
                "feedback": feedback
            })

    def reject(self, checkpoint_id: str, reason: str):
        """
        Reject checkpoint (called from API endpoint).

        In production, this would be called from:
        POST /api/work-sessions/{id}/checkpoints/{checkpoint_id}/reject
        """
        if checkpoint_id in self.checkpoints:
            self.checkpoints[checkpoint_id].update({
                "status": "rejected",
                "rejected_at": datetime.now().isoformat(),
                "feedback": reason
            })


# === Custom Exceptions ===

class CheckpointRejectedError(Exception):
    """Raised when checkpoint is rejected"""
    pass


class CheckpointTimeoutError(Exception):
    """Raised when checkpoint approval times out"""
    pass


# === Usage Example ===

async def main():
    """Example usage"""
    from claude_agent_sdk import BaseAgent, StepContext
    from claude_agent_sdk.integrations.memory import InMemoryProvider

    # Create checkpoint manager
    checkpoint_manager = CheckpointManager(
        session_id="work_session_123",
        timeout=10,
        auto_approve_low_risk=True
    )

    # Create agent with checkpoint hook
    class DemoAgent(BaseAgent):
        async def execute(self, task: str, **kwargs):
            # Step 1: Planning
            plan = await self.execute_step(
                "plan",
                lambda ctx: {"steps": ["a", "b", "c"]},
                inputs={"task": task}
            )

            # Checkpoint: Review plan
            await self.offer_checkpoint("plan_ready", {"plan": plan})

            # Step 2: Execution
            result = await self.execute_step(
                "execute",
                lambda ctx: {"status": "completed"},
                inputs={}
            )

            # Checkpoint: Review results
            await self.offer_checkpoint("results_ready", {"result": result})

            return result

    agent = DemoAgent(
        agent_id="demo",
        memory=InMemoryProvider(),
        on_checkpoint_opportunity=checkpoint_manager.on_checkpoint_opportunity,
        anthropic_api_key="dummy"
    )

    # Execute
    result = await agent.execute("Test task")

    print("\n✓ Execution completed")
    print(f"\nCheckpoints created: {len(checkpoint_manager.checkpoints)}")
    for cp_id, cp in checkpoint_manager.checkpoints.items():
        print(f"  - {cp['name']}: {cp['status']}")


if __name__ == "__main__":
    asyncio.run(main())
