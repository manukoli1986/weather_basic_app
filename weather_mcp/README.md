# Weather MCP Server

MCP server exposing the weather app's data as tools for MCP clients
(Claude Code, Claude Desktop).

## Tools / Resources

| Type | Name | Purpose |
|------|------|---------|
| tool | `get_weather(city)` | current temp, description, humidity, wind |
| tool | `get_forecast(city, slots)` | 3-hour-step forecast |
| resource | `weather://{city}/current` | current weather as a text line |

## Setup

```bash
cd weather_mcp
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
export OPENWEATHER_API_KEY=<your_key>
```

## Try it (MCP Inspector)

```bash
mcp dev weather_mcp_server.py
```
Opens a browser UI to call the tools directly.

## Connect to Claude Code

```bash
claude mcp add weather \
  -e OPENWEATHER_API_KEY=<your_key> \
  -- python /absolute/path/weather_mcp/weather_mcp_server.py
```
Verify with `/mcp` in a session, then ask "weather in London".

## Connect to Claude Desktop

Add to `claude_desktop_config.json`:

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
Restart Claude Desktop.
