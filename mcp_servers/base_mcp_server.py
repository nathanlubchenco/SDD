"""
Base MCP Server implementation for SDD project.

This provides the foundation for real MCP (Model Context Protocol) servers
that can be called by LLMs through the proper protocol.
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from pathlib import Path


@dataclass
class MCPTool:
    """Represents an MCP tool that can be called by LLMs."""
    name: str
    description: str
    input_schema: Dict[str, Any]
    handler: Callable


@dataclass
class MCPResource:
    """Represents an MCP resource that can be accessed by LLMs."""
    uri: str
    name: str
    description: str
    mime_type: str


@dataclass
class MCPPrompt:
    """Represents an MCP prompt template."""
    name: str
    description: str
    arguments: List[Dict[str, Any]]


class BaseMCPServer(ABC):
    """
    Base class for MCP servers in the SDD project.
    
    This implements the MCP protocol and provides a foundation for
    specialized servers (Docker, Specification, Implementation, etc.)
    """

    def __init__(self, name: str, version: str = "1.0.0"):
        self.name = name
        self.version = version
        self.tools: Dict[str, MCPTool] = {}
        self.resources: Dict[str, MCPResource] = {}
        self.prompts: Dict[str, MCPPrompt] = {}
        self.logger = logging.getLogger(f"mcp.{name}")
        
        # Initialize AI client for tool implementations
        self._init_ai_client()
        
        # Register tools, resources, and prompts
        self._register_capabilities()

    def _init_ai_client(self):
        """Initialize AI client for tool implementations."""
        try:
            from core import ai_client
            self.ai_client = ai_client
        except ImportError as e:
            self.logger.warning(f"AI client not available: {e}")
            self.ai_client = None

    @abstractmethod
    def _register_capabilities(self):
        """Register tools, resources, and prompts. Implemented by subclasses."""
        pass

    def register_tool(self, 
                     name: str, 
                     description: str, 
                     input_schema: Dict[str, Any], 
                     handler: Callable):
        """Register a tool that can be called by LLMs."""
        tool = MCPTool(
            name=name,
            description=description,
            input_schema=input_schema,
            handler=handler
        )
        self.tools[name] = tool
        self.logger.info(f"Registered tool: {name}")

    def register_resource(self, 
                         uri: str, 
                         name: str, 
                         description: str, 
                         mime_type: str = "text/plain"):
        """Register a resource that can be accessed by LLMs."""
        resource = MCPResource(
            uri=uri,
            name=name,
            description=description,
            mime_type=mime_type
        )
        self.resources[uri] = resource
        self.logger.info(f"Registered resource: {uri}")

    def register_prompt(self, 
                       name: str, 
                       description: str, 
                       arguments: List[Dict[str, Any]]):
        """Register a prompt template."""
        prompt = MCPPrompt(
            name=name,
            description=description,
            arguments=arguments
        )
        self.prompts[name] = prompt
        self.logger.info(f"Registered prompt: {name}")

    async def handle_mcp_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle an MCP protocol request.
        
        This is the main entry point for MCP protocol messages.
        """
        try:
            method = request.get("method")
            params = request.get("params", {})
            request_id = request.get("id")

            if method == "initialize":
                return await self._handle_initialize(params, request_id)
            elif method == "tools/list":
                return await self._handle_tools_list(request_id)
            elif method == "tools/call":
                return await self._handle_tools_call(params, request_id)
            elif method == "resources/list":
                return await self._handle_resources_list(request_id)
            elif method == "resources/read":
                return await self._handle_resources_read(params, request_id)
            elif method == "prompts/list":
                return await self._handle_prompts_list(request_id)
            elif method == "prompts/get":
                return await self._handle_prompts_get(params, request_id)
            else:
                return self._error_response(request_id, "METHOD_NOT_FOUND", f"Unknown method: {method}")

        except Exception as e:
            self.logger.error(f"Error handling MCP request: {e}")
            return self._error_response(request.get("id"), "INTERNAL_ERROR", str(e))

    async def _handle_initialize(self, params: Dict[str, Any], request_id: Any) -> Dict[str, Any]:
        """Handle MCP initialize request."""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {"listChanged": True},
                    "resources": {"subscribe": True, "listChanged": True},
                    "prompts": {"listChanged": True}
                },
                "serverInfo": {
                    "name": self.name,
                    "version": self.version
                }
            }
        }

    async def _handle_tools_list(self, request_id: Any) -> Dict[str, Any]:
        """Handle tools/list request."""
        tools_list = []
        for tool in self.tools.values():
            tools_list.append({
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.input_schema
            })

        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "tools": tools_list
            }
        }

    async def _handle_tools_call(self, params: Dict[str, Any], request_id: Any) -> Dict[str, Any]:
        """Handle tools/call request."""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        if tool_name not in self.tools:
            return self._error_response(request_id, "TOOL_NOT_FOUND", f"Tool not found: {tool_name}")

        try:
            tool = self.tools[tool_name]
            result = await tool.handler(**arguments)
            
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": str(result)
                        }
                    ]
                }
            }
        except Exception as e:
            return self._error_response(request_id, "TOOL_ERROR", f"Tool execution failed: {e}")

    async def _handle_resources_list(self, request_id: Any) -> Dict[str, Any]:
        """Handle resources/list request."""
        resources_list = []
        for resource in self.resources.values():
            resources_list.append({
                "uri": resource.uri,
                "name": resource.name,
                "description": resource.description,
                "mimeType": resource.mime_type
            })

        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "resources": resources_list
            }
        }

    async def _handle_resources_read(self, params: Dict[str, Any], request_id: Any) -> Dict[str, Any]:
        """Handle resources/read request."""
        uri = params.get("uri")
        
        if uri not in self.resources:
            return self._error_response(request_id, "RESOURCE_NOT_FOUND", f"Resource not found: {uri}")

        try:
            content = await self._read_resource(uri)
            
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "contents": [
                        {
                            "uri": uri,
                            "mimeType": self.resources[uri].mime_type,
                            "text": content
                        }
                    ]
                }
            }
        except Exception as e:
            return self._error_response(request_id, "RESOURCE_ERROR", f"Resource read failed: {e}")

    async def _handle_prompts_list(self, request_id: Any) -> Dict[str, Any]:
        """Handle prompts/list request."""
        prompts_list = []
        for prompt in self.prompts.values():
            prompts_list.append({
                "name": prompt.name,
                "description": prompt.description,
                "arguments": prompt.arguments
            })

        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "prompts": prompts_list
            }
        }

    async def _handle_prompts_get(self, params: Dict[str, Any], request_id: Any) -> Dict[str, Any]:
        """Handle prompts/get request."""
        prompt_name = params.get("name")
        arguments = params.get("arguments", {})

        if prompt_name not in self.prompts:
            return self._error_response(request_id, "PROMPT_NOT_FOUND", f"Prompt not found: {prompt_name}")

        try:
            content = await self._get_prompt(prompt_name, arguments)
            
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "description": self.prompts[prompt_name].description,
                    "messages": [
                        {
                            "role": "user",
                            "content": {
                                "type": "text",
                                "text": content
                            }
                        }
                    ]
                }
            }
        except Exception as e:
            return self._error_response(request_id, "PROMPT_ERROR", f"Prompt generation failed: {e}")

    def _error_response(self, request_id: Any, code: str, message: str) -> Dict[str, Any]:
        """Generate an MCP error response."""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": code,
                "message": message
            }
        }

    @abstractmethod
    async def _read_resource(self, uri: str) -> str:
        """Read a resource by URI. Implemented by subclasses."""
        pass

    @abstractmethod
    async def _get_prompt(self, name: str, arguments: Dict[str, Any]) -> str:
        """Generate a prompt with arguments. Implemented by subclasses."""
        pass

    async def start_server(self, host: str = "localhost", port: int = 8000):
        """Start the MCP server (for HTTP transport)."""
        # This would implement HTTP server for MCP protocol
        # For now, we'll focus on the direct integration approach
        self.logger.info(f"MCP server {self.name} ready (direct integration mode)")

    def __str__(self):
        return f"MCPServer({self.name} v{self.version}, {len(self.tools)} tools, {len(self.resources)} resources)"