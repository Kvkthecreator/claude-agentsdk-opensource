"""
Claude Tools for YARNNN Integration

These tools allow Claude to interact with YARNNN substrate through
the native tool calling interface.
"""

from typing import Any, Dict, List, Optional
from .client import YarnnnClient, Block, ContextItem


def get_yarnnn_tools(client: YarnnnClient, basket_id: str) -> List[Dict[str, Any]]:
    """
    Get Claude tool definitions for YARNNN integration

    Args:
        client: Initialized YarnnnClient
        basket_id: Default basket to operate on

    Returns:
        List of tool definitions for Claude
    """

    async def query_memory(query: str, limit: int = 20) -> str:
        """
        Query YARNNN substrate for relevant context

        Args:
            query: Semantic search query
            limit: Maximum results to return

        Returns:
            Formatted context from substrate
        """
        results = await client.query_substrate(
            basket_id=basket_id,
            query=query,
            limit=limit
        )

        # Format results for Claude
        formatted = []
        for item in results:
            if item.get("type") == "block":
                formatted.append(
                    f"**{item['title']}**\n{item['body']}\n"
                    f"[Anchor: {item.get('anchor_role', 'orphan')} | "
                    f"State: {item.get('state', 'mature')}]"
                )
            elif item.get("type") == "context_item":
                formatted.append(
                    f"• {item['name']} ({item.get('context_type', 'concept')})"
                )

        return "\n\n".join(formatted) if formatted else "No relevant context found."

    async def propose_to_memory(
        blocks: Optional[List[Dict[str, Any]]] = None,
        context_items: Optional[List[str]] = None,
        reasoning: Optional[str] = None,
        confidence: float = 0.7
    ) -> str:
        """
        Propose changes to YARNNN substrate

        Args:
            blocks: Building blocks to create (list of {title, body, semantic_type})
            context_items: Context items to create (list of names)
            reasoning: Explanation of proposed changes
            confidence: Confidence score (0.0-1.0)

        Returns:
            Proposal ID and status
        """
        # Parse blocks
        block_objs = []
        if blocks:
            for b in blocks:
                block_objs.append(Block(
                    title=b["title"],
                    body=b["body"],
                    semantic_type=b.get("semantic_type", "knowledge"),
                    confidence=b.get("confidence", confidence)
                ))

        # Parse context items
        context_objs = []
        if context_items:
            for name in context_items:
                context_objs.append(ContextItem(name=name))

        # Create proposal
        proposal = await client.create_proposal(
            basket_id=basket_id,
            blocks=block_objs if block_objs else None,
            context_items=context_objs if context_objs else None,
            confidence=confidence,
            reasoning=reasoning
        )

        return (
            f"Proposal created: {proposal.id}\n"
            f"Status: {proposal.status}\n"
            f"Operations: {len(proposal.ops)}\n"
            f"Confidence: {proposal.confidence}\n\n"
            f"Awaiting human review in YARNNN UI."
        )

    async def check_proposal_status(proposal_id: str) -> str:
        """
        Check status of a governance proposal

        Args:
            proposal_id: Proposal ID to check

        Returns:
            Current proposal status
        """
        proposal = await client.get_proposal(proposal_id)

        status_messages = {
            "DRAFT": "Draft - not yet submitted",
            "PROPOSED": "Proposed - awaiting review",
            "UNDER_REVIEW": "Under review",
            "APPROVED": "Approved - ready to commit",
            "REJECTED": "Rejected",
            "COMMITTED": "Committed to substrate"
        }

        return (
            f"Proposal: {proposal.id}\n"
            f"Status: {status_messages.get(proposal.status, proposal.status)}\n"
            f"Operations: {len(proposal.ops)}\n"
            f"Confidence: {proposal.confidence}"
        )

    async def get_anchor_context(anchor: str) -> str:
        """
        Get all blocks under a specific anchor

        Args:
            anchor: Anchor name to query

        Returns:
            Formatted blocks under this anchor
        """
        blocks = await client.get_blocks(
            basket_id=basket_id,
            anchor=anchor,
            limit=50
        )

        if not blocks:
            return f"No blocks found under anchor: {anchor}"

        formatted = [f"## Anchor: {anchor}\n"]
        for block in blocks:
            formatted.append(
                f"**{block['title']}**\n{block['body']}\n"
                f"[State: {block.get('state', 'mature')}]"
            )

        return "\n\n".join(formatted)

    # Tool definitions for Claude
    tools = [
        {
            "name": "query_memory",
            "description": (
                "Query the YARNNN substrate for relevant context. "
                "Use this to retrieve existing knowledge, building blocks, "
                "and context items that are relevant to the current task. "
                "This provides long-term memory beyond the current conversation."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Semantic search query to find relevant context"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results (default: 20)",
                        "default": 20
                    }
                },
                "required": ["query"]
            },
            "function": query_memory
        },
        {
            "name": "propose_to_memory",
            "description": (
                "Propose changes to the YARNNN substrate. Use this to add new "
                "building blocks, context items, or relationships. Changes will "
                "be submitted as a governance proposal that requires human approval "
                "before being committed to the substrate."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "blocks": {
                        "type": "array",
                        "description": "Building blocks to create",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string"},
                                "body": {"type": "string"},
                                "semantic_type": {
                                    "type": "string",
                                    "enum": ["knowledge", "meaning", "structural"],
                                    "default": "knowledge"
                                },
                                "confidence": {
                                    "type": "number",
                                    "minimum": 0.0,
                                    "maximum": 1.0
                                }
                            },
                            "required": ["title", "body"]
                        }
                    },
                    "context_items": {
                        "type": "array",
                        "description": "Context items (entities/concepts) to create",
                        "items": {"type": "string"}
                    },
                    "reasoning": {
                        "type": "string",
                        "description": "Explanation of why these changes are needed"
                    },
                    "confidence": {
                        "type": "number",
                        "description": "Confidence score for this proposal (0.0-1.0)",
                        "minimum": 0.0,
                        "maximum": 1.0,
                        "default": 0.7
                    }
                },
                "required": []
            },
            "function": propose_to_memory
        },
        {
            "name": "check_proposal_status",
            "description": (
                "Check the status of a governance proposal. Use this to see "
                "if a proposal has been approved, rejected, or is still pending review."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "proposal_id": {
                        "type": "string",
                        "description": "Proposal ID to check"
                    }
                },
                "required": ["proposal_id"]
            },
            "function": check_proposal_status
        },
        {
            "name": "get_anchor_context",
            "description": (
                "Get all building blocks under a specific anchor (category). "
                "Use this to understand what knowledge exists in a particular area."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "anchor": {
                        "type": "string",
                        "description": "Anchor name to query"
                    }
                },
                "required": ["anchor"]
            },
            "function": get_anchor_context
        }
    ]

    return tools
