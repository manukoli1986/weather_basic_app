# Weather MCP Server

MCP server that exposes the weather app's data as tools for MCP clients
(Claude Code, Claude Desktop).

[← back to main README](../README.md)

---

## What is MCP?

**MCP (Model Context Protocol)** is a standard way for AI clients to call
external tools. You write a small server that registers **tools** (functions),
**resources** (readable data), and the client (Claude Code / Desktop) discovers
and calls them. Transport is **stdio** (client spawns your process) or **HTTP**.

## What this server exposes

| Type | Name | Purpose |
|------|------|---------|
| tool | `get_weather(city)` | current temp, feels-like, humidity, wind, condition |
| tool | `get_forecast(city, slots)` | 3-hour-step forecast, `slots` steps ahead |
| resource | `weather://{city}/current` | current weather as a text line |

---

## How it was created

**1. Install the SDK**
```bash
cd weather_mcp
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt      # mcp[cli] + requests
```

**2. Create the server** — `weather_mcp_server.py`. Core shape:
```python
from mcp.server.mcpserver import MCPServer   # SDK 2.0 class (was FastMCP in 1.x)

mcp = MCPServer("weather")

@mcp.tool()
def get_weather(city: str) -> dict:
    """Get current weather for a city."""   # docstring + type hints = what the LLM reads
    ...

@mcp.resource("weather://{city}/current")
def current_weather_resource(city: str) -> str:
    ...

if __name__ == "__main__":
    mcp.run()   # stdio transport
```

Key ideas:
- `@mcp.tool()` registers a function. **Docstring + type hints matter** — the LLM
  uses them to decide when and how to call it.
- Same OpenWeather logic as the web app; API key read from `OPENWEATHER_API_KEY`.
- `mcp.run()` starts the stdio loop.

**3. Set the key**
```bash
export OPENWEATHER_API_KEY=<your_key>
```

---

## How to connect a client

### Claude Code (CLI)
```bash
claude mcp add weather \
  -e OPENWEATHER_API_KEY=<your_key> \
  -- python /absolute/path/weather_mcp/weather_mcp_server.py
```
Then in a session run `/mcp` to confirm it's connected, and ask
"what's the weather in London" — Claude calls `get_weather`.

### Claude Desktop
Add to `claude_desktop_config.json`
(macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "weather": {
      "command": "python",
      "args": ["/absolute/path/weather_mcp/weather_mcp_server.py"],
      "env": { "OPENWEATHER_API_KEY": "<your_key>" }
    }
  }
}
```
Restart Claude Desktop. The tools appear in the 🔌 menu.

### Test without a client (MCP Inspector)
```bash
mcp dev weather_mcp_server.py
```
Opens a browser UI to call the tools directly.

---

## Extend it (learning next steps)
- Add more tools: air quality, alerts.
- Serve over **HTTP** for remote clients: `mcp.run(transport="streamable-http")`.
- Spec + docs: https://modelcontextprotocol.io
