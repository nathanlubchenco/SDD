"""
Real MCP-enabled SDD Orchestrator.

This orchestrator uses actual MCP protocol calls to coordinate 
AI-driven specification and implementation services.
"""

import asyncio
import json
from pathlib import Path
from typing import Dict, List, Any, Optional

from mcp_servers.specification_mcp_server import SpecificationMCPServer
from mcp_servers.docker_mcp_server import DockerMCPServer
from mcp_servers.implementation_server import ImplementationMCPServer
from mcp_servers.monitoring_server import MonitoringMCPServer


class MCPOrchestrator:
    """
    Real MCP-enabled orchestrator for SDD workflow.
    
    This replaces direct Python calls with proper MCP protocol
    communication, enabling true LLM tool calling architecture.
    """

    def __init__(self):
        # Initialize real MCP servers
        self.spec_server = SpecificationMCPServer(Path("./specs"))
        self.docker_server = DockerMCPServer()
        self.impl_server = ImplementationMCPServer(Path("./workspaces"))
        self.monitor_server = MonitoringMCPServer()
        
        # Initialize all servers
        asyncio.create_task(self._initialize_servers())

    async def _initialize_servers(self):
        """Initialize all MCP servers."""
        try:
            await self.spec_server.start_server()
            await self.docker_server.start_server() 
            await self.impl_server.start_server()
            await self.monitor_server.start_server()
            print("🔧 All MCP servers initialized")
        except Exception as e:
            print(f"⚠️ Server initialization warning: {e}")

    async def implement_feature(self, feature_request: str, domain: str = None) -> Dict:
        """Complete feature implementation flow using MCP protocol."""

        print(f"🚀 Starting MCP-enabled implementation for: {feature_request}")

        # Derive domain from feature_request if not provided
        if not domain:
            import re
            domain = re.sub(r'[^a-zA-Z0-9]+', '_', feature_request).lower().strip('_')
            if not domain or domain[0].isdigit():
                domain = f"service_{domain}"

        try:
            # Phase 1: Load or create specification using MCP
            print(f"📝 Phase 1: Loading specification for domain: {domain}...")
            spec_result = await self._load_specification_mcp(domain)

            # Phase 2: Enhance specification with AI
            print("🧠 Phase 2: Enhancing specification with AI...")
            enhanced_spec = await self._enhance_specification_mcp(spec_result, feature_request)

            # Phase 3: Generate implementation using MCP
            print("🔨 Phase 3: Generating implementation...")
            impl_result = await self._implement_specification_mcp(enhanced_spec)

            # Phase 4: Generate Docker configuration using MCP
            print("🐳 Phase 4: Generating Docker configuration...")
            docker_result = await self._generate_docker_mcp(impl_result)

            # Phase 5: Verification
            print("✅ Phase 5: Verifying implementation...")
            verification = await self._verify_implementation_mcp(impl_result)

            # Phase 6: Setup monitoring
            print("📊 Phase 6: Setting up monitoring...")
            monitoring = await self._setup_monitoring_mcp(impl_result)

            return {
                "feature_request": feature_request,
                "domain": domain,
                "specification": enhanced_spec,
                "implementation": impl_result,
                "docker": docker_result,
                "verification": verification,
                "monitoring": monitoring,
                "status": "completed",
                "mcp_enabled": True
            }

        except Exception as e:
            print(f"❌ Implementation failed: {e}")
            return {
                "feature_request": feature_request,
                "domain": domain,
                "status": "failed",
                "error": str(e),
                "mcp_enabled": True
            }

    async def _load_specification_mcp(self, domain: str) -> Dict:
        """Load specification using MCP protocol."""
        
        request = {
            "jsonrpc": "2.0",
            "id": "load_spec_1",
            "method": "tools/call",
            "params": {
                "name": "get_scenarios",
                "arguments": {
                    "domain": domain,
                    "include_constraints": True
                }
            }
        }

        response = await self.spec_server.handle_mcp_request(request)
        
        if 'result' in response:
            # Parse the response content (returned as text)
            content = response['result']['content'][0]['text']
            try:
                spec_data = eval(content)  # Convert string repr to dict
                
                if "error" in spec_data:
                    # Create basic specification structure
                    return {
                        "domain": domain,
                        "scenarios": [],
                        "constraints": {},
                        "status": "new"
                    }
                
                spec_data["status"] = "loaded"
                return spec_data
                
            except Exception as e:
                print(f"⚠️ Spec parsing error: {e}")
                return {
                    "domain": domain,
                    "scenarios": [],
                    "constraints": {},
                    "status": "parse_error"
                }
        else:
            print(f"⚠️ Spec loading error: {response.get('error', 'Unknown error')}")
            return {
                "domain": domain,
                "scenarios": [],
                "constraints": {},
                "status": "error"
            }

    async def _enhance_specification_mcp(self, spec: Dict, feature_request: str) -> Dict:
        """Enhance specification using AI through MCP."""
        
        scenarios = spec.get("scenarios", [])
        if not scenarios:
            # Generate initial scenarios if none exist
            print("🎯 Generating initial scenarios for new specification...")
            
            # Use basic scenario structure for new domains
            basic_scenario = {
                "name": f"Basic {feature_request} functionality",
                "description": f"Core functionality for {feature_request}",
                "given": "System is in normal state", 
                "when": f"User performs {feature_request}",
                "then": ["Operation completes successfully", "System returns expected result"]
            }
            
            spec["scenarios"] = [basic_scenario]
            spec["status"] = "enhanced"
            return spec

        # Enhance existing scenarios if present
        print("🔍 Analyzing scenario coverage...")
        
        coverage_request = {
            "jsonrpc": "2.0",
            "id": "coverage_1",
            "method": "tools/call",
            "params": {
                "name": "analyze_coverage",
                "arguments": {
                    "domain": spec["domain"],
                    "suggest_missing": True,
                    "coverage_goals": ["functional", "edge_cases", "error_handling"]
                }
            }
        }

        coverage_response = await self.spec_server.handle_mcp_request(coverage_request)
        
        if 'result' in coverage_response:
            print("✅ Coverage analysis completed")

        # Generate edge cases to improve coverage
        print("🎯 Generating edge case scenarios...")
        
        edge_cases_request = {
            "jsonrpc": "2.0",
            "id": "edge_cases_1", 
            "method": "tools/call",
            "params": {
                "name": "generate_edge_cases",
                "arguments": {
                    "domain": spec["domain"],
                    "edge_case_types": ["error", "boundary", "security"]
                }
            }
        }

        edge_response = await self.spec_server.handle_mcp_request(edge_cases_request)
        
        if 'result' in edge_response:
            try:
                content = edge_response['result']['content'][0]['text']
                edge_cases = eval(content)
                if isinstance(edge_cases, list) and edge_cases:
                    spec["scenarios"].extend(edge_cases[:3])  # Add up to 3 edge cases
                    print(f"✅ Added {len(edge_cases[:3])} edge case scenarios")
            except Exception as e:
                print(f"⚠️ Edge case parsing error: {e}")

        spec["status"] = "enhanced"
        return spec

    async def _implement_specification_mcp(self, spec: Dict) -> Dict:
        """Implement specification using MCP (still uses old server for now)."""
        
        # Note: ImplementationMCPServer is not converted to real MCP yet
        # For now, use the existing direct call approach
        
        workspace = await self.impl_server.create_workspace(
            project_name=spec.get("domain", "unknown"),
            template="microservice" 
        )

        implementation = await self.impl_server.generate_implementation(
            workspace["workspace_id"],
            spec
        )

        return {
            "workspace_id": workspace["workspace_id"],
            "implementation": implementation,
            "specification": spec,
            "mcp_generated": False  # Mark as not yet MCP-generated
        }

    async def _generate_docker_mcp(self, impl_result: Dict) -> Dict:
        """Generate Docker configuration using MCP protocol."""
        
        # First analyze the implementation code for dependencies
        workspace_id = impl_result["workspace_id"]
        workspace_path = self.impl_server.active_workspaces[workspace_id]["path"]
        
        # Read implementation files
        try:
            impl_files = list(workspace_path.glob("*.py"))
            if not impl_files:
                raise Exception("No implementation files found")
                
            impl_file = [f for f in impl_files if not f.name.startswith("test_") and f.name != "__init__.py"][0]
            test_files = [f for f in impl_files if f.name.startswith("test_")]
            
            with open(impl_file, 'r') as f:
                impl_code = f.read()
                
            test_code = ""
            if test_files:
                with open(test_files[0], 'r') as f:
                    test_code = f.read()

        except Exception as e:
            print(f"⚠️ Could not read implementation files: {e}")
            return {"status": "failed", "error": str(e)}

        # Analyze dependencies using MCP
        print("🔍 Analyzing code dependencies...")
        
        analyze_request = {
            "jsonrpc": "2.0",
            "id": "analyze_deps_1",
            "method": "tools/call",
            "params": {
                "name": "analyze_dependencies",
                "arguments": {
                    "implementation_code": impl_code,
                    "test_code": test_code
                }
            }
        }

        analyze_response = await self.docker_server.handle_mcp_request(analyze_request)
        
        if 'result' not in analyze_response:
            print(f"⚠️ Dependency analysis failed: {analyze_response.get('error', 'Unknown error')}")
            return {"status": "failed", "error": "Dependency analysis failed"}

        try:
            analysis_content = analyze_response['result']['content'][0]['text']
            code_analysis = eval(analysis_content)
        except Exception as e:
            print(f"⚠️ Analysis parsing error: {e}")
            return {"status": "failed", "error": f"Analysis parsing error: {e}"}

        # Generate Dockerfile using MCP
        print("🐳 Generating optimized Dockerfile...")
        
        dockerfile_request = {
            "jsonrpc": "2.0",
            "id": "dockerfile_1",
            "method": "tools/call",
            "params": {
                "name": "generate_dockerfile",
                "arguments": {
                    "code_analysis": code_analysis,
                    "constraints": {
                        "security": ["non-root-user", "minimal-attack-surface"],
                        "performance": ["layer-caching", "multi-stage-build"]
                    },
                    "environment": "production",
                    "optimization_goals": ["security", "performance", "size"]
                }
            }
        }

        dockerfile_response = await self.docker_server.handle_mcp_request(dockerfile_request)
        
        if 'result' not in dockerfile_response:
            print(f"⚠️ Dockerfile generation failed: {dockerfile_response.get('error', 'Unknown error')}")
            return {"status": "failed", "error": "Dockerfile generation failed"}

        dockerfile_content = dockerfile_response['result']['content'][0]['text']

        # Generate docker-compose using MCP
        print("📦 Generating docker-compose configuration...")
        
        compose_request = {
            "jsonrpc": "2.0",
            "id": "compose_1",
            "method": "tools/call", 
            "params": {
                "name": "generate_docker_compose",
                "arguments": {
                    "services": [
                        {
                            "name": impl_result["specification"]["domain"],
                            "type": "web" if code_analysis.get("has_web_server") else "service",
                            "dependencies": list(code_analysis.get("dependencies", [])),
                            "ports": code_analysis.get("ports", [8000])
                        }
                    ],
                    "networking": {"internal": True},
                    "volumes": ["data:/app/data"],
                    "environment": "production"
                }
            }
        }

        compose_response = await self.docker_server.handle_mcp_request(compose_request)
        
        compose_content = ""
        if 'result' in compose_response:
            compose_content = compose_response['result']['content'][0]['text']
        else:
            print(f"⚠️ Compose generation warning: {compose_response.get('error', 'Unknown error')}")

        # Save Docker files to workspace
        (workspace_path / "Dockerfile.mcp").write_text(dockerfile_content)
        if compose_content:
            (workspace_path / "docker-compose.mcp.yml").write_text(compose_content)

        return {
            "dockerfile": dockerfile_content,
            "docker_compose": compose_content,
            "code_analysis": code_analysis,
            "workspace_path": str(workspace_path),
            "status": "completed",
            "mcp_generated": True
        }

    async def _verify_implementation_mcp(self, impl_result: Dict) -> Dict:
        """Verify implementation using MCP (placeholder for now)."""
        
        workspace_id = impl_result["workspace_id"]
        spec = impl_result["specification"]
        constraints = spec.get("constraints", {})

        # For now, use existing verification (not yet converted to MCP)
        verification = await self.impl_server.verify_constraints(
            workspace_id,
            constraints
        )

        verification["mcp_verified"] = False  # Mark as not yet MCP-verified
        return verification

    async def _setup_monitoring_mcp(self, impl_result: Dict) -> Dict:
        """Setup monitoring using MCP (placeholder for now)."""
        
        workspace_id = impl_result["workspace_id"]
        
        # For now, use existing monitoring (not yet converted to MCP)
        health = await self.monitor_server.get_health_status(workspace_id)
        predictions = await self.monitor_server.predict_failures(workspace_id)
        
        return {
            "workspace_id": workspace_id,
            "health_status": health,
            "predictions": predictions,
            "monitoring_enabled": True,
            "mcp_monitored": False  # Mark as not yet MCP-monitored
        }

    async def get_system_status(self) -> Dict:
        """Get system status from all MCP servers."""
        
        status = {
            "orchestrator_type": "MCP-enabled",
            "servers": {}
        }

        # Get status from each MCP server
        for server_name, server in [
            ("specification", self.spec_server),
            ("docker", self.docker_server), 
            ("implementation", self.impl_server),
            ("monitoring", self.monitor_server)
        ]:
            try:
                # Try to get server info via MCP
                init_request = {
                    "jsonrpc": "2.0",
                    "id": f"status_{server_name}",
                    "method": "initialize",
                    "params": {"protocolVersion": "2024-11-05", "capabilities": {}}
                }
                
                response = await server.handle_mcp_request(init_request)
                
                if 'result' in response:
                    status["servers"][server_name] = {
                        "status": "active",
                        "name": response['result']['serverInfo']['name'],
                        "version": response['result']['serverInfo'].get('version', '1.0.0'),
                        "mcp_enabled": True
                    }
                else:
                    status["servers"][server_name] = {
                        "status": "error", 
                        "mcp_enabled": False,
                        "error": response.get('error', 'Unknown error')
                    }
                    
            except Exception as e:
                status["servers"][server_name] = {
                    "status": "error",
                    "mcp_enabled": False,
                    "error": str(e)
                }

        # Add workspace info
        if hasattr(self.impl_server, 'active_workspaces'):
            status["active_workspaces"] = len(self.impl_server.active_workspaces)
        
        return status

    async def list_available_tools(self) -> Dict[str, List[Dict]]:
        """List all available MCP tools across servers."""
        
        tools_by_server = {}
        
        for server_name, server in [
            ("specification", self.spec_server),
            ("docker", self.docker_server),
            ("implementation", self.impl_server),
            ("monitoring", self.monitor_server)
        ]:
            tools_request = {
                "jsonrpc": "2.0",
                "id": f"tools_{server_name}",
                "method": "tools/list",
                "params": {}
            }
            
            try:
                response = await server.handle_mcp_request(tools_request)
                if 'result' in response:
                    tools_by_server[server_name] = response['result']['tools']
                else:
                    tools_by_server[server_name] = []
            except Exception as e:
                tools_by_server[server_name] = [{"error": str(e)}]
        
        return tools_by_server

    async def call_mcp_tool(self, server_name: str, tool_name: str, arguments: Dict) -> Dict:
        """Call any MCP tool by name."""
        
        server_map = {
            "specification": self.spec_server,
            "docker": self.docker_server,
            "implementation": self.impl_server,
            "monitoring": self.monitor_server
        }
        
        if server_name not in server_map:
            return {"error": f"Unknown server: {server_name}"}
        
        server = server_map[server_name]
        
        request = {
            "jsonrpc": "2.0",
            "id": f"call_{tool_name}",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        try:
            response = await server.handle_mcp_request(request)
            return response
        except Exception as e:
            return {"error": str(e)}

    def __str__(self):
        return f"MCPOrchestrator(4 MCP servers: specification, docker, implementation, monitoring)"