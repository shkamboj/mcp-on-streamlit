# mcp-on-streamlit
MCP client integrated within Streamlit UI

## MCP servers:
1. `playwright`: to support navigation of website and search over internet
2. `github`: to support functionalities around github repo.

### How to run above given MCP servers:
1. `playwright`: Run `DEBUG=pw:mcp* npx @playwright/mcp@latest --host 0.0.0.0 --port 8931 --isolated --headless` from any working directory.
2. `github`: Run `python server.py` from root directory of mcp-on-streamlit repository.

### Configuration for MCP servers: (needs to be placed at root directory with name as servers.json)

```
{
  "mcpServers": {
    "playwright": {
      "transport": "sse",
      "url": "http://localhost:8931/sse",
      "timeout": 6000,
      "headers": null,
      "sse_read_timeout": 9000
    },
    "github": {
        "transport": "sse",
        "url": "http://0.0.0.0:8000/sse/",
        "timeout": 6000,
        "headers": null,
        "sse_read_timeout": 9000
    }
  }
}
```

