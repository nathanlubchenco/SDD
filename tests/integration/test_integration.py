#!/usr/bin/env python3
"""
Test integration of Docker MCP Server with existing handoff flow.

This demonstrates how to replace the bespoke Docker generation
with the new AI-driven MCP server.
"""

import asyncio
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.mcp_servers.docker_mcp_server import DockerMCPServer


async def test_integration_example():
    """Test integrating Docker MCP server with existing code analysis."""
    
    print("🔗 Testing Docker MCP Server Integration")
    
    # Initialize the Docker MCP server
    docker_server = DockerMCPServer()
    
    # Use existing code from a workspace for testing
    workspace_path = Path("workspaces/task_manager_clean")
    if not workspace_path.exists():
        print("❌ Test workspace not found")
        return
        
    # Read existing implementation
    with open(workspace_path / "task_management_system.py", "r") as f:
        impl_code = f.read()
    
    with open(workspace_path / "test_task_management_system.py", "r") as f:
        test_code = f.read()
    
    print("📊 Analyzing existing code...")
    
    # Step 1: Use existing dependency analysis
    analysis = _analyze_code_for_docker(impl_code, test_code, {})
    print(f"   Dependencies detected: {list(analysis['dependencies'])}")
    print(f"   Has web server: {analysis['has_web_server']}")
    print(f"   Has async: {analysis['has_async']}")
    
    # Step 2: Use MCP server to generate Docker configuration
    print("\n🐳 Generating Dockerfile with AI...")
    
    dockerfile_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "generate_dockerfile",
            "arguments": {
                "code_analysis": dict(analysis),  # Convert set to dict for JSON serialization
                "constraints": {
                    "security": ["non-root-user", "minimal-attack-surface"],
                    "performance": ["layer-caching", "multi-stage-build"]
                },
                "environment": "production",
                "optimization_goals": ["security", "performance"]
            }
        }
    }
    
    response = await docker_server.handle_mcp_request(dockerfile_request)
    
    if 'result' in response:
        dockerfile_content = response['result']['content'][0]['text']
        
        print("✅ AI-Generated Dockerfile:")
        print("=" * 50)
        print(dockerfile_content)
        print("=" * 50)
        
        # Step 3: Generate docker-compose
        print("\n📦 Generating docker-compose.yml...")
        
        compose_request = {
            "jsonrpc": "2.0", 
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "generate_docker_compose",
                "arguments": {
                    "services": [
                        {
                            "name": "task-manager",
                            "type": "web",
                            "dependencies": list(analysis['dependencies']),
                            "ports": analysis.get('ports', [8000])
                        }
                    ],
                    "networking": {"internal": True},
                    "volumes": ["data:/app/data"],
                    "environment": "production"
                }
            }
        }
        
        response = await docker_server.handle_mcp_request(compose_request)
        
        if 'result' in response:
            compose_content = response['result']['content'][0]['text']
            
            print("✅ AI-Generated docker-compose.yml:")
            print("=" * 50)
            print(compose_content)
            print("=" * 50)
        
        # Step 4: Save the generated files
        print("\n💾 Saving generated Docker files...")
        
        output_dir = workspace_path / "generated_docker"
        output_dir.mkdir(exist_ok=True)
        
        (output_dir / "Dockerfile.ai").write_text(dockerfile_content)
        if 'result' in response:
            (output_dir / "docker-compose.ai.yml").write_text(compose_content)
        
        print(f"✅ Files saved to {output_dir}")
        
        # Step 5: Compare with old generation
        old_dockerfile = workspace_path / "Dockerfile"
        if old_dockerfile.exists():
            print("\n🔍 Comparing with old template-based generation:")
            with open(old_dockerfile, "r") as f:
                old_content = f.read()
            
            print(f"   Old Dockerfile size: {len(old_content)} chars")
            print(f"   AI Dockerfile size: {len(dockerfile_content)} chars")
            print(f"   Improvement: {len(dockerfile_content) - len(old_content):+d} chars")
            
            # Count optimization features
            ai_features = sum([
                "multi-stage" in dockerfile_content.lower() or "as builder" in dockerfile_content.lower(),
                "non-root" in dockerfile_content.lower() or "adduser" in dockerfile_content.lower(),
                "healthcheck" in dockerfile_content.lower(),
                "pythondontwritebytecode" in dockerfile_content.lower(),
                "security" in dockerfile_content.lower()
            ])
            
            old_features = sum([
                "multi-stage" in old_content.lower() or "as builder" in old_content.lower(),
                "non-root" in old_content.lower() or "adduser" in old_content.lower(),
                "healthcheck" in old_content.lower(),
                "pythondontwritebytecode" in old_content.lower(),
                "security" in old_content.lower()
            ])
            
            print(f"   AI optimization features: {ai_features}/5")
            print(f"   Old optimization features: {old_features}/5")
    
    else:
        print(f"❌ Dockerfile generation failed: {response.get('error', 'Unknown error')}")
    
    print(f"\n🎉 Integration test completed!")
    print(f"This demonstrates how AI-driven MCP servers can replace bespoke templates.")


if __name__ == "__main__":
    asyncio.run(test_integration_example())