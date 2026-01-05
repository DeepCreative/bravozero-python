# Bravo Zero Python SDK

Official Python SDK for the Bravo Zero Breaking the Limits platform.

## Installation

```bash
pip install bravozero
```

## Quick Start

```python
from bravozero import Client

# Initialize client
client = Client(api_key="your-api-key")

# Check system health
health = client.governance.get_health()
print(f"System: {health.state}, Omega: {health.omega_score}")
```

## Governance Examples

### Evaluate Actions

```python
# Evaluate an action against the constitution
result = client.governance.evaluate(
    agent_id="agent-123",
    action="Generate a summary of the user's document",
    context={"user_id": "user-456"}
)

if result.decision == "allow":
    print("Action allowed!")
    perform_action()
elif result.decision == "deny":
    print(f"Denied: {result.reasoning}")
elif result.decision == "escalate":
    print("Requires human review")
```

### Monitor Omega Score

```python
# Get current system alignment
omega = client.governance.get_omega()
print(f"Omega Score: {omega.omega:.2f}")
print(f"Trend: {omega.trend}")

for name, score in omega.components.items():
    print(f"  {name}: {score:.2f}")
```

### Submit Governance Proposals

```python
# Submit a proposal for new rule
proposal = client.governance.submit_proposal(
    title="Add data retention rule",
    description="Require agents to respect data retention preferences",
    category="rule"
)

print(f"Proposal {proposal.proposal_id} submitted")
print(f"Voting ends: {proposal.voting_ends_at}")
```

### Check Active Alerts

```python
# Get system alerts
alerts = client.governance.get_alerts()

for alert in alerts.alerts:
    print(f"[{alert['severity']}] {alert['title']}")
```

## Memory Examples

```python
# Store a memory
memory = client.memory.record(
    content="User prefers TypeScript",
    importance=0.8,
    tags=["preference", "language"]
)

# Query memories
results = client.memory.query(
    query="programming preferences",
    limit=5
)

for match in results.matches:
    print(f"[{match.relevance:.2f}] {match.memory.content}")
```

## VFS Examples

```python
# Access files via VFS
files = client.bridge.list_files("/project/src")
content = client.bridge.read_file("/project/src/main.py")
```

## Async Support

```python
from bravozero import AsyncClient

async with AsyncClient(api_key="your-key") as client:
    result = await client.governance.evaluate(
        agent_id="agent-123",
        action="read_file"
    )
    print(result.decision)
```

## Configuration

Set environment variables:

```bash
export BRAVOZERO_API_KEY="your-api-key"
export BRAVOZERO_AGENT_ID="your-agent-id"
```

## Documentation

- [Quickstart Guide](https://docs.bravozero.ai/getting-started)
- [Governance Integration](https://docs.bravozero.ai/guides/governance-integration)
- [API Reference](https://docs.bravozero.ai/api/governance-api)
- [Examples](./examples/)

## License

MIT License - see [LICENSE](LICENSE) for details.

