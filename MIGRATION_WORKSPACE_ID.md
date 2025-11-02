# Migration Guide: workspace_id Parameter Change

**Version:** Post-refactor (workspace_id as required parameter)
**Breaking Change:** Yes
**Impact:** All YARNNN integration users

## What Changed?

The `workspace_id` parameter is now **required** and must be passed explicitly when creating `YarnnnClient`, `YarnnnMemory`, or `YarnnnGovernance` instances. It no longer falls back to the `YARNNN_WORKSPACE_ID` environment variable.

## Why This Change?

**Multi-tenant Support:** `workspace_id` is user/tenant-specific and should come from the application request context, not from environment variables. This allows:

- One deployment to serve multiple workspaces/users
- Different requests to use different workspaces
- Proper tenant isolation in multi-tenant SaaS applications

**Service vs. User Credentials:**
- `YARNNN_API_URL` and `YARNNN_API_KEY` are **service-level** credentials (shared across all tenants) → Can use env vars
- `workspace_id` is **user/tenant-specific** → Must come from request context

## Before (Old Code)

```python
import os
from claude_agent_sdk.integrations.yarnnn import YarnnnMemory, YarnnnGovernance

# workspace_id came from environment variable
memory = YarnnnMemory(
    basket_id="basket_123"
    # workspace_id would default to os.getenv("YARNNN_WORKSPACE_ID")
)

governance = YarnnnGovernance(
    basket_id="basket_456"
    # workspace_id would default to os.getenv("YARNNN_WORKSPACE_ID")
)
```

## After (New Code)

```python
import os
from claude_agent_sdk.integrations.yarnnn import YarnnnMemory, YarnnnGovernance

# workspace_id is REQUIRED - get it from your request context
def create_agent_for_user(user_id, basket_id):
    # Get workspace_id from your application context
    workspace_id = get_workspace_for_user(user_id)  # Your application logic

    memory = YarnnnMemory(
        workspace_id=workspace_id,  # REQUIRED parameter (first position)
        basket_id=basket_id
        # api_url and api_key can still fall back to env vars
    )

    governance = YarnnnGovernance(
        workspace_id=workspace_id,  # REQUIRED parameter (first position)
        basket_id=basket_id
    )

    return memory, governance
```

## Migration Steps

### Step 1: Remove YARNNN_WORKSPACE_ID from Environment

Remove this from your `.env` file:
```bash
# DELETE THIS LINE:
YARNNN_WORKSPACE_ID=ws_...
```

Keep these (service-level credentials):
```bash
YARNNN_API_URL=https://yarnnn.example.com
YARNNN_API_KEY=ynk_...
```

### Step 2: Update Your Code

**For Single-Tenant Applications:**

If you only have one workspace, you can hardcode it or use a config constant:

```python
WORKSPACE_ID = "ws_my_workspace"  # Your workspace

memory = YarnnnMemory(
    workspace_id=WORKSPACE_ID,
    basket_id="basket_123"
)
```

**For Multi-Tenant Applications:**

Get `workspace_id` from your request context:

```python
# Flask example
from flask import request, g

@app.before_request
def load_workspace():
    # Get workspace from JWT token, session, database, etc.
    g.workspace_id = get_workspace_from_token(request.headers.get('Authorization'))

@app.route('/api/agent/query')
def query_agent():
    # Use workspace from request context
    memory = YarnnnMemory(
        workspace_id=g.workspace_id,
        basket_id=request.json['basket_id']
    )
    # ... rest of your logic
```

```python
# FastAPI example
from fastapi import Depends, Request

async def get_workspace_id(request: Request) -> str:
    # Extract from JWT, session, etc.
    return extract_workspace_from_token(request.headers.get('authorization'))

@app.post("/api/agent/query")
async def query_agent(
    workspace_id: str = Depends(get_workspace_id),
    basket_id: str
):
    memory = YarnnnMemory(
        workspace_id=workspace_id,
        basket_id=basket_id
    )
    # ... rest of your logic
```

### Step 3: Update Agent Initialization

If you're initializing agents globally, move to per-request initialization:

**Before (problematic):**
```python
# Global initialization (BAD for multi-tenant)
memory = YarnnnMemory(basket_id="basket_123")
agent = MyAgent(memory=memory, ...)

def handle_request(user_id):
    # All users share same agent/memory!
    return agent.execute(task)
```

**After (correct):**
```python
def handle_request(user_id, task):
    # Create agent per request with user's workspace
    workspace_id = get_workspace_for_user(user_id)

    memory = YarnnnMemory(
        workspace_id=workspace_id,
        basket_id="basket_123"
    )

    agent = MyAgent(
        agent_id=f"agent_{user_id}",
        memory=memory,
        ...
    )

    return agent.execute(task)
```

## Error Handling

If you don't provide `workspace_id`, you'll get a clear error:

```python
memory = YarnnnMemory(basket_id="basket_123")
# ValueError: workspace_id is required and must be explicitly provided
```

## Testing Your Migration

1. **Remove** `YARNNN_WORKSPACE_ID` from environment
2. **Run your tests** - they should fail with clear error messages
3. **Update code** to pass `workspace_id` explicitly
4. **Run tests again** - they should pass

## Benefits After Migration

✅ **Multi-tenant ready:** Different users/workspaces isolated
✅ **Explicit:** workspace_id is visible in code, not hidden in env
✅ **Secure:** No risk of using wrong workspace due to env var
✅ **Flexible:** Can switch workspaces per-request

## Need Help?

- Check `examples/01_with_yarnnn.py` for updated examples
- Check `tests/test_yarnnn_integration.py` for test patterns
- Review the updated docstrings in `claude_agent_sdk/integrations/yarnnn/`

## Breaking Change Checklist

- [ ] Removed `YARNNN_WORKSPACE_ID` from `.env`
- [ ] Updated all `YarnnnMemory` calls to include `workspace_id` parameter
- [ ] Updated all `YarnnnGovernance` calls to include `workspace_id` parameter
- [ ] Updated all `YarnnnClient` calls to include `workspace_id` parameter
- [ ] Moved from global agent initialization to per-request initialization (if multi-tenant)
- [ ] All tests pass
- [ ] Application works with explicit workspace_id
