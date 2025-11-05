"""
Logging Hook Example

Demonstrates comprehensive logging using lifecycle hooks.

This example shows how to implement structured logging that captures:
- Step execution flow
- Performance metrics
- Error tracking
- Execution context
"""

import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from claude_agent_sdk import AgentState, StepContext, StepResult


class StructuredLogger:
    """
    Structured logging implementation using lifecycle hooks.

    Logs are structured as JSON for easy parsing and analysis.
    """

    def __init__(
        self,
        session_id: str,
        log_level: str = "INFO",
        log_file: Optional[str] = None
    ):
        """
        Initialize structured logger.

        Args:
            session_id: Work session ID for grouping logs
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
            log_file: Optional file path for log output
        """
        self.session_id = session_id

        # Configure Python logger
        self.logger = logging.getLogger(f"agent.{session_id}")
        self.logger.setLevel(getattr(logging, log_level))

        # Console handler with JSON formatting
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(JsonFormatter())
        self.logger.addHandler(console_handler)

        # File handler if specified
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(JsonFormatter())
            self.logger.addHandler(file_handler)

        # Metrics tracking
        self.metrics = {
            "steps_executed": 0,
            "total_duration": 0.0,
            "errors": 0,
            "steps": {}
        }

    async def on_step_start(self, state: AgentState, context: StepContext):
        """Log step start"""
        self.logger.info("step_start", extra={
            "session_id": self.session_id,
            "agent_id": state.agent_id,
            "step_name": context.step_name,
            "inputs": context.inputs,
            "metadata": context.metadata
        })

    async def on_step_end(self, state: AgentState, result: StepResult):
        """Log step end and update metrics"""
        # Log
        self.logger.info("step_end", extra={
            "session_id": self.session_id,
            "agent_id": state.agent_id,
            "step_name": result.step_name,
            "success": result.success,
            "duration": result.duration,
            "output_size": len(str(result.output)) if result.output else 0
        })

        # Update metrics
        self.metrics["steps_executed"] += 1
        self.metrics["total_duration"] += result.duration

        if result.step_name not in self.metrics["steps"]:
            self.metrics["steps"][result.step_name] = {
                "count": 0,
                "total_duration": 0.0,
                "avg_duration": 0.0
            }

        step_metrics = self.metrics["steps"][result.step_name]
        step_metrics["count"] += 1
        step_metrics["total_duration"] += result.duration
        step_metrics["avg_duration"] = (
            step_metrics["total_duration"] / step_metrics["count"]
        )

    async def on_error(
        self,
        state: AgentState,
        error: Exception,
        context: Optional[str]
    ):
        """Log errors"""
        self.logger.error("error_occurred", extra={
            "session_id": self.session_id,
            "agent_id": state.agent_id,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context
        })

        self.metrics["errors"] += 1

    def get_metrics(self) -> Dict[str, Any]:
        """Get execution metrics"""
        return {
            **self.metrics,
            "avg_step_duration": (
                self.metrics["total_duration"] / self.metrics["steps_executed"]
                if self.metrics["steps_executed"] > 0
                else 0.0
            )
        }

    def print_summary(self):
        """Print execution summary"""
        metrics = self.get_metrics()

        print("\n" + "="*60)
        print("EXECUTION SUMMARY")
        print("="*60)
        print(f"Session ID: {self.session_id}")
        print(f"Steps Executed: {metrics['steps_executed']}")
        print(f"Total Duration: {metrics['total_duration']:.2f}s")
        print(f"Avg Step Duration: {metrics['avg_step_duration']:.2f}s")
        print(f"Errors: {metrics['errors']}")

        if metrics['steps']:
            print("\nPer-Step Metrics:")
            for step_name, step_metrics in metrics['steps'].items():
                print(f"  {step_name}:")
                print(f"    Count: {step_metrics['count']}")
                print(f"    Avg Duration: {step_metrics['avg_duration']:.2f}s")

        print("="*60 + "\n")


class JsonFormatter(logging.Formatter):
    """Format log records as JSON"""

    def format(self, record):
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "level": record.levelname,
            "event": record.getMessage(),
            **getattr(record, "extra", {})
        }
        return json.dumps(log_data)


# === Usage Example ===

async def main():
    """Example usage"""
    import asyncio
    from claude_agent_sdk import BaseAgent
    from claude_agent_sdk.integrations.memory import InMemoryProvider

    # Create structured logger
    logger = StructuredLogger(
        session_id="demo_session_001",
        log_level="INFO"
    )

    # Create agent with logging hooks
    class DemoAgent(BaseAgent):
        async def execute(self, task: str, **kwargs):
            # Step 1
            plan = await self.execute_step(
                "plan",
                lambda ctx: {"steps": ["a", "b", "c"]},
                inputs={"task": task}
            )
            await asyncio.sleep(0.5)

            # Step 2
            result = await self.execute_step(
                "execute",
                lambda ctx: {"status": "completed"},
                inputs={}
            )
            await asyncio.sleep(0.7)

            # Step 3
            output = await self.execute_step(
                "finalize",
                lambda ctx: {"result": result, "formatted": True},
                inputs={}
            )
            await asyncio.sleep(0.3)

            return output

    agent = DemoAgent(
        agent_id="demo",
        memory=InMemoryProvider(),
        on_step_start=logger.on_step_start,
        on_step_end=logger.on_step_end,
        on_error=logger.on_error,
        anthropic_api_key="dummy"
    )

    # Execute
    print("\nExecuting agent with structured logging...")
    result = await agent.execute("Test task")

    # Print summary
    logger.print_summary()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
