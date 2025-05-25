import json
import asyncio
from typing import Dict, List, Optional
from pathlib import Path
import yaml
from mcp.server import MCPServer, Tool, Resource
from mcp.types import TextContent, ImageContent


class SpecificationMCPServer(MCPServer):
    """MCP Server for managing system specifications"""

    def __init__(self, spec_directory: Path):
        super().__init__("specification-server")
        self.spec_dir = spec_directory
        self.specs = self._load_specifications()
        self.scenario_cache = {}

    def _load_specifications(self) -> Dict:
        """Load all specification files"""
        specs = {}
        for spec_file in self.spec_dir.glob("**/*.yaml"):
            with open(spec_file) as f:
                domain = spec_file.stem
                specs[domain] = yaml.safe_load(f)
        return specs

    @Tool(
        name="get_scenarios",
        description="Retrieve scenarios for a specific domain or feature",
        parameters={
            "domain": {"type": "string", "description": "Domain name (e.g., 'checkout', 'inventory')"},
            "feature": {"type": "string", "description": "Optional specific feature", "required": False},
            "include_constraints": {"type": "boolean", "description": "Include related constraints", "default": True}
        }
    )
    async def get_scenarios(self, domain: str, feature: Optional[str] = None,
                            include_constraints: bool = True) -> Dict:
        """Retrieve scenarios with full context"""

        if domain not in self.specs:
            return {"error": f"Domain '{domain}' not found"}

        domain_spec = self.specs[domain]
        scenarios = domain_spec.get("scenarios", [])

        # Filter by feature if specified
        if feature:
            scenarios = [s for s in scenarios if s.get("feature") == feature]

        result = {
            "domain": domain,
            "scenarios": scenarios,
            "total_count": len(scenarios)
        }

        # Include constraints if requested
        if include_constraints:
            result["constraints"] = domain_spec.get("constraints", {})
            result["global_constraints"] = self.specs.get("global", {}).get("constraints", {})

        return result

    @Tool(
        name="validate_scenario",
        description="Validate a new scenario against existing specifications",
        parameters={
            "scenario": {"type": "object", "description": "Scenario to validate"},
            "domain": {"type": "string", "description": "Target domain"},
            "check_conflicts": {"type": "boolean", "default": True},
            "check_completeness": {"type": "boolean", "default": True}
        }
    )
    async def validate_scenario(self, scenario: Dict, domain: str,
                                check_conflicts: bool = True,
                                check_completeness: bool = True) -> Dict:
        """Validate scenario for conflicts and completeness"""

        validation_result = {
            "valid": True,
            "conflicts": [],
            "warnings": [],
            "suggestions": []
        }

        if check_conflicts:
            conflicts = await self._check_conflicts(scenario, domain)
            validation_result["conflicts"] = conflicts
            validation_result["valid"] = len(conflicts) == 0

        if check_completeness:
            completeness = await self._check_completeness(scenario, domain)
            validation_result["warnings"].extend(completeness["warnings"])
            validation_result["suggestions"].extend(completeness["suggestions"])

        return validation_result

    async def _check_conflicts(self, scenario: Dict, domain: str) -> List[Dict]:
        """Check for conflicts with existing scenarios"""
        conflicts = []
        existing_scenarios = self.specs.get(domain, {}).get("scenarios", [])

        for existing in existing_scenarios:
            # Check for duplicate names
            if existing.get("name") == scenario.get("name"):
                conflicts.append({
                    "type": "duplicate_name",
                    "message": f"Scenario '{scenario['name']}' already exists",
                    "existing_scenario": existing
                })

            # Check for conflicting behaviors
            if self._scenarios_conflict(scenario, existing):
                conflicts.append({
                    "type": "behavioral_conflict",
                    "message": "Conflicting behavior detected",
                    "scenario1": scenario["name"],
                    "scenario2": existing["name"],
                    "details": self._explain_conflict(scenario, existing)
                })
        
        return conflicts

    @Tool(
        name="generate_test_suite",
        description="Generate test suite from scenarios",
        parameters={
            "domain": {"type": "string", "description": "Domain to generate tests for"},
            "language": {"type": "string", "description": "Programming language", "default": "python"},
            "framework": {"type": "string", "description": "Test framework", "default": "pytest"}
        }
    )
    async def generate_test_suite(self, domain: str, language: str = "python",
                                 framework: str = "pytest") -> Dict:
        """Generate executable tests from scenarios"""

        scenarios = await self.get_scenarios(domain)
        if "error" in scenarios:
            return scenarios

        test_code = self._generate_test_code(
            scenarios["scenarios"],
            language,
            framework
        )

        return {
            "domain": domain,
            "language": language,
            "framework": framework,
            "test_code": test_code,
            "test_count": len(scenarios["scenarios"])
        }

    @Tool(
        name="analyze_coverage",
        description="Analyze scenario coverage for edge cases",
        parameters={
            "domain": {"type": "string", "description": "Domain to analyze"},
            "suggest_missing": {"type": "boolean", "description": "Suggest missing scenarios", "default": True}
        }
    )
    async def analyze_coverage(self, domain: str, suggest_missing: bool = True) -> Dict:
        """Analyze test coverage and suggest missing scenarios"""

        scenarios = await self.get_scenarios(domain)
        if "error" in scenarios:
            return scenarios

        analysis = {
            "domain": domain,
            "total_scenarios": len(scenarios["scenarios"]),
            "coverage_analysis": self._analyze_coverage_gaps(scenarios["scenarios"]),
            "edge_cases_covered": [],
            "edge_cases_missing": []
        }

        if suggest_missing:
            analysis["suggested_scenarios"] = await self._suggest_missing_scenarios(
                scenarios["scenarios"],
                domain
            )

        return analysis

    @Resource(
        name="scenario_templates",
        description="Templates for common scenario patterns"
    )
    async def get_scenario_templates(self) -> List[Dict]:
        """Provide scenario templates"""
        return [
            {
                "name": "CRUD Operations",
                "template": {
                    "create": {"given": "...", "when": "create X", "then": "X exists"},
                    "read": {"given": "X exists", "when": "read X", "then": "return X"},
                    "update": {"given": "X exists", "when": "update X", "then": "X updated"},
                    "delete": {"given": "X exists", "when": "delete X", "then": "X not exists"}
                }
            },
            {
                "name": "Error Handling",
                "template": {
                    "not_found": {"given": "X not exists", "when": "access X", "then": "404 error"},
                    "invalid_input": {"given": "...", "when": "invalid input", "then": "400 error"},
                    "unauthorized": {"given": "no auth", "when": "access protected", "then": "401 error"}
                }
            }
        ]

    def _generate_test_code(self, scenarios: List[Dict], language: str, framework: str) -> str:
        """Generate actual test code from scenarios"""
        if language == "python" and framework == "pytest":
            return self._generate_pytest_code(scenarios)
        # Add other language/framework combinations

    def _generate_pytest_code(self, scenarios: List[Dict]) -> str:
        """Generate pytest code from scenarios"""
        code = """import pytest
from your_app import api_client

class TestGeneratedScenarios:
"""

        for scenario in scenarios:
            test_name = f"test_{scenario['name'].lower().replace(' ', '_')}"
            code += f"""
    def {test_name}(self, api_client):
        \"\"\"Test: {scenario['name']}\"\"\"
        # Given: {scenario.get('given', 'Initial state')}
        {self._generate_given_code(scenario.get('given'))}

        # When: {scenario['when']}
        response = {self._generate_when_code(scenario['when'])}

        # Then: {scenario['then']}
        {self._generate_then_code(scenario['then'])}
"""

        return code