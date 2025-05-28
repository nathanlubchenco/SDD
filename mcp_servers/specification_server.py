import json
import asyncio
from typing import Dict, List, Optional
from pathlib import Path
import yaml


class SpecificationMCPServer:
    """MCP Server for managing system specifications"""

    def __init__(self, spec_directory: Path):
        self.name = "specification-server"
        self.spec_dir = spec_directory
        self.spec_dir.mkdir(parents=True, exist_ok=True)
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
    
    def _scenarios_conflict(self, scenario1: Dict, scenario2: Dict) -> bool:
        """Check if two scenarios have conflicting behaviors"""
        # Simple heuristic: same 'when' action but different 'then' outcomes
        when1 = scenario1.get('when', '').lower()
        when2 = scenario2.get('when', '').lower()
        
        if when1 == when2:
            then1 = str(scenario1.get('then', [])).lower()
            then2 = str(scenario2.get('then', [])).lower()
            return then1 != then2
        
        return False
    
    def _explain_conflict(self, scenario1: Dict, scenario2: Dict) -> str:
        """Explain why two scenarios conflict"""
        return f"Same action '{scenario1.get('when')}' produces different outcomes"
    
    async def _check_completeness(self, scenario: Dict, domain: str) -> Dict:
        """Check scenario completeness"""
        warnings = []
        suggestions = []
        
        if not scenario.get('given'):
            warnings.append("No 'given' conditions specified")
            suggestions.append("Add preconditions to make the scenario more specific")
        
        if not scenario.get('then'):
            warnings.append("No 'then' outcomes specified")
            suggestions.append("Add expected outcomes to verify behavior")
        
        return {"warnings": warnings, "suggestions": suggestions}
    
    def _analyze_coverage_gaps(self, scenarios: List[Dict]) -> Dict:
        """Analyze coverage gaps in scenarios"""
        operations = set()
        error_cases = 0
        
        for scenario in scenarios:
            when_text = scenario.get('when', '').lower()
            if 'create' in when_text:
                operations.add('create')
            elif 'update' in when_text or 'modify' in when_text:
                operations.add('update')
            elif 'delete' in when_text:
                operations.add('delete')
            elif 'read' in when_text or 'get' in when_text or 'list' in when_text:
                operations.add('read')
            
            then_text = str(scenario.get('then', [])).lower()
            if 'error' in then_text:
                error_cases += 1
        
        return {
            "crud_operations_covered": list(operations),
            "error_scenarios": error_cases,
            "coverage_percentage": min(100, (len(operations) * 25))  # Basic CRUD = 100%
        }
    
    async def _suggest_missing_scenarios(self, scenarios: List[Dict], domain: str) -> List[Dict]:
        """Suggest missing scenarios based on coverage analysis"""
        analysis = self._analyze_coverage_gaps(scenarios)
        suggestions = []
        
        crud_ops = ['create', 'read', 'update', 'delete']
        covered = analysis['crud_operations_covered']
        
        for op in crud_ops:
            if op not in covered:
                suggestions.append({
                    "name": f"{op.title()} operation scenario",
                    "reason": f"No {op} scenarios detected",
                    "template": {
                        "when": f"User performs {op} operation",
                        "then": [f"Operation {op} succeeds"]
                    }
                })
        
        if analysis['error_scenarios'] == 0:
            suggestions.append({
                "name": "Error handling scenarios",
                "reason": "No error scenarios detected", 
                "template": {
                    "when": "Invalid input provided",
                    "then": ["Appropriate error message returned"]
                }
            })
        
        return suggestions
    
    def _generate_given_code(self, given: Optional[str]) -> str:
        """Generate setup code from given condition"""
        if not given:
            return "# Setup initial state"
        return f"# Setup: {given}"
    
    def _generate_when_code(self, when: str) -> str:
        """Generate action code from when condition"""
        return f"api_client.action('{when}')"
    
    def _generate_then_code(self, then: List[str]) -> str:
        """Generate assertion code from then conditions"""
        assertions = []
        for condition in then:
            assertions.append(f"assert {condition.replace(' ', '_').lower()}")
        return '\n        '.join(assertions)