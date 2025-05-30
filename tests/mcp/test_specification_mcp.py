#!/usr/bin/env python3
"""
Test script for the Specification MCP Server.

This tests the real MCP server implementation for specification management.
"""

import asyncio
import json
import yaml
from pathlib import Path
import sys

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.mcp_servers.specification_mcp_server import SpecificationMCPServer


async def test_specification_mcp_server():
    """Test the Specification MCP Server functionality."""
    
    print("📋 Testing Specification MCP Server")
    
    # Use the existing specs directory
    spec_dir = Path("specs")
    spec_server = SpecificationMCPServer(spec_dir)
    print(f"✅ Server initialized: {spec_server}")
    
    # Test 1: Initialize MCP protocol
    print("\n🔧 Test 1: MCP Protocol Initialization")
    init_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {}
        }
    }
    
    response = await spec_server.handle_mcp_request(init_request)
    print(f"✅ Initialize response: {response['result']['serverInfo']['name']}")
    
    # Test 2: List available tools
    print("\n🛠️ Test 2: List Available Tools")
    tools_request = {
        "jsonrpc": "2.0", 
        "id": 2,
        "method": "tools/list",
        "params": {}
    }
    
    response = await spec_server.handle_mcp_request(tools_request)
    tools = response['result']['tools']
    print(f"✅ Found {len(tools)} tools:")
    for tool in tools:
        print(f"   - {tool['name']}: {tool['description']}")
    
    # Test 3: Get scenarios (should work without AI)
    print("\n📖 Test 3: Get Scenarios")
    
    # First, let's create a test specification if it doesn't exist
    test_spec_content = """
feature:
  name: "Task Management System"
  description: "Manage user tasks and todo items"

scenarios:
  - name: "Create a simple task"
    description: "User creates a new task with a title"
    given: "User is logged into the system"
    when: "User creates a task with title 'Buy groceries'"
    then:
      - "Task is created with status 'pending'"
      - "Task has a unique identifier"
      - "Task title is 'Buy groceries'"
    
  - name: "Complete a task"
    description: "User marks a task as completed"
    given: "User has a pending task"
    when: "User marks the task as complete"
    then:
      - "Task status changes to 'completed'"
      - "Task completion time is recorded"

constraints:
  performance:
    - name: "API response time"
      requirement: "All operations complete within 200ms"
  
  security:
    - name: "User authentication"
      requirement: "All operations require valid user session"
"""
    
    # Write test spec
    test_spec_path = spec_dir / "task_manager.yaml"
    test_spec_path.parent.mkdir(exist_ok=True)
    test_spec_path.write_text(test_spec_content)
    
    # Reload specs
    spec_server.specs = spec_server._load_specifications()
    
    scenarios_request = {
        "jsonrpc": "2.0",
        "id": 3, 
        "method": "tools/call",
        "params": {
            "name": "get_scenarios",
            "arguments": {
                "domain": "task_manager",
                "include_constraints": True
            }
        }
    }
    
    response = await spec_server.handle_mcp_request(scenarios_request)
    if 'result' in response:
        print("✅ Get scenarios successful")
        content = response['result']['content'][0]['text']
        scenarios_data = eval(content)  # Convert string repr back to dict
        print(f"   Found {scenarios_data['total_count']} scenarios")
        print(f"   Has constraints: {'constraints' in scenarios_data}")
    else:
        print(f"❌ Get scenarios failed: {response.get('error', 'Unknown error')}")
    
    # Test 4: Validate scenario using AI
    print("\n🔍 Test 4: Validate Scenario with AI")
    
    test_scenario = {
        "name": "Delete completed tasks",
        "description": "User removes completed tasks from their list",
        "given": "User has completed tasks in their list",
        "when": "User selects 'Delete completed tasks'",
        "then": [
            "All completed tasks are removed",
            "Pending tasks remain unchanged",
            "User sees confirmation message"
        ]
    }
    
    validate_request = {
        "jsonrpc": "2.0",
        "id": 4,
        "method": "tools/call",
        "params": {
            "name": "validate_scenario",
            "arguments": {
                "scenario": test_scenario,
                "domain": "task_manager",
                "check_conflicts": True,
                "check_completeness": True
            }
        }
    }
    
    response = await spec_server.handle_mcp_request(validate_request)
    if 'result' in response:
        print("✅ Scenario validation successful")
        content = response['result']['content'][0]['text']
        print(f"   Validation result: {content[:200]}...")
    else:
        print(f"❌ Scenario validation failed: {response.get('error', 'Unknown error')}")
    
    # Test 5: Generate edge cases using AI
    print("\n🎯 Test 5: Generate Edge Cases")
    
    edge_cases_request = {
        "jsonrpc": "2.0",
        "id": 5,
        "method": "tools/call",
        "params": {
            "name": "generate_edge_cases",
            "arguments": {
                "domain": "task_manager",
                "edge_case_types": ["error", "boundary", "security"]
            }
        }
    }
    
    response = await spec_server.handle_mcp_request(edge_cases_request)
    if 'result' in response:
        print("✅ Edge case generation successful")
        content = response['result']['content'][0]['text']
        try:
            edge_cases = eval(content)
            print(f"   Generated {len(edge_cases)} edge cases")
            if edge_cases:
                print(f"   Example: {edge_cases[0].get('name', 'Unnamed')}")
        except:
            print(f"   Edge cases: {content[:100]}...")
    else:
        print(f"❌ Edge case generation failed: {response.get('error', 'Unknown error')}")
    
    # Test 6: Analyze coverage
    print("\n📊 Test 6: Analyze Coverage")
    
    coverage_request = {
        "jsonrpc": "2.0",
        "id": 6,
        "method": "tools/call",
        "params": {
            "name": "analyze_coverage",
            "arguments": {
                "domain": "task_manager",
                "suggest_missing": True,
                "coverage_goals": ["functional", "edge_cases", "error_handling"]
            }
        }
    }
    
    response = await spec_server.handle_mcp_request(coverage_request)
    if 'result' in response:
        print("✅ Coverage analysis successful")
        content = response['result']['content'][0]['text']
        print(f"   Coverage analysis: {content[:150]}...")
    else:
        print(f"❌ Coverage analysis failed: {response.get('error', 'Unknown error')}")
    
    # Test 7: List resources
    print("\n📚 Test 7: List Resources")
    resources_request = {
        "jsonrpc": "2.0",
        "id": 7,
        "method": "resources/list",
        "params": {}
    }
    
    response = await spec_server.handle_mcp_request(resources_request)
    resources = response['result']['resources']
    print(f"✅ Found {len(resources)} resources:")
    for resource in resources:
        print(f"   - {resource['name']}: {resource['uri']}")
    
    # Test 8: Read a resource
    print("\n📄 Test 8: Read Resource")
    read_resource_request = {
        "jsonrpc": "2.0",
        "id": 8,
        "method": "resources/read",
        "params": {
            "uri": "spec://templates/basic-scenario"
        }
    }
    
    response = await spec_server.handle_mcp_request(read_resource_request)
    if 'result' in response:
        content = response['result']['contents'][0]['text']
        print("✅ Resource read successful")
        print("Basic scenario template:")
        print(content[:200] + "...")
    
    print(f"\n🎉 Specification MCP Server test completed!")
    print(f"Server ready with {len(tools)} tools and {len(resources)} resources")


if __name__ == "__main__":
    asyncio.run(test_specification_mcp_server())