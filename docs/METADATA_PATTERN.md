# Context Metadata Pattern

## Overview

The SDK supports **metadata enhancement** via the `Context.metadata` field. This allows implementations to inject custom data without changing SDK interfaces.

This pattern enables implementations to provide rich context (files, configuration, custom data) to agents while maintaining the SDK's generic, provider-agnostic design.

## Design Principles

- **Backward Compatible**: Agents work without metadata
- **Generic**: Not tied to specific implementation schemas
- **Extensible**: Implementations can add any metadata fields
- **Opt-in**: Agents only use metadata if present
- **Graceful Degradation**: Missing metadata fields are handled safely

## The Pattern

### Implementation Side: Injecting Metadata

Implementations inject a "metadata context" as the **first item** in the context list returned by memory queries:

```python
from claude_agent_sdk.interfaces import Context

# Create metadata context with special marker content
metadata_context = Context(
    content="[AGENT EXECUTION CONTEXT]",  # Marker that identifies this as metadata
    metadata={
        "reference_assets": [
            {
                "file_name": "brand_guidelines.pdf",
                "asset_type": "brand_voice",
                "signed_url": "https://...",
                "description": "Primary brand voice guidelines"
            }
        ],
        "agent_config": {
            "brand_voice": {
                "tone": "professional",
                "voice_guidelines": "Clear, concise, authoritative"
            },
            "platforms": {
                "linkedin": {
                    "include_hashtags": True,
                    "max_hashtags": 5
                }
            }
        }
    }
)

# Return as first context item
contexts = [metadata_context, ...regular_blocks...]
return contexts
```

### Agent Side: Consuming Metadata

Agents use the `extract_metadata_from_contexts()` helper to safely extract metadata:

```python
from claude_agent_sdk.interfaces import extract_metadata_from_contexts

# Get contexts from memory
contexts = await self.memory.query("task description")

# Extract metadata (returns {} if not found)
metadata = extract_metadata_from_contexts(contexts)

# Extract specific keys (returns {} if not found)
assets = extract_metadata_from_contexts(contexts, "reference_assets")
config = extract_metadata_from_contexts(contexts, "agent_config")

# Use in agent logic (generic pattern)
if metadata:
    # Implementation provided metadata - enhance behavior
    assets = metadata.get("reference_assets", [])
    for asset in assets:
        # Use whatever fields the implementation provides
        name = asset.get("file_name", "Unknown")
        url = asset.get("signed_url", "")
        # Add to prompt...
```

## Content Marker Convention

The SDK recognizes these special content markers for metadata contexts:

- `[AGENT EXECUTION CONTEXT]` - Primary marker (recommended)
- `[METADATA]` - Alternative marker

These markers signal that the context contains metadata rather than regular content blocks.

## Use Cases

### 1. File/Asset References

Provide agents with access to files, documents, templates:

```python
metadata = {
    "reference_assets": [
        {
            "id": "uuid-123",
            "file_name": "brand_guidelines.pdf",
            "asset_type": "brand_voice",
            "signed_url": "https://storage.example.com/...",
            "description": "Primary brand voice guidelines",
            "mime_type": "application/pdf"
        },
        {
            "id": "uuid-456",
            "file_name": "logo.png",
            "asset_type": "logo",
            "signed_url": "https://storage.example.com/...",
            "description": "Company logo (primary)",
            "mime_type": "image/png"
        }
    ]
}
```

**Agent Usage**: ContentCreatorAgent extracts assets and includes them in prompts for brand consistency.

### 2. Configuration Parameters

Provide behavioral configuration to agents:

```python
metadata = {
    "agent_config": {
        "brand_voice": {
            "tone": "professional",
            "voice_guidelines": "Clear, concise, authoritative"
        },
        "watchlist": {
            "topics": ["AI agents", "automation"],
            "competitors": ["Company A", "Company B"]
        },
        "alert_rules": {
            "confidence_threshold": 0.8,
            "notification_channels": ["email", "slack"]
        }
    }
}
```

**Agent Usage**: ResearchAgent uses watchlist and alert rules to configure monitoring behavior.

### 3. External Context

Provide external identifiers and context:

```python
metadata = {
    "session_context": {
        "user_id": "user_123",
        "workspace_id": "ws_456",
        "project_id": "proj_789"
    },
    "external_ids": {
        "task_id": "task_123",
        "work_session_id": "session_456"
    }
}
```

### 4. Custom Implementation Data

Any implementation-specific data:

```python
metadata = {
    "custom_data": {
        "api_keys": {"service_a": "key_123"},
        "database_connection": "postgres://...",
        "feature_flags": {"new_feature": True}
    }
}
```

## Implementation Examples

### Example 1: Content Creator with Brand Assets

**Implementation (YARNNN):**

```python
class YarnnnMemory(MemoryProvider):
    async def query(self, query: str, filters=None, limit=20):
        # Get regular blocks
        blocks = await self._query_substrate(query, limit)

        # Get reference assets (files)
        assets = await self._get_reference_assets()

        # Get agent config
        config = await self._get_agent_config()

        # Inject metadata as first context
        contexts = [
            Context(
                content="[AGENT EXECUTION CONTEXT]",
                metadata={
                    "reference_assets": assets,
                    "agent_config": config
                }
            )
        ]

        # Add regular block contexts
        contexts.extend([Context(content=b.content) for b in blocks])

        return contexts
```

**Agent (ContentCreator):**

```python
async def create(self, platform: str, topic: str):
    # Get contexts (includes metadata if available)
    contexts = await self.memory.query(f"{platform} content")

    # Extract metadata
    metadata = extract_metadata_from_contexts(contexts)

    # Build prompt
    prompt = f"Create content about: {topic}\n\n"

    # Enhance with metadata if available
    if metadata:
        assets = metadata.get("reference_assets", [])
        for asset in assets:
            if asset.get("asset_type") == "brand_voice":
                prompt += f"Reference: {asset['file_name']}\n"
                prompt += f"URL: {asset['signed_url']}\n"

        config = metadata.get("agent_config", {})
        if "brand_voice" in config:
            tone = config["brand_voice"].get("tone")
            prompt += f"Tone: {tone}\n"

    # Continue with agent logic...
```

### Example 2: Research Agent with Watchlist

**Implementation:**

```python
metadata = {
    "agent_config": {
        "watchlist": {
            "topics": ["AI safety", "LLM alignment"],
            "competitors": ["OpenAI", "Anthropic"]
        },
        "alert_rules": {
            "confidence_threshold": 0.75
        }
    }
}
```

**Agent (ResearchAgent):**

```python
async def monitor(self):
    contexts = await self.memory.query("monitoring config")

    # Extract config
    config = extract_metadata_from_contexts(contexts, "agent_config")

    # Use config-driven monitoring
    topics = []
    competitors = []
    threshold = self.signal_threshold  # default

    if config:
        watchlist = config.get("watchlist", {})
        topics = watchlist.get("topics", [])
        competitors = watchlist.get("competitors", [])

        alert_rules = config.get("alert_rules", {})
        threshold = alert_rules.get("confidence_threshold", threshold)

    # Monitor with config-driven parameters
    # ...
```

### Example 3: Reporting Agent with Formatting Preferences

**Implementation:**

```python
metadata = {
    "agent_config": {
        "report_preferences": {
            "include_toc": True,
            "include_executive_summary": True,
            "default_format": "pdf"
        },
        "formatting": {
            "chart_style": "corporate",
            "color_scheme": "blue",
            "font_family": "Arial"
        }
    }
}
```

**Agent (ReportingAgent):**

```python
async def generate(self, report_type: str, format: str):
    contexts = await self.memory.query(f"{format} templates")

    # Extract config
    config = extract_metadata_from_contexts(contexts, "agent_config")

    # Apply preferences
    include_toc = True  # default
    chart_style = "default"

    if config:
        prefs = config.get("report_preferences", {})
        include_toc = prefs.get("include_toc", True)

        formatting = config.get("formatting", {})
        chart_style = formatting.get("chart_style", "default")

    # Generate report with preferences...
```

## Best Practices

### For Implementations

1. **Always use first context position** for metadata
2. **Use standard marker content**: `[AGENT EXECUTION CONTEXT]`
3. **Make all fields optional**: Agents should handle missing fields gracefully
4. **Document your metadata schema**: Help agent developers know what's available
5. **Include only relevant metadata**: Don't inject data agents won't use

### For Agent Developers

1. **Always use `extract_metadata_from_contexts()`** helper
2. **Use `.get()` with defaults**: Never assume metadata fields exist
3. **Graceful degradation**: Agent should work without any metadata
4. **Filter out metadata contexts** when processing regular blocks:
   ```python
   blocks = [c for c in contexts if c.content not in ["[AGENT EXECUTION CONTEXT]", "[METADATA]"]]
   ```
5. **Log when metadata is used**: Help debug metadata enhancement
6. **Document metadata usage**: Help implementations know what agents expect

## Testing Metadata Enhancement

### Test 1: Without Metadata (Backward Compatibility)

```python
# Agent should work fine with just regular blocks
contexts = [
    Context(content="Regular block 1"),
    Context(content="Regular block 2")
]

result = await agent.create("linkedin", "AI trends")
assert result is not None  # Should succeed
```

### Test 2: With Metadata (Enhancement)

```python
# Agent should use metadata when available
contexts = [
    Context(
        content="[AGENT EXECUTION CONTEXT]",
        metadata={"agent_config": {"brand_voice": {"tone": "professional"}}}
    ),
    Context(content="Regular block")
]

result = await agent.create("linkedin", "AI trends")
assert result["enhanced_with_metadata"] == True
```

### Test 3: With Partial Metadata (Graceful Degradation)

```python
# Agent should handle missing fields gracefully
contexts = [
    Context(
        content="[AGENT EXECUTION CONTEXT]",
        metadata={"reference_assets": []}  # Empty assets
    )
]

result = await agent.create("linkedin", "AI trends")
assert result is not None  # Should succeed without crashing
```

## Version History

- **v0.2.0** (2025-01-14): Initial metadata pattern implementation
  - Added `extract_metadata_from_contexts()` helper
  - Enhanced ContentCreator, Research, and Reporting agents
  - Documented pattern and examples

## See Also

- [Lifecycle Hooks](lifecycle-hooks.md) - Another extensibility mechanism
- [Provider Interfaces](../claude_agent_sdk/interfaces.py) - Core abstractions
- [Agent Archetypes](../claude_agent_sdk/archetypes/) - Example implementations
