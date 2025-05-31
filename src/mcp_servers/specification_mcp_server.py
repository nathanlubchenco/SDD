"""
Real Specification MCP Server for AI-driven specification management.

This server provides tools for managing, validating, and enhancing 
system specifications using AI instead of hardcoded logic.
"""

import json
import asyncio
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
from .base_mcp_server import BaseMCPServer


class SpecificationMCPServer(BaseMCPServer):
    """
    Real MCP Server for specification management.
    
    This replaces the old SpecificationMCPServer class with proper 
    MCP protocol implementation and AI-driven capabilities.
    """

    def __init__(self, spec_directory: Path, show_prompts: bool = False):
        self.spec_dir = spec_directory
        self.spec_dir.mkdir(parents=True, exist_ok=True)
        self.scenario_cache = {}
        
        # Initialize parent class first to set up logger
        super().__init__("specification-server", "1.0.0", show_prompts=show_prompts)
        
        # Now load specifications with logger available
        self.specs = self._load_specifications()
        
    def _register_capabilities(self):
        """Register specification-related tools, resources, and prompts."""
        
        # Tools for specification management
        self.register_tool(
            name="get_scenarios",
            description="Retrieve scenarios for a domain with full context",
            input_schema={
                "type": "object",
                "properties": {
                    "domain": {
                        "type": "string",
                        "description": "Domain name to retrieve scenarios for"
                    },
                    "feature": {
                        "type": "string",
                        "description": "Optional feature filter"
                    },
                    "include_constraints": {
                        "type": "boolean", 
                        "description": "Whether to include constraints in response",
                        "default": True
                    }
                },
                "required": ["domain"]
            },
            handler=self._get_scenarios
        )

        self.register_tool(
            name="validate_scenario",
            description="Validate scenario for conflicts, completeness, and quality using AI",
            input_schema={
                "type": "object",
                "properties": {
                    "scenario": {
                        "type": "object",
                        "description": "Scenario specification to validate"
                    },
                    "domain": {
                        "type": "string",
                        "description": "Domain context for validation"
                    },
                    "check_conflicts": {
                        "type": "boolean",
                        "description": "Check for conflicts with existing scenarios",
                        "default": True
                    },
                    "check_completeness": {
                        "type": "boolean",
                        "description": "Check scenario completeness and suggest improvements",
                        "default": True
                    }
                },
                "required": ["scenario", "domain"]
            },
            handler=self._validate_scenario
        )

        self.register_tool(
            name="generate_edge_cases",
            description="Use AI to generate edge case scenarios based on existing specifications",
            input_schema={
                "type": "object",
                "properties": {
                    "domain": {
                        "type": "string",
                        "description": "Domain to generate edge cases for"
                    },
                    "base_scenarios": {
                        "type": "array",
                        "items": {"type": "object"},
                        "description": "Existing scenarios to build upon"
                    },
                    "constraints": {
                        "type": "object",
                        "description": "Domain constraints to consider"
                    },
                    "edge_case_types": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Types of edge cases to focus on: error, boundary, security, performance",
                        "default": ["error", "boundary"]
                    }
                },
                "required": ["domain"]
            },
            handler=self._generate_edge_cases
        )

        self.register_tool(
            name="analyze_coverage",
            description="Analyze scenario coverage and suggest missing test cases",
            input_schema={
                "type": "object",
                "properties": {
                    "domain": {
                        "type": "string",
                        "description": "Domain to analyze coverage for"
                    },
                    "suggest_missing": {
                        "type": "boolean",
                        "description": "Whether to generate suggestions for missing scenarios",
                        "default": True
                    },
                    "coverage_goals": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Coverage goals: functional, edge_cases, error_handling, performance"
                    }
                },
                "required": ["domain"]
            },
            handler=self._analyze_coverage
        )

        self.register_tool(
            name="generate_test_suite",
            description="Generate test code from scenarios using AI",
            input_schema={
                "type": "object",
                "properties": {
                    "domain": {
                        "type": "string",
                        "description": "Domain to generate tests for"
                    },
                    "language": {
                        "type": "string",
                        "description": "Programming language for test generation",
                        "enum": ["python", "javascript", "java", "go"],
                        "default": "python"
                    },
                    "framework": {
                        "type": "string", 
                        "description": "Test framework to use",
                        "default": "pytest"
                    },
                    "test_style": {
                        "type": "string",
                        "description": "Test style preferences",
                        "enum": ["unit", "integration", "behavior_driven"],
                        "default": "behavior_driven"
                    }
                },
                "required": ["domain"]
            },
            handler=self._generate_test_suite
        )

        self.register_tool(
            name="enhance_scenario",
            description="Use AI to enhance and improve scenario specifications",
            input_schema={
                "type": "object",
                "properties": {
                    "scenario": {
                        "type": "object",
                        "description": "Scenario to enhance"
                    },
                    "enhancement_goals": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Enhancement goals: clarity, completeness, testability, edge_cases"
                    },
                    "domain_context": {
                        "type": "object",
                        "description": "Domain context and constraints"
                    }
                },
                "required": ["scenario"]
            },
            handler=self._enhance_scenario
        )

        # Resources for specification templates and examples
        self.register_resource(
            uri="spec://templates/basic-scenario",
            name="Basic Scenario Template",
            description="Template for creating well-structured scenarios",
            mime_type="application/yaml"
        )

        self.register_resource(
            uri="spec://templates/constraint-specification", 
            name="Constraint Specification Template",
            description="Template for defining system constraints",
            mime_type="application/yaml"
        )

        self.register_resource(
            uri="spec://examples/ecommerce",
            name="E-commerce Specification Example",
            description="Complete specification example for e-commerce domain",
            mime_type="application/yaml"
        )

        # Prompts for specification work
        self.register_prompt(
            name="scenario_validation",
            description="Validate and improve scenario specifications",
            arguments=[
                {"name": "scenario", "description": "Scenario to validate", "required": True},
                {"name": "domain", "description": "Domain context", "required": True},
                {"name": "existing_scenarios", "description": "Related scenarios", "required": False}
            ]
        )

        self.register_prompt(
            name="edge_case_generation", 
            description="Generate comprehensive edge case scenarios",
            arguments=[
                {"name": "domain", "description": "Target domain", "required": True},
                {"name": "base_scenarios", "description": "Scenarios to build upon", "required": True},
                {"name": "focus_areas", "description": "Areas to focus on", "required": False}
            ]
        )

    def _load_specifications(self) -> Dict:
        """Load all specification files from the directory."""
        specs = {}
        for spec_file in self.spec_dir.glob("**/*.yaml"):
            try:
                with open(spec_file) as f:
                    domain = spec_file.stem
                    specs[domain] = yaml.safe_load(f)
            except Exception as e:
                self.logger.warning(f"Failed to load spec {spec_file}: {e}")
        return specs

    async def _get_scenarios(self, 
                           domain: str, 
                           feature: Optional[str] = None,
                           include_constraints: bool = True) -> Dict[str, Any]:
        """Retrieve scenarios with full context."""
        
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

    async def _validate_scenario(self,
                               scenario: Dict[str, Any],
                               domain: str,
                               check_conflicts: bool = True,
                               check_completeness: bool = True) -> Dict[str, Any]:
        """Validate scenario using AI for advanced analysis."""
        
        if not self.ai_client:
            return await self._fallback_validate_scenario(scenario, domain, check_conflicts, check_completeness)

        # Get domain context
        domain_data = await self._get_scenarios(domain)
        existing_scenarios = domain_data.get("scenarios", [])
        constraints = domain_data.get("constraints", {})

        # Build validation prompt
        prompt = self._build_validation_prompt(scenario, domain, existing_scenarios, constraints)

        try:
            validation_response = self.ai_client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=1500
            )

            # Parse AI response into structured validation result
            result = self._parse_validation_response(validation_response)
            
            self.logger.info(f"AI validated scenario '{scenario.get('name', 'unnamed')}'")
            return result

        except Exception as e:
            self.logger.error(f"AI validation failed: {e}")
            return await self._fallback_validate_scenario(scenario, domain, check_conflicts, check_completeness)

    async def _generate_edge_cases(self,
                                 domain: str,
                                 base_scenarios: Optional[List[Dict]] = None,
                                 constraints: Optional[Dict] = None,
                                 edge_case_types: List[str] = ["error", "boundary"]) -> List[Dict]:
        """Generate edge case scenarios using AI."""
        
        if not self.ai_client:
            return self._fallback_generate_edge_cases(domain, base_scenarios)

        # Get domain context if base_scenarios not provided
        if not base_scenarios:
            domain_data = await self._get_scenarios(domain)
            base_scenarios = domain_data.get("scenarios", [])
            constraints = domain_data.get("constraints", {})

        prompt = self._build_edge_case_prompt(domain, base_scenarios, constraints, edge_case_types)

        try:
            response = self.ai_client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,  # Slightly higher for creativity
                max_tokens=2000
            )

            edge_cases = self._parse_edge_cases_response(response)
            
            self.logger.info(f"Generated {len(edge_cases)} edge cases for {domain}")
            return edge_cases

        except Exception as e:
            self.logger.error(f"Edge case generation failed: {e}")
            return self._fallback_generate_edge_cases(domain, base_scenarios)

    async def _analyze_coverage(self,
                              domain: str,
                              suggest_missing: bool = True,
                              coverage_goals: Optional[List[str]] = None) -> Dict[str, Any]:
        """Analyze scenario coverage using AI."""
        
        coverage_goals = coverage_goals or ["functional", "edge_cases", "error_handling"]
        
        domain_data = await self._get_scenarios(domain)
        scenarios = domain_data.get("scenarios", [])
        constraints = domain_data.get("constraints", {})

        if not self.ai_client:
            return self._fallback_analyze_coverage(scenarios, coverage_goals)

        prompt = self._build_coverage_analysis_prompt(domain, scenarios, constraints, coverage_goals)

        try:
            response = self.ai_client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=1500
            )

            analysis = self._parse_coverage_analysis(response)
            
            self.logger.info(f"Analyzed coverage for {domain}: {analysis.get('coverage_score', 'unknown')}%")
            return analysis

        except Exception as e:
            self.logger.error(f"Coverage analysis failed: {e}")
            return self._fallback_analyze_coverage(scenarios, coverage_goals)

    async def _generate_test_suite(self,
                                 domain: str,
                                 language: str = "python",
                                 framework: str = "pytest",
                                 test_style: str = "behavior_driven") -> str:
        """Generate test code from scenarios using AI."""
        
        domain_data = await self._get_scenarios(domain)
        scenarios = domain_data.get("scenarios", [])

        if not self.ai_client:
            return self._fallback_generate_tests(scenarios, language, framework)

        prompt = self._build_test_generation_prompt(domain, scenarios, language, framework, test_style)

        try:
            test_code = self.ai_client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=3000
            )

            self.logger.info(f"Generated {language}/{framework} test suite for {domain}")
            return test_code

        except Exception as e:
            self.logger.error(f"Test generation failed: {e}")
            return self._fallback_generate_tests(scenarios, language, framework)

    async def _enhance_scenario(self,
                              scenario: Dict[str, Any],
                              enhancement_goals: Optional[List[str]] = None,
                              domain_context: Optional[Dict] = None) -> Dict[str, Any]:
        """Enhance scenario specification using AI."""
        
        enhancement_goals = enhancement_goals or ["clarity", "completeness", "testability"]
        domain_context = domain_context or {}

        if not self.ai_client:
            return scenario  # Return original if AI unavailable

        prompt = self._build_enhancement_prompt(scenario, enhancement_goals, domain_context)

        try:
            response = self.ai_client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=1500
            )

            enhanced = self._parse_enhanced_scenario(response, scenario)
            
            self.logger.info(f"Enhanced scenario '{scenario.get('name', 'unnamed')}'")
            return enhanced

        except Exception as e:
            self.logger.error(f"Scenario enhancement failed: {e}")
            return scenario

    # Prompt building methods
    def _build_validation_prompt(self, scenario: Dict, domain: str, existing_scenarios: List[Dict], constraints: Dict) -> str:
        """Build prompt for AI scenario validation using SDD principles."""
        return f"""
You are an SDD specification expert. Validate this behavioral scenario for clarity, implementability, and behavioral completeness.

Domain: {domain}
Scenario to validate:
{yaml.dump(scenario, default_flow_style=False)}

Existing scenarios in domain:
{yaml.dump(existing_scenarios[:5], default_flow_style=False)}  # Behavioral context

Domain constraints:
{yaml.dump(constraints, default_flow_style=False)}

SDD VALIDATION CRITERIA:
1. BEHAVIORAL CLARITY: Does the scenario describe observable system behavior?
2. IMPLEMENTATION INDEPENDENCE: Does it specify WHAT happens, not HOW?
3. TESTABILITY: Can this scenario be directly executed as a test?
4. BUSINESS VALUE: Does it represent meaningful user or system behavior?
5. SCENARIO COMPLETENESS: Are Given/When/Then elements sufficient for implementation?
6. BEHAVIORAL CONSISTENCY: Does it conflict with or duplicate existing behaviors?

VALIDATION FOCUS:
- Given: Are preconditions clear and realistic?
- When: Is the trigger action specific and testable?
- Then: Are expected outcomes observable and verifiable?
- Business Logic: Does this represent real-world behavior?
- Error Handling: Are failure scenarios properly specified?

Analyze the scenario and provide:
1. Behavioral conflicts with existing scenarios
2. Missing elements that prevent implementation
3. Clarity issues that obscure business intent
4. Testability concerns that prevent verification
5. Suggestions to improve behavioral specification

Format response as JSON:
{{
  "valid": true/false,
  "behavioral_clarity": 0-100,
  "implementability": 0-100,
  "conflicts": ["behavioral conflicts with existing scenarios"],
  "warnings": ["potential issues with behavioral specification"],
  "suggestions": ["specific improvements for better behavior definition"],
  "quality_score": 0-100,
  "missing_elements": ["required elements for complete behavior specification"],
  "business_value_assessment": "how this scenario serves user/system needs"
}}
"""

    def _build_edge_case_prompt(self, domain: str, base_scenarios: List[Dict], constraints: Dict, edge_case_types: List[str]) -> str:
        """Build prompt for edge case generation using SDD principles."""
        return f"""
You are an SDD expert at discovering edge case behaviors that complement the main behavioral scenarios.

Domain: {domain}
Focus on these behavioral edge case types: {', '.join(edge_case_types)}

Base behavioral scenarios:
{yaml.dump(base_scenarios, default_flow_style=False)}

Domain constraints:
{yaml.dump(constraints, default_flow_style=False)}

SDD EDGE CASE PHILOSOPHY:
Edge cases are not just technical failures - they are alternative behavioral paths that must be properly specified and handled. Each edge case represents a scenario where the system's behavior differs from the happy path.

BEHAVIORAL EDGE CASE CATEGORIES:
- Boundary behaviors: How system behaves at limits
- Error behaviors: What happens when preconditions fail
- Security behaviors: How system protects against misuse
- Performance behaviors: System behavior under load/stress
- Data validation behaviors: How invalid inputs are handled
- Business rule violations: When business constraints are violated

Generate 3-5 edge case scenarios that specify:
1. Alternative behavioral paths from base scenarios
2. System behavior under exceptional conditions
3. Recovery and error handling behaviors
4. Boundary condition behaviors
5. Security and validation behaviors

For each edge case, provide behavioral specification:
- scenario: descriptive name focusing on behavior
- description: what behavioral aspect this tests
- given: preconditions that lead to edge behavior
- when: trigger that causes alternative behavior
- then: expected system behavior (not just error messages)
- edge_case_type: category of behavioral edge case
- business_rationale: why this behavior matters to users/business

CRITICAL: Focus on BEHAVIORAL outcomes, not technical implementation details. Each edge case should specify what the system DOES in these situations, not how it fails technically.

Return as YAML array of behavioral scenarios.
"""

    def _build_coverage_analysis_prompt(self, domain: str, scenarios: List[Dict], constraints: Dict, coverage_goals: List[str]) -> str:
        """Build prompt for coverage analysis."""
        return f"""
Analyze test coverage for this software domain.

Domain: {domain}
Coverage goals: {', '.join(coverage_goals)}

Current scenarios:
{yaml.dump(scenarios, default_flow_style=False)}

Domain constraints:
{yaml.dump(constraints, default_flow_style=False)}

Analyze coverage and provide:
1. Coverage percentage for each goal area
2. Missing test scenarios
3. Over-tested areas
4. Quality assessment
5. Specific suggestions for improvement

Format as JSON:
{{
  "coverage_score": 0-100,
  "goal_coverage": {{"functional": 85, "edge_cases": 45, ...}},
  "missing_scenarios": [list of missing scenarios],
  "over_tested": [list of over-tested areas],
  "suggestions": [list of specific improvements]
}}
"""

    def _build_test_generation_prompt(self, domain: str, scenarios: List[Dict], language: str, framework: str, test_style: str) -> str:
        """Build prompt for test code generation."""
        return f"""
Generate {language} test code using {framework} for these scenarios.

Domain: {domain}
Test style: {test_style}
Language: {language}
Framework: {framework}

Scenarios:
{yaml.dump(scenarios, default_flow_style=False)}

Generate comprehensive test code that:
1. Tests all scenarios thoroughly
2. Follows {framework} best practices
3. Uses {test_style} approach
4. Includes proper setup/teardown
5. Has clear, descriptive test names
6. Includes edge case handling

Return only the test code, no explanations.
"""

    def _build_enhancement_prompt(self, scenario: Dict, enhancement_goals: List[str], domain_context: Dict) -> str:
        """Build prompt for scenario enhancement using SDD principles."""
        return f"""
Transform this scenario into a more behavior-focused specification using SDD principles for better {', '.join(enhancement_goals)}.

Current scenario:
{yaml.dump(scenario, default_flow_style=False)}

Domain context:
{yaml.dump(domain_context, default_flow_style=False)}

Enhancement goals: {', '.join(enhancement_goals)}

SDD ENHANCEMENT PRINCIPLES:
1. Scenarios must describe OBSERVABLE BEHAVIOR, not implementation details
2. Focus on WHAT the system does, never HOW it does it
3. Use business language that stakeholders understand
4. Ensure scenarios are directly implementable as tests
5. Specify clear behavioral outcomes, not technical side effects

BEHAVIORAL ENHANCEMENT CHECKLIST:
- Given: Are preconditions expressed in business terms?
- When: Is the trigger action something a user/system actually does?
- Then: Do outcomes describe observable system behavior?
- Language: Is this free of implementation details?
- Testability: Can this be directly verified by automated tests?
- Business Value: Does this represent meaningful user/business behavior?

Enhance the scenario by:
1. Converting technical language to behavioral language
2. Ensuring Given/When/Then elements are complete and behavior-focused
3. Improving clarity of expected behavioral outcomes
4. Removing any implementation hints or technical details
5. Strengthening the business context and value
6. Making the scenario more directly testable
7. Ensuring it fits naturally with domain behavioral patterns

CRITICAL: The enhanced scenario should read like a story about system behavior that both business stakeholders and developers can understand and verify.

Return the enhanced behavioral scenario in YAML format.
"""

    # Response parsing methods
    def _parse_validation_response(self, response: str) -> Dict[str, Any]:
        """Parse AI validation response into structured format."""
        try:
            # Try to extract JSON from response (handle markdown formatting)
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                json_text = response[start:end].strip()
            else:
                json_text = response.strip()
            
            return json.loads(json_text)
        except json.JSONDecodeError:
            # Fallback parsing
            return {
                "valid": "error" not in response.lower(),
                "conflicts": [],
                "warnings": ["AI provided unstructured response"],
                "suggestions": [response[:200] + "..."] if response else ["No response"],
                "quality_score": 50
            }

    def _parse_edge_cases_response(self, response: str) -> List[Dict]:
        """Parse AI edge cases response."""
        try:
            # Try to extract YAML from response (handle markdown formatting)
            if "```yaml" in response:
                start = response.find("```yaml") + 7
                end = response.find("```", start)
                yaml_text = response[start:end].strip()
            elif "```" in response:
                start = response.find("```") + 3
                end = response.find("```", start)
                yaml_text = response[start:end].strip()
            else:
                yaml_text = response.strip()
            
            parsed = yaml.safe_load(yaml_text)
            return parsed if isinstance(parsed, list) else []
        except yaml.YAMLError:
            return []

    def _parse_coverage_analysis(self, response: str) -> Dict[str, Any]:
        """Parse AI coverage analysis response."""
        try:
            # Try to extract JSON from response (handle markdown formatting)
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                json_text = response[start:end].strip()
            else:
                json_text = response.strip()
            
            return json.loads(json_text)
        except json.JSONDecodeError:
            return {
                "coverage_score": 50,
                "goal_coverage": {},
                "missing_scenarios": [],
                "suggestions": [response[:100] + "..." if response else "No response"]
            }

    def _parse_enhanced_scenario(self, response: str, original: Dict) -> Dict[str, Any]:
        """Parse enhanced scenario response."""
        try:
            return yaml.safe_load(response)
        except yaml.YAMLError:
            return original

    # Fallback methods when AI is unavailable
    async def _fallback_validate_scenario(self, scenario: Dict, domain: str, check_conflicts: bool, check_completeness: bool) -> Dict[str, Any]:
        """Fallback validation using basic rules."""
        validation_result = {
            "valid": True,
            "conflicts": [],
            "warnings": [],
            "suggestions": [],
            "quality_score": 70
        }

        # Basic completeness checks
        if not scenario.get("name"):
            validation_result["warnings"].append("Scenario missing name")
        if not scenario.get("when"):
            validation_result["warnings"].append("Scenario missing 'when' action")
        if not scenario.get("then"):
            validation_result["warnings"].append("Scenario missing 'then' expectations")

        return validation_result

    def _fallback_generate_edge_cases(self, domain: str, base_scenarios: Optional[List[Dict]]) -> List[Dict]:
        """Fallback edge case generation."""
        return [
            {
                "name": f"{domain}_error_handling",
                "description": "Test error handling in critical paths",
                "given": "System is in normal state",
                "when": "Invalid input is provided",
                "then": ["Appropriate error is returned", "System remains stable"],
                "edge_case_type": "error"
            }
        ]

    def _fallback_analyze_coverage(self, scenarios: List[Dict], coverage_goals: List[str]) -> Dict[str, Any]:
        """Fallback coverage analysis."""
        return {
            "coverage_score": 60,
            "goal_coverage": {goal: 60 for goal in coverage_goals},
            "missing_scenarios": ["More edge cases needed"],
            "suggestions": ["Add error handling scenarios", "Include performance tests"]
        }

    def _fallback_generate_tests(self, scenarios: List[Dict], language: str, framework: str) -> str:
        """Fallback test generation."""
        return f"""# Generated {language} tests using {framework}

import {framework}

class TestScenarios:
    def test_basic_functionality(self):
        # Basic test for {len(scenarios)} scenarios
        assert True  # Replace with actual test logic
"""

    # Resource and prompt handlers
    async def _read_resource(self, uri: str) -> str:
        """Read specification resources."""
        if uri == "spec://templates/basic-scenario":
            return """name: "scenario_name"
description: "Clear description of what this scenario tests"
given: "Initial system state"
when: "Action or trigger"
then:
  - "Expected outcome 1"
  - "Expected outcome 2"
feature: "feature_name"
priority: "high|medium|low"
"""

        elif uri == "spec://templates/constraint-specification":
            return """constraints:
  performance:
    - name: "API response time"
      requirement: "p95 latency < 100ms"
    - name: "Throughput"
      requirement: "> 1000 requests/second"
  
  security:
    - name: "Authentication"
      requirement: "JWT tokens required for all endpoints"
    - name: "Data encryption"
      requirement: "All PII must be encrypted at rest"
  
  reliability:
    - name: "Uptime"
      requirement: "99.9% availability"
    - name: "Error rate"
      requirement: "< 0.1% error rate"
"""

        elif uri == "spec://examples/ecommerce":
            return """feature:
  name: "E-commerce Order Management"
  description: "Handle customer orders from creation to fulfillment"

scenarios:
  - name: "Process successful order"
    given: "Customer has items in cart and valid payment method"
    when: "Customer submits order"
    then:
      - "Order is created with unique ID"
      - "Payment is processed"
      - "Inventory is updated"
      - "Confirmation email is sent"
  
  - name: "Handle payment failure"
    given: "Customer has items in cart"
    when: "Customer submits order with invalid payment"
    then:
      - "Payment is rejected"
      - "Order is not created"
      - "Error message is shown"
      - "Cart remains unchanged"

constraints:
  performance:
    - name: "Order processing time"
      requirement: "< 3 seconds end-to-end"
  security:
    - name: "Payment security"
      requirement: "PCI DSS compliance required"
"""

        return f"Resource not found: {uri}"

    async def _get_prompt(self, name: str, arguments: Dict[str, Any]) -> str:
        """Generate specification prompts."""
        if name == "scenario_validation":
            scenario = arguments.get("scenario", {})
            domain = arguments.get("domain", "")
            return self._build_validation_prompt(scenario, domain, [], {})

        elif name == "edge_case_generation":
            domain = arguments.get("domain", "")
            base_scenarios = arguments.get("base_scenarios", [])
            return self._build_edge_case_prompt(domain, base_scenarios, {}, ["error", "boundary"])

        return f"Prompt not found: {name}"