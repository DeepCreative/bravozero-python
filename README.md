# Bravo Zero Python SDK

Official Python SDK for the Bravo Zero Breaking the Limits platform.

## Installation

```bash
pip install bravozero
```

## Quick Start

```python
from bravozero import Client, Decision

# Initialize client
client = Client(
    api_key="your-api-key",
    agent_id="your-agent-id"
)

# Evaluate an action against the constitution
result = client.constitution.evaluate(
    action="read_file",
    context={"path": "/project/src/main.py"}
)

if result.decision == Decision.PERMIT:
    print("Action allowed!")
else:
    print(f"Denied: {result.reasoning}")

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

# Access files via VFS
files = client.bridge.list_files("/project/src")
content = client.bridge.read_file("/project/src/main.py")
```

## Async Support

```python
from bravozero import AsyncClient

async with AsyncClient(api_key="your-key") as client:
    result = await client.constitution.evaluate(action="read_file")
    print(result.decision)
```

## Configuration

Set environment variables:

```bash
export BRAVOZERO_API_KEY="your-api-key"
export BRAVOZERO_AGENT_ID="your-agent-id"
export BRAVOZERO_PRIVATE_KEY_PATH="~/.bravozero/private.pem"
```

## Documentation

- [Quickstart Guide](https://docs.bravozero.ai/getting-started)
- [API Reference](https://docs.bravozero.ai/api)
- [Examples](./examples/)

## License

MIT License - see [LICENSE](LICENSE) for details.

