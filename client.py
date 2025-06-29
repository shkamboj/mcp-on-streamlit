import asyncio
from contextlib import AsyncExitStack
import json
from mcp import ClientSession
from mcp.client.sse import sse_client
from anthropic import Anthropic
from dotenv import load_dotenv
import sys
import logging

load_dotenv()

class MCPClient:
    def __init__(self):
        self.sessions = {}
        self.servers = {}
        self.available_tools = list()
        self.exit_stack = AsyncExitStack()
        self.anthropic = Anthropic()

    async def connect_to_servers(self, config: dict):
        """Connect to all MCP servers defined in the config
        Args:
            config: Config dict containing server configurations
        """
        
        if "mcpServers" not in config:
            raise ValueError("Config must contain 'mcpServers' key")
        
        if not config["mcpServers"]:
            logging.info("\nNo MCP servers are defined in config")
            return
        
        logging(f"\nAttempting to Connect to {len(config['mcpServers'])} servers...")
        
        for server_name, server_config in config["mcpServers"].items():
            try:
                logging.info(f"\nAttempting to connect to `{server_name}`...")
                            
                transport_type = server_config.get("transport", "http").lower()
                server_url = server_config["url"]
                
                connection_params = {}
                if "timeout" in server_config and server_config["timeout"]:
                    connection_params["timeout"] = server_config["timeout"]
                if "headers" in server_config and server_config["headers"]:
                    connection_params["headers"] = server_config["headers"]
                
                if transport_type == "sse":
                    if "sse_read_timeout" in server_config and server_config["sse_read_timeout"]:
                        connection_params["sse_read_timeout"] = server_config["sse_read_timeout"]
                    
                    transport = await self.exit_stack.enter_async_context(
                        sse_client(server_url, **connection_params)
                    )
                    
                else:
                    logging.info(f"\nUnsupported transport type for '{server_name}': {transport_type}")
                    continue
                
                _session = await self.exit_stack.enter_async_context(
                    ClientSession(transport[0], transport[1])
                )
                
                await _session.initialize()
                
                self.servers[server_name] = transport
                self.sessions[server_name] = _session
                
                response = await _session.list_tools()
                tools = response.tools

                for tool in tools:
                    self.available_tools.append({
                        "name": tool.name,
                        "description": tool.description,
                        "input_schema": tool.inputSchema,
                        "_server": server_name
                    })
                    
            except Exception as e:
                logging.info(f"\nWarning: Could not list tools from server '{server_name}': {e}")
                logging.info(f"\nConnected to '{server_name}' ({transport_type.upper()}) at {server_url}")
                logging.info(f"\nAvailable tools: {[tool.name for tool in tools]}")
        
        connected_count = len(self.sessions)
        total_count = len(config["mcpServers"])
        logging.info(f"\nSuccessfully connected to {connected_count}/{total_count} servers")


    async def process_query(self, query: str) -> str:
        """Process a query using Claude and available tools"""
        if not self.sessions:
            return "No MCP servers connected. Please check your server configuration."
        
        messages = [
            {
                "role": "user",
                "content": query
            }
        ]

        claude_tools = [{k: v for k, v in tool.items() if k != "_server"} for tool in self.available_tools]
        
        response = self.anthropic.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1000,
            messages=messages,
            tools=claude_tools
        )
        
        final_text = []

        assistant_message_content = []
        for content in response.content:
            if content.type == 'text':
                final_text.append(content.text)
                assistant_message_content.append(content)
            elif content.type == 'tool_use':
                tool_name = content.name
                tool_args = content.input

                server_for_tool = None
                for tool in self.available_tools:
                    if tool["name"] == tool_name:
                        server_for_tool = tool["_server"]
                        break

                if server_for_tool and server_for_tool in self.sessions:
                    try:
                        result = await self.sessions[server_for_tool].call_tool(tool_name, tool_args)
                        final_text.append(f"[Calling tool {tool_name} on server {server_for_tool}]")

                        assistant_message_content.append(content)
                        messages.append({
                            "role": "assistant",
                            "content": assistant_message_content
                        })
                        messages.append({
                            "role": "user",
                            "content": [
                                {
                                    "type": "tool_result",
                                    "tool_use_id": content.id,
                                    "content": result.content
                                }
                            ]
                        })

                        response = self.anthropic.messages.create(
                            model="claude-3-5-sonnet-20241022",
                            max_tokens=1000,
                            messages=messages,
                            tools=claude_tools
                        )

                        final_text.append(response.content[0].text)
                    except Exception as e:
                        final_text.append(f"Error executing tool {tool_name}: {str(e)}")
                else:
                    final_text.append(f"Error: Could not find server for tool {tool_name}")

        return "\n".join(final_text)


    # for testing via terminal
    async def chat_loop(self):
        while True:
            try:
                query = input("\nQuery: ").strip()
                if query.lower() == 'quit':
                    break
                response = await self.process_query(query)
                logging.info(f"\n{response}")

            except Exception as e:
                logging.info(f"\nError: {str(e)}")

    async def cleanup(self):
        await self.exit_stack.aclose()


async def main():
    if len(sys.argv) < 2:
        logging.info("Usage: python client.py <path_to_server_config_json>")
        sys.exit(1)

    path = sys.argv[1]
    
    with open(path, 'r') as handle:
        config = json.load(handle)
    client = MCPClient()
    try:
        await client.connect_to_servers(config=config)
        await client.chat_loop()
    finally:
        await client.cleanup()

if __name__ == "__main__":
    import sys
    asyncio.run(main())