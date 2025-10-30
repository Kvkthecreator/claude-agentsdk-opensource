# Getting Started with YARNNN Agents

Complete guide to setting up and running your first governed autonomous agent.

## Prerequisites

Before you begin, ensure you have:

1. **Python 3.10 or higher**
   ```bash
   python --version  # Should be 3.10+
   ```

2. **Docker and Docker Compose** (for local YARNNN instance)
   ```bash
   docker --version
   docker-compose --version
   ```

3. **Anthropic API Key**
   - Sign up at [console.anthropic.com](https://console.anthropic.com)
   - Get your API key from the dashboard

4. **YARNNN Instance**
   - Option A: Run locally with Docker (recommended for testing)
   - Option B: Use a hosted YARNNN instance
   - Option C: Deploy your own following [YARNNN docs](https://github.com/Kvkthecreator/rightnow-agent-app-fullstack)

## Step 1: Clone the Repository

```bash
git clone https://github.com/Kvkthecreator/claude-agentsdk-yarnn.git
cd claude-agentsdk-yarnn
```

## Step 2: Install Dependencies

### Using pip

```bash
# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install package in development mode
pip install -e .
```

### Using Docker

```bash
# Build the agent container
docker build -t yarnnn-agent .
```

## Step 3: Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your credentials
nano .env  # or use your preferred editor
```

Required environment variables:

```bash
# Anthropic Configuration
ANTHROPIC_API_KEY=sk-ant-your-key-here

# YARNNN Configuration
YARNNN_API_URL=http://localhost:3000  # or your hosted URL
YARNNN_API_KEY=your_yarnnn_api_key
YARNNN_WORKSPACE_ID=your_workspace_id

# Agent Behavior
AGENT_AUTO_APPROVE=false  # Recommended: require human approval
AGENT_CONFIDENCE_THRESHOLD=0.8
AGENT_MAX_RETRIES=3

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=text
```

## Step 4: Set Up YARNNN (Local Development)

### Option A: Run YARNNN with Docker Compose

```bash
# Start YARNNN (assumes you have the YARNNN image)
docker-compose up -d yarnnn-web

# Check logs
docker-compose logs -f yarnnn-web
```

### Option B: Use Existing YARNNN Instance

If you already have YARNNN running:

1. Get your workspace ID from the YARNNN UI
2. Create an API key in workspace settings
3. Create a basket for your agent to operate on
4. Update `.env` with these values

## Step 5: Verify Setup

Test that everything is configured correctly:

```bash
# Test YARNNN connection
python -c "
from integrations.yarnnn import YarnnnClient
import asyncio

async def test():
    client = YarnnnClient()
    print('YARNNN client initialized successfully!')
    # Try a simple query (will fail if credentials are wrong)
    try:
        result = await client.get_blocks('your-basket-id', limit=1)
        print('✓ YARNNN connection working!')
    except Exception as e:
        print(f'✗ YARNNN connection failed: {e}')

asyncio.run(test())
"
```

## Step 6: Run Your First Agent

### Quick Test

```bash
# Run the Knowledge Agent with a simple task
python examples/knowledge-agent/run.py \
  --basket-id YOUR_BASKET_ID \
  --task "Research AI governance frameworks"
```

You should see:
1. Agent queries YARNNN for existing knowledge
2. Claude reasons about the task
3. Agent proposes changes via YARNNN governance
4. Proposal ID is returned

### Check the Proposal

Navigate to YARNNN UI:
- Workspace-level: `http://localhost:3000/workspace/change-requests`
- Basket-level: `http://localhost:3000/baskets/YOUR_BASKET_ID/change-requests`

You'll see the agent's proposal with:
- Proposed building blocks
- Confidence score
- Reasoning
- Validation report

### Approve the Proposal

Click "Approve" to commit the changes to your substrate.

## Step 7: Try More Examples

### Multiple Tasks

```bash
# Create a tasks file
cat > tasks.txt <<EOF
Research AI alignment techniques
Research constitutional AI methods
Research AI safety best practices
EOF

# Run multiple tasks
python examples/knowledge-agent/run.py \
  --basket-id YOUR_BASKET_ID \
  --tasks tasks.txt \
  --delay 10
```

### Continuous Operation

```bash
# Run agent continuously (checks for tasks every 5 minutes)
python examples/knowledge-agent/run.py \
  --basket-id YOUR_BASKET_ID \
  --continuous \
  --interval 300
```

### With Auto-Approval (Use with Caution!)

```bash
# Auto-approve proposals above 0.85 confidence
python examples/knowledge-agent/run.py \
  --basket-id YOUR_BASKET_ID \
  --task "Research AI ethics principles" \
  --auto-approve \
  --confidence-threshold 0.85
```

## Step 8: Explore the Framework

### Check Agent Status

```python
from examples.knowledge_agent import KnowledgeAgent

agent = KnowledgeAgent(basket_id="your-basket-id")

# Get substrate summary
summary = await agent.memory.summarize_substrate()
print(summary)

# Get recent updates
updates = await agent.memory.get_recent_updates(hours=24)
print(updates)
```

### Create Custom Agent

```python
from yarnnn_agents import BaseAgent

class MyCustomAgent(BaseAgent):
    async def execute(self, task: str):
        # 1. Query memory
        context = await self.memory.query(task)

        # 2. Your custom logic here
        # ...

        # 3. Propose changes
        proposal = await self.governance.propose(
            blocks=[{"title": "New Insight", "body": "Details..."}],
            reasoning="Why this is valuable"
        )

        return {"proposal_id": proposal.id}
```

### Monitor with Docker

```bash
# Run everything with Docker Compose
docker-compose up

# View logs
docker-compose logs -f knowledge-agent

# Stop
docker-compose down
```

## Troubleshooting

### "YARNNN_API_KEY must be set"

**Solution:** Check that `.env` file exists and has correct values:
```bash
cat .env | grep YARNNN_API_KEY
```

### "Connection refused" to YARNNN

**Solution:** Verify YARNNN is running:
```bash
curl http://localhost:3000/api/health
```

### Agent not proposing changes

**Solution:** Check Claude response:
```python
# Add more logging
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Proposals not appearing in UI

**Solution:**
1. Check basket ID is correct
2. Verify governance is enabled in YARNNN settings
3. Look for errors in YARNNN logs

### Import errors

**Solution:** Install in development mode:
```bash
pip install -e .
```

## Next Steps

1. **Read the Architecture** → [docs/architecture.md](./architecture.md)
2. **Create Custom Agents** → [docs/creating-agents.md](./creating-agents.md)
3. **Understand YARNNN** → [YARNNN Documentation](https://github.com/Kvkthecreator/rightnow-agent-app-fullstack/tree/main/docs)
4. **Join the Community** → GitHub Discussions (coming soon)

## Common Workflows

### Development Workflow

```bash
# 1. Start YARNNN
docker-compose up -d yarnnn-web

# 2. Make code changes
nano yarnnn_agents/base.py

# 3. Test changes
python examples/knowledge-agent/run.py --basket-id test-basket --task "Test task"

# 4. Review in YARNNN UI
open http://localhost:3000/baskets/test-basket/change-requests

# 5. Iterate
```

### Production Deployment

```bash
# 1. Build production image
docker build -t yarnnn-agent:prod -f Dockerfile.prod .

# 2. Deploy to your infrastructure
# (specific steps depend on your deployment platform)

# 3. Configure monitoring
# - Set up logging aggregation
# - Configure health checks
# - Set up alerting
```

## Getting Help

- **Documentation:** [docs/](./docs/)
- **Examples:** [examples/](./examples/)
- **Issues:** [GitHub Issues](https://github.com/Kvkthecreator/claude-agentsdk-yarnn/issues)
- **YARNNN Core:** [YARNNN Repository](https://github.com/Kvkthecreator/rightnow-agent-app-fullstack)

---

**You're ready to build governed autonomous agents!**

Start with the Knowledge Agent example, explore the framework, and build your own agents on top of the foundation.
