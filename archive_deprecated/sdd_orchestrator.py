from pathlib import Path
from typing import Dict
from mcp_servers.specification_server import SpecificationMCPServer
from mcp_servers.implementation_server import ImplementationMCPServer
from mcp_servers.monitoring_server import MonitoringMCPServer


class SDDOrchestrator:
    """Orchestrates the specification to implementation flow"""

    def __init__(self):
        # Initialize MCP servers
        self.spec_server = SpecificationMCPServer(Path("./specs"))
        self.impl_server = ImplementationMCPServer(Path("./workspaces"))
        self.monitor_server = MonitoringMCPServer()

    async def implement_feature(self, feature_request: str, domain: str = None) -> Dict:
        """Complete feature implementation flow"""

        print(f"🚀 Starting implementation for: {feature_request}")

        # Derive domain from feature_request if not provided
        if not domain:
            # Convert feature request to a valid domain name (snake_case)
            import re
            domain = re.sub(r'[^a-zA-Z0-9]+', '_', feature_request).lower().strip('_')
            if not domain or domain[0].isdigit():
                domain = f"service_{domain}"

        # Phase 1: Load or create specification
        print(f"📝 Phase 1: Loading specification for domain: {domain}...")
        spec_result = await self._load_specification(domain)

        # Phase 2: Implementation
        print("🔨 Phase 2: Generating implementation...")
        impl_result = await self._implement_specification(spec_result)

        # Phase 3: Verification
        print("✅ Phase 3: Verifying constraints...")
        verification = await self._verify_implementation(impl_result)

        # Phase 4: Monitoring Setup
        print("📊 Phase 4: Setting up monitoring...")
        monitoring = await self._setup_monitoring(impl_result)

        return {
            "feature_request": feature_request,
            "specification": spec_result,
            "implementation": impl_result,
            "verification": verification,
            "monitoring": monitoring,
            "status": "completed"
        }

    async def _load_specification(self, domain: str) -> Dict:
        """Load specification from spec server"""
        # Try to get existing scenarios
        scenarios = await self.spec_server.get_scenarios(domain)
        
        if "error" in scenarios:
            # Create a basic specification structure
            return {
                "domain": domain,
                "scenarios": [],
                "constraints": {},
                "status": "new"
            }
        
        return scenarios

    async def _implement_specification(self, spec: Dict) -> Dict:
        """Implement the specification using implementation server"""
        
        # Create workspace
        workspace = await self.impl_server.create_workspace(
            project_name=spec.get("domain", "unknown"),
            template="microservice"
        )

        # Generate implementation
        implementation = await self.impl_server.generate_implementation(
            workspace["workspace_id"],
            spec
        )

        return {
            "workspace_id": workspace["workspace_id"],
            "implementation": implementation,
            "specification": spec
        }

    async def _verify_implementation(self, impl_result: Dict) -> Dict:
        """Verify implementation meets all constraints"""

        workspace_id = impl_result["workspace_id"]
        spec = impl_result["specification"]
        constraints = spec.get("constraints", {})

        # Verify constraints using implementation server
        verification = await self.impl_server.verify_constraints(
            workspace_id,
            constraints
        )

        return verification

    async def _setup_monitoring(self, impl_result: Dict) -> Dict:
        """Set up monitoring for the implementation"""
        
        workspace_id = impl_result["workspace_id"]
        
        # Get initial health status
        health = await self.monitor_server.get_health_status(workspace_id)
        
        # Set up predictive monitoring
        predictions = await self.monitor_server.predict_failures(workspace_id)
        
        return {
            "workspace_id": workspace_id,
            "health_status": health,
            "predictions": predictions,
            "monitoring_enabled": True
        }

    async def get_system_status(self) -> Dict:
        """Get overall system status"""
        return {
            "spec_server": {"status": "active", "name": self.spec_server.name},
            "impl_server": {"status": "active", "name": self.impl_server.name},
            "monitor_server": {"status": "active", "name": self.monitor_server.name},
            "active_workspaces": len(self.impl_server.active_workspaces)
        }