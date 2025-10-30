"""
Run Knowledge Agent

Simple CLI to run the Knowledge Agent with various tasks.

Usage:
    python examples/knowledge-agent/run.py --basket-id BASKET_ID --task "Research AI governance"

    python examples/knowledge-agent/run.py --basket-id BASKET_ID --tasks tasks.txt

    python examples/knowledge-agent/run.py --basket-id BASKET_ID --continuous
"""

import asyncio
import argparse
import logging
import sys
import os
from dotenv import load_dotenv

# Add parent directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from examples.knowledge_agent import KnowledgeAgent


# Load environment
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def run_single_task(agent: KnowledgeAgent, task: str, wait: bool = False):
    """Run a single task"""
    logger.info(f"Running task: {task}")

    if wait:
        result = await agent.research_and_wait(task)
    else:
        result = await agent.execute(task)

    logger.info("Task completed!")
    logger.info(f"Status: {result['status']}")

    if result.get("proposals"):
        logger.info(f"Proposals: {', '.join(result['proposals'])}")
        logger.info("Check YARNNN UI to review and approve proposals")

    if result.get("message"):
        logger.info(f"Agent response:\n{result['message']}")

    return result


async def run_multiple_tasks(agent: KnowledgeAgent, tasks: list, delay: int = 10):
    """Run multiple tasks"""
    logger.info(f"Running {len(tasks)} tasks with {delay}s delay...")

    results = await agent.autonomous_loop(
        tasks=tasks,
        delay_between_tasks=delay
    )

    logger.info(f"Completed {len(results)} tasks")

    # Summary
    total_proposals = sum(len(r.get("proposals", [])) for r in results)
    logger.info(f"Total proposals submitted: {total_proposals}")

    return results


async def run_continuous(agent: KnowledgeAgent, interval: int = 300):
    """Run agent continuously"""
    logger.info(f"Starting continuous operation (check interval: {interval}s)")
    logger.info("Press Ctrl+C to stop")

    try:
        await agent.continuous_operation(check_interval=interval)
    except KeyboardInterrupt:
        logger.info("Stopping agent...")


def main():
    parser = argparse.ArgumentParser(description="Run Knowledge Agent")

    # Required
    parser.add_argument(
        "--basket-id",
        required=True,
        help="YARNNN basket ID to operate on"
    )

    # Task modes (mutually exclusive)
    task_group = parser.add_mutually_exclusive_group(required=True)
    task_group.add_argument(
        "--task",
        help="Single task to execute"
    )
    task_group.add_argument(
        "--tasks",
        help="File with tasks (one per line)"
    )
    task_group.add_argument(
        "--continuous",
        action="store_true",
        help="Run continuously"
    )

    # Options
    parser.add_argument(
        "--wait",
        action="store_true",
        help="Wait for proposal approval before continuing"
    )
    parser.add_argument(
        "--delay",
        type=int,
        default=10,
        help="Delay between tasks in seconds (default: 10)"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=300,
        help="Check interval for continuous mode (default: 300s)"
    )
    parser.add_argument(
        "--model",
        default="claude-3-5-sonnet-20241022",
        help="Claude model to use"
    )
    parser.add_argument(
        "--auto-approve",
        action="store_true",
        help="Enable auto-approval (not recommended)"
    )
    parser.add_argument(
        "--confidence-threshold",
        type=float,
        default=0.8,
        help="Confidence threshold for auto-approval (default: 0.8)"
    )

    args = parser.parse_args()

    # Validate environment
    if not os.getenv("ANTHROPIC_API_KEY"):
        logger.error("ANTHROPIC_API_KEY not set in environment")
        sys.exit(1)

    if not os.getenv("YARNNN_API_URL"):
        logger.error("YARNNN_API_URL not set in environment")
        sys.exit(1)

    # Initialize agent
    logger.info(f"Initializing Knowledge Agent for basket {args.basket_id}")

    agent = KnowledgeAgent(
        basket_id=args.basket_id,
        model=args.model,
        auto_approve=args.auto_approve,
        confidence_threshold=args.confidence_threshold
    )

    # Run based on mode
    if args.task:
        # Single task
        asyncio.run(run_single_task(agent, args.task, args.wait))

    elif args.tasks:
        # Multiple tasks from file
        if not os.path.exists(args.tasks):
            logger.error(f"Tasks file not found: {args.tasks}")
            sys.exit(1)

        with open(args.tasks) as f:
            tasks = [line.strip() for line in f if line.strip()]

        if not tasks:
            logger.error("No tasks found in file")
            sys.exit(1)

        asyncio.run(run_multiple_tasks(agent, tasks, args.delay))

    elif args.continuous:
        # Continuous operation
        asyncio.run(run_continuous(agent, args.interval))


if __name__ == "__main__":
    main()
