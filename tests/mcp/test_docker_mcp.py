#!/usr/bin/env python3
"""
Test script for the Docker MCP Server.

This tests the real MCP server implementation to ensure it can:
1. Register tools correctly
2. Handle MCP protocol requests
3. Generate Docker configurations using AI
"""

import asyncio
import json
from pathlib import Path
import sys

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.mcp_servers.docker_mcp_server import DockerMCPServer


async def test_docker_mcp_server():
    """Test the Docker MCP Server functionality."""
    
    print("🔧 Testing Docker MCP Server")
    
    # Initialize the server
    docker_server = DockerMCPServer()
    print(f"✅ Server initialized: {docker_server}")
    
    # Test 1: Initialize MCP protocol
    print("\n📋 Test 1: MCP Protocol Initialization")
    init_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {}
        }
    }
    
    response = await docker_server.handle_mcp_request(init_request)
    print(f"✅ Initialize response: {response['result']['serverInfo']['name']}")
    
    # Test 2: List available tools
    print("\n🛠️ Test 2: List Available Tools")
    tools_request = {
        "jsonrpc": "2.0", 
        "id": 2,
        "method": "tools/list",
        "params": {}
    }
    
    response = await docker_server.handle_mcp_request(tools_request)
    tools = response['result']['tools']
    print(f"✅ Found {len(tools)} tools:")
    for tool in tools:
        print(f"   - {tool['name']}: {tool['description']}")
    
    # Test 3: Analyze dependencies (this should work without AI)
    print("\n🔍 Test 3: Analyze Dependencies")
    analyze_request = {
        "jsonrpc": "2.0",
        "id": 3, 
        "method": "tools/call",
        "params": {
            "name": "analyze_dependencies",
            "arguments": {
                "implementation_code": """
from fastapi import FastAPI
from fastapi_limiter import FastAPILimiter
import pydantic
import asyncio

app = FastAPI()

@app.get("/health")
async def health():
    return {"status": "ok"}
""",
                "test_code": "import pytest\nimport asyncio"
            }
        }
    }
    
    response = await docker_server.handle_mcp_request(analyze_request)
    if 'result' in response:
        print("✅ Dependency analysis successful")
        # Parse the response content (it's returned as text)
        content = response['result']['content'][0]['text']
        print(f"   Analysis result: {content[:100]}...")
    else:
        print(f"❌ Dependency analysis failed: {response.get('error', 'Unknown error')}")
    
    # Test 4: Generate Dockerfile (will test AI integration)
    print("\n📦 Test 4: Generate Dockerfile")
    dockerfile_request = {
        "jsonrpc": "2.0",
        "id": 4,
        "method": "tools/call", 
        "params": {
            "name": "generate_dockerfile",
            "arguments": {
                "code_analysis": {
                    "language": "python",
                    "dependencies": ["fastapi", "fastapi-limiter", "pydantic"],
                    "has_web_server": True,
                    "has_async": True,
                    "ports": [8000],
                    "python_version": "3.11"
                },
                "constraints": {
                    "security": ["non-root-user", "minimal-attack-surface"],
                    "performance": ["layer-caching", "multi-stage-build"]
                },
                "environment": "production",
                "optimization_goals": ["security", "performance", "size"]
            }
        }
    }
    
    response = await docker_server.handle_mcp_request(dockerfile_request)
    if 'result' in response:
        print("✅ Dockerfile generation successful")
        content = response['result']['content'][0]['text']
        print("Generated Dockerfile:")
        print("```dockerfile")
        print(content[:500] + "..." if len(content) > 500 else content)
        print("```")
    else:
        print(f"❌ Dockerfile generation failed: {response.get('error', 'Unknown error')}")
    
    # Test 5: List resources
    print("\n📚 Test 5: List Resources")
    resources_request = {
        "jsonrpc": "2.0",
        "id": 5,
        "method": "resources/list",
        "params": {}
    }
    
    response = await docker_server.handle_mcp_request(resources_request)
    resources = response['result']['resources']
    print(f"✅ Found {len(resources)} resources:")
    for resource in resources:
        print(f"   - {resource['name']}: {resource['uri']}")
    
    print(f"\n🎉 Docker MCP Server test completed!")
    print(f"Server ready with {len(tools)} tools and {len(resources)} resources")


if __name__ == "__main__":
    asyncio.run(test_docker_mcp_server())