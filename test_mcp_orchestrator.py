#!/usr/bin/env python3
"""
Test script for the MCP-enabled SDD Orchestrator.

This tests the complete MCP protocol integration across all servers.
"""

import asyncio
import json
from pathlib import Path
import sys

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

from orchestrator.mcp_orchestrator import MCPOrchestrator


async def test_mcp_orchestrator():
    """Test the MCP-enabled orchestrator functionality."""
    
    print("🎛️ Testing MCP-Enabled SDD Orchestrator")
    
    # Initialize the orchestrator
    orchestrator = MCPOrchestrator()
    await asyncio.sleep(1)  # Allow servers to initialize
    
    print(f"✅ Orchestrator initialized: {orchestrator}")
    
    # Test 1: Check system status
    print("\n📊 Test 1: System Status Check")
    status = await orchestrator.get_system_status()
    print(f"✅ System status retrieved")
    print(f"   Orchestrator type: {status['orchestrator_type']}")
    
    for server_name, server_info in status["servers"].items():
        mcp_status = "🔧 MCP" if server_info.get("mcp_enabled") else "❌ No MCP"
        print(f"   {server_name}: {server_info['status']} {mcp_status}")
    
    # Test 2: List available tools across all servers
    print("\n🛠️ Test 2: List All Available MCP Tools")
    tools_by_server = await orchestrator.list_available_tools()
    
    total_tools = 0
    for server_name, tools in tools_by_server.items():
        if tools and isinstance(tools, list) and 'error' not in tools[0]:
            print(f"   {server_name}: {len(tools)} tools")
            total_tools += len(tools)
            for tool in tools[:2]:  # Show first 2 tools
                print(f"      - {tool['name']}")
        else:
            print(f"   {server_name}: Error or no tools")
    
    print(f"✅ Total MCP tools available: {total_tools}")
    
    # Test 3: Call individual MCP tools
    print("\n🔧 Test 3: Call Individual MCP Tools")
    
    # Test specification server tool
    print("   📋 Testing specification server...")
    spec_response = await orchestrator.call_mcp_tool(
        "specification",
        "get_scenarios", 
        {"domain": "test_domain", "include_constraints": True}
    )
    
    if 'result' in spec_response:
        print("   ✅ Specification tool call successful")
    else:
        print(f"   ⚠️ Specification tool call: {spec_response.get('error', 'Unknown error')}")
    
    # Test docker server tool
    print("   🐳 Testing docker server...")
    docker_response = await orchestrator.call_mcp_tool(
        "docker",
        "analyze_dependencies",
        {
            "implementation_code": "from fastapi import FastAPI\napp = FastAPI()",
            "test_code": "import pytest"
        }
    )
    
    if 'result' in docker_response:
        print("   ✅ Docker tool call successful")
    else:
        print(f"   ⚠️ Docker tool call: {docker_response.get('error', 'Unknown error')}")
    
    # Test 4: Full implementation workflow (simplified)
    print("\n🚀 Test 4: MCP Implementation Workflow")
    
    try:
        # This will test the full MCP-enabled workflow
        result = await orchestrator.implement_feature(
            feature_request="Simple Calculator Service",
            domain="calculator"
        )
        
        if result["status"] == "completed":
            print("✅ Full MCP workflow completed successfully!")
            print(f"   Domain: {result['domain']}")
            print(f"   Specification status: {result['specification']['status']}")
            print(f"   Implementation workspace: {result['implementation']['workspace_id']}")
            print(f"   Docker generated: {result['docker'].get('mcp_generated', False)}")
            print(f"   MCP enabled: {result['mcp_enabled']}")
            
            # Show some details about what was generated
            docker_info = result.get('docker', {})
            if docker_info.get('status') == 'completed':
                analysis = docker_info.get('code_analysis', {})
                deps = analysis.get('dependencies', set())
                print(f"   Dependencies detected: {len(deps)} - {list(deps)[:3]}")
                print(f"   Has web server: {analysis.get('has_web_server', False)}")
                
        elif result["status"] == "failed":
            print(f"❌ MCP workflow failed: {result.get('error', 'Unknown error')}")
        
    except Exception as e:
        print(f"❌ MCP workflow exception: {e}")
    
    # Test 5: Resource access
    print("\n📚 Test 5: Resource Access")
    
    # Test reading a specification template
    try:
        resources_request = {
            "jsonrpc": "2.0",
            "id": "resources_test",
            "method": "resources/read",
            "params": {
                "uri": "spec://templates/basic-scenario"
            }
        }
        
        resource_response = await orchestrator.spec_server.handle_mcp_request(resources_request)
        
        if 'result' in resource_response:
            content = resource_response['result']['contents'][0]['text']
            print("✅ Resource access successful")
            print(f"   Template preview: {content[:100]}...")
        else:
            print(f"⚠️ Resource access failed: {resource_response.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Resource access exception: {e}")
    
    print(f"\n🎉 MCP Orchestrator test completed!")
    print(f"The system now uses real MCP protocol for AI-driven development")


if __name__ == "__main__":
    asyncio.run(test_mcp_orchestrator())