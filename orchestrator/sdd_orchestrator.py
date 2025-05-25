from pathlib import Path
from typing import Dict
from mcp_servers.specification_server import SpecificationMCPServer
from mcp_servers.implementation_server import ImplementationMCPServer
from mcp_servers.monitoring_server import MonitoringMCPServer
from orchestrator.claude_integration import ClaudeWithMCP


class SDDOrchestrator:
    """Orchestrates the specification to implementation flow"""

    def __init__(self):
        # Initialize MCP servers
        self.spec_server = SpecificationMCPServer(Path("./specs"))
        self.impl_server = ImplementationMCPServer(Path("./workspaces"))
        self.monitor_server = MonitoringMCPServer()

        # Initialize AI agents with MCP access
        self.claude = ClaudeWithMCP(
            servers=[self.spec_server, self.impl_server, self.monitor_server]
        )

    async def implement_feature(self, feature_request: str) -> Dict:
        """Complete feature implementation flow"""

        print(f"🚀 Starting implementation for: {feature_request}")

        # Phase 1: Specification Generation
        print("📝 Phase 1: Generating specifications...")
        spec_result = await self._generate_specification(feature_request)

        # Phase 2: Human Review
        print("👀 Phase 2: Human review...")
        approved_spec = await self._human_review(spec_result)

        # Phase 3: Implementation
        print("🔨 Phase 3: Generating implementation...")
        impl_result = await self._implement_specification(approved_spec)

        # Phase 4: Verification
        print("✅ Phase 4: Verifying constraints...")
        verification = await self._verify_implementation(impl_result)

        # Phase 5: Optimization (if needed)
        if verification.get("constraints_failed"):
            print("🔧 Phase 5: Optimizing implementation...")
            optimization = await self._optimize_implementation(impl_result, verification)
            return optimization

        return impl_result

    async def _generate_specification(self, feature_request: str) -> Dict:
        """Generate specification from feature request"""

        # First, analyze existing system
        system_context = await self.claude.execute(
            prompt=f"""
            Analyze the current system to understand context for: {feature_request}

            Use the get_scenarios tool to retrieve existing scenarios for related domains.
            Identify which domains will be affected.
            """,
            tools=["get_scenarios", "analyze_coverage"]
        )

        # Generate new scenarios
        new_scenarios = await self.claude.execute(
            prompt=f"""
            Generate comprehensive scenarios for: {feature_request}

            Context: {system_context}

            Include:
            1. Happy path scenarios
            2. Error cases
            3. Edge cases
            4. Performance scenarios
            5. Security scenarios

            Use the validate_scenario tool to check each scenario.
            """,
            tools=["validate_scenario", "get_scenario_templates"]
        )

        # Generate constraints
        constraints = await self.claude.execute(
            prompt=f"""
            Define constraints for: {feature_request}

            Based on the scenarios: {new_scenarios}

            Include:
            1. Performance requirements
            2. Security requirements
            3. Scalability requirements
            4. Data consistency requirements
            """,
            tools=["get_constraints"]
        )

        return {
            "feature": feature_request,
            "scenarios": new_scenarios,
            "constraints": constraints,
            "impacted_domains": system_context.get("impacted_domains")
        }

    async def _implement_specification(self, spec: Dict) -> Dict:
        """Implement the approved specification"""

        # Create workspace
        workspace = await self.impl_server.create_workspace(
            project_name=spec["feature"].replace(" ", "_"),
            template="microservice"
        )

        # Generate implementation
        implementation = await self.claude.execute(
            prompt=f"""
            Generate complete implementation for specification: {spec}

            Use the generate_implementation tool to create:
            1. Data models
            2. API endpoints
            3. Business logic
            4. Tests
            5. Integration points

            Ensure all scenarios are covered.
            """,
            tools=["generate_implementation", "run_tests"],
            context={"workspace_id": workspace["workspace_id"]}
        )

        # Run initial tests
        test_results = await self.impl_server.run_tests(
            workspace_id=workspace["workspace_id"]
        )

        return {
            "workspace_id": workspace["workspace_id"],
            "implementation": implementation,
            "test_results": test_results,
            "specification": spec
        }

    async def _verify_implementation(self, impl_result: Dict) -> Dict:
        """Verify implementation meets all constraints"""

        verification = await self.claude.execute(
            prompt=f"""
            Verify the implementation meets all constraints.

            Specification: {impl_result['specification']}
            Test Results: {impl_result['test_results']}

            Use verify_constraints tool to check:
            1. All functional scenarios pass
            2. Performance constraints are met
            3. Security requirements are satisfied
            4. Scalability targets are achieved
            """,
            tools=["verify_constraints"],
            context={"workspace_id": impl_result["workspace_id"]}
        )

        return verification

    async def _optimize_implementation(self, impl_result: Dict,
                                      verification: Dict) -> Dict:
        """Optimize implementation to meet failed constraints"""

        optimization_result = await self.claude.execute(
            prompt=f"""
            Optimize the implementation to meet failed constraints.

            Failed constraints: {verification['constraints_failed']}
            Current metrics: {verification['performance_metrics']}

            Use optimize_implementation tool to:
            1. Identify bottlenecks
            2. Apply optimizations
            3. Re-verify constraints
            4. Iterate until all constraints pass
            """,
            tools=["optimize_implementation", "verify_constraints"],
            context={"workspace_id": impl_result["workspace_id"]}
        )

        return optimization_result