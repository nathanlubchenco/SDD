"""
Implementation MCP Server for AI-driven code generation and refinement.

This server handles code generation, testing, and iterative refinement using AI.
It supports the full generate→test→refine cycle for AI-driven development.
"""

import asyncio
import ast
import json
import tempfile
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional
from .base_mcp_server import BaseMCPServer


class ImplementationMCPServer(BaseMCPServer):
    """
    MCP Server for AI-driven implementation generation and refinement.
    
    This server provides tools for generating initial implementations,
    refining code based on test failures and quality analysis,
    and managing the iterative development process.
    """

    def __init__(self, workspace_dir: Optional[Path] = None, show_prompts: bool = False, api_docs_server=None):
        super().__init__("implementation-server", "1.0.0", show_prompts=show_prompts)
        self.workspace_dir = workspace_dir or Path("workspaces")
        self.api_docs_server = api_docs_server
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        self.active_workspaces = {}

    def _register_capabilities(self):
        """Register implementation and refinement tools."""
        
        # Core implementation generation
        self.register_tool(
            name="generate_implementation",
            description="Generate initial implementation from scenarios and constraints",
            input_schema={
                "type": "object",
                "properties": {
                    "scenarios": {
                        "type": "array",
                        "items": {"type": "object"},
                        "description": "Behavior scenarios to implement"
                    },
                    "constraints": {
                        "type": "object",
                        "description": "Non-functional constraints and requirements"
                    },
                    "target_framework": {
                        "type": "string",
                        "enum": ["fastapi", "flask", "django", "plain"],
                        "description": "Target framework for implementation",
                        "default": "fastapi"
                    },
                    "include_tests": {
                        "type": "boolean",
                        "description": "Whether to generate test code",
                        "default": True
                    },
                    "optimization_level": {
                        "type": "string",
                        "enum": ["simple", "balanced", "performance", "maintainable"],
                        "description": "Code optimization focus",
                        "default": "balanced"
                    }
                },
                "required": ["scenarios"]
            },
            handler=self._generate_implementation
        )

        self.register_tool(
            name="refine_implementation",
            description="Refine existing implementation based on test failures and quality analysis",
            input_schema={
                "type": "object",
                "properties": {
                    "current_implementation": {
                        "type": "object",
                        "description": "Current implementation to refine"
                    },
                    "test_failures": {
                        "type": "array",
                        "items": {"type": "object"},
                        "description": "Test failures to address"
                    },
                    "quality_issues": {
                        "type": "array",
                        "items": {"type": "object"},
                        "description": "Code quality issues to fix"
                    },
                    "refactoring_suggestions": {
                        "type": "array",
                        "items": {"type": "object"},
                        "description": "AI-generated refactoring suggestions"
                    },
                    "target_quality_score": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 100,
                        "description": "Target quality score to achieve",
                        "default": 80
                    },
                    "preserve_functionality": {
                        "type": "boolean",
                        "description": "Whether to preserve existing functionality",
                        "default": True
                    }
                },
                "required": ["current_implementation"]
            },
            handler=self._refine_implementation
        )

        self.register_tool(
            name="generate_code_from_specification",
            description="Generate specific code module from detailed specification",
            input_schema={
                "type": "object",
                "properties": {
                    "specification_text": {
                        "type": "string",
                        "description": "Detailed specification for code generation"
                    },
                    "module_name": {
                        "type": "string",
                        "description": "Name of the module to generate"
                    },
                    "style_preferences": {
                        "type": "object",
                        "description": "Code style and structure preferences"
                    }
                },
                "required": ["specification_text", "module_name"]
            },
            handler=self._generate_code_from_specification
        )

        self.register_tool(
            name="optimize_for_constraints",
            description="Optimize implementation to meet specific constraints",
            input_schema={
                "type": "object",
                "properties": {
                    "implementation": {
                        "type": "object",
                        "description": "Implementation to optimize"
                    },
                    "constraints": {
                        "type": "object",
                        "description": "Constraints to optimize for"
                    },
                    "optimization_focus": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Areas to focus optimization: performance, memory, security, readability"
                    }
                },
                "required": ["implementation", "constraints"]
            },
            handler=self._optimize_for_constraints
        )

        self.register_tool(
            name="create_workspace",
            description="Create a new workspace for development",
            input_schema={
                "type": "object",
                "properties": {
                    "project_name": {
                        "type": "string",
                        "description": "Name of the project"
                    },
                    "template": {
                        "type": "string",
                        "enum": ["microservice", "library", "cli", "webapp"],
                        "description": "Project template to use",
                        "default": "microservice"
                    }
                },
                "required": ["project_name"]
            },
            handler=self._create_workspace
        )

        self.register_tool(
            name="write_implementation_files",
            description="Write implementation files to workspace",
            input_schema={
                "type": "object",
                "properties": {
                    "workspace_id": {
                        "type": "string",
                        "description": "Workspace identifier"
                    },
                    "implementation": {
                        "type": "object",
                        "description": "Implementation data to write"
                    }
                },
                "required": ["workspace_id", "implementation"]
            },
            handler=self._write_implementation_files
        )

    async def _generate_implementation(self,
                                     scenarios: List[Dict[str, Any]],
                                     constraints: Dict[str, Any] = {},
                                     target_framework: str = "fastapi",
                                     include_tests: bool = True,
                                     optimization_level: str = "balanced") -> Dict[str, Any]:
        """Generate initial implementation from scenarios and constraints."""
        
        if not self.ai_client:
            self.logger.warning("AI client not available, using enhanced fallback")
            return await self._fallback_implementation_generation(scenarios, constraints, target_framework)

        # Query API documentation to enhance implementation quality
        api_docs_context = await self._gather_api_documentation(target_framework, scenarios)

        # Build comprehensive prompt for implementation generation
        prompt = self._build_implementation_prompt(
            scenarios, constraints, target_framework, optimization_level, api_docs_context
        )

        try:
            self._log_prompt("generate_implementation", prompt)
            
            response = self.ai_client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=4000
            )
            
            self._log_prompt("generate_implementation", prompt, response)

            implementation = self._parse_implementation_response(response, include_tests)
            
            # Add metadata
            implementation["metadata"] = {
                "scenarios_count": len(scenarios),
                "framework": target_framework,
                "optimization_level": optimization_level,
                "generated_with_ai": True
            }

            self.logger.info(f"Generated implementation with {len(scenarios)} scenarios")
            return implementation

        except Exception as e:
            self.logger.error(f"AI implementation generation failed: {e}")
            return await self._fallback_implementation_generation(scenarios, constraints, target_framework)

    async def _refine_implementation(self,
                                   current_implementation: Dict[str, Any],
                                   test_failures: List[Dict[str, Any]] = [],
                                   quality_issues: List[Dict[str, Any]] = [],
                                   refactoring_suggestions: List[Dict[str, Any]] = [],
                                   target_quality_score: int = 80,
                                   preserve_functionality: bool = True) -> Dict[str, Any]:
        """Refine implementation based on feedback from testing and analysis."""
        
        if not self.ai_client:
            return {"success": False, "error": "AI client not available for refinement"}

        # Extract current code - handle multiple possible formats
        if isinstance(current_implementation, list) and len(current_implementation) > 0:
            # If it's a list, try to get the first element and parse it
            impl_data = current_implementation[0]
            if isinstance(impl_data, dict) and "text" in impl_data:
                # Handle MCP response format with text field containing string representation
                text_content = impl_data["text"]
                try:
                    # First try to parse as JSON
                    current_implementation = json.loads(text_content)
                except json.JSONDecodeError:
                    # If that fails, try to evaluate as Python literal (for string dict representations)
                    try:
                        import ast
                        current_implementation = ast.literal_eval(text_content)
                    except (ValueError, SyntaxError):
                        self.logger.warning(f"Failed to parse implementation text: {text_content[:100]}...")
                        current_implementation = {}
            elif isinstance(impl_data, str):
                try:
                    current_implementation = json.loads(impl_data)
                except json.JSONDecodeError:
                    current_implementation = {}
            elif isinstance(impl_data, dict):
                # Already a dict, use directly
                current_implementation = impl_data
        
        # Ensure current_implementation is a dict
        if not isinstance(current_implementation, dict):
            current_implementation = {}
            
        current_code = current_implementation.get("main_module", "")
        current_tests = current_implementation.get("test_module", "")

        # Build refinement prompt
        prompt = self._build_refinement_prompt(
            current_code=current_code,
            current_tests=current_tests,
            test_failures=test_failures,
            quality_issues=quality_issues,
            refactoring_suggestions=refactoring_suggestions,
            target_quality_score=target_quality_score,
            preserve_functionality=preserve_functionality
        )

        try:
            self._log_prompt("refine_implementation", prompt)
            
            response = self.ai_client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=4000
            )
            
            self._log_prompt("refine_implementation", prompt, response)

            refined_implementation = self._parse_implementation_response(response, include_tests=True)
            
            # Preserve metadata and add refinement info
            refined_implementation["metadata"] = current_implementation.get("metadata", {})
            refined_implementation["metadata"]["refinement_info"] = {
                "test_failures_addressed": len(test_failures),
                "quality_issues_addressed": len(quality_issues),
                "suggestions_applied": len(refactoring_suggestions),
                "target_quality_score": target_quality_score
            }

            self.logger.info(f"Refined implementation addressing {len(test_failures)} test failures and {len(quality_issues)} quality issues")
            
            return {
                "success": True,
                "implementation": refined_implementation
            }

        except Exception as e:
            self.logger.error(f"AI implementation refinement failed: {e}")
            return {"success": False, "error": str(e)}

    async def _generate_code_from_specification(self,
                                              specification_text: str,
                                              module_name: str,
                                              style_preferences: Dict[str, Any] = {}) -> Dict[str, Any]:
        """Generate code from detailed specification."""
        
        if not self.ai_client:
            return {"success": False, "error": "AI client not available"}

        prompt = f"""
Generate Python code for the following specification:

MODULE NAME: {module_name}

SPECIFICATION:
{specification_text}

STYLE PREFERENCES:
{json.dumps(style_preferences, indent=2) if style_preferences else "Use standard Python conventions"}

Requirements:
1. Generate clean, well-documented Python code
2. Include type hints where appropriate
3. Follow PEP 8 conventions
4. Include docstrings for classes and functions
5. Handle errors appropriately
6. Make the code production-ready

Return the code in this JSON format:
{{
  "module_code": "the generated Python code",
  "dependencies": ["list", "of", "required", "packages"],
  "key_functions": ["list", "of", "main", "functions"],
  "complexity_estimate": "low|medium|high"
}}
"""

        try:
            response = self.ai_client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=3000
            )

            result = self._parse_code_generation_response(response)
            result["success"] = True
            
            self.logger.info(f"Generated code for module {module_name}")
            return result

        except Exception as e:
            self.logger.error(f"Code generation failed: {e}")
            return {"success": False, "error": str(e)}

    async def _optimize_for_constraints(self,
                                      implementation: Dict[str, Any],
                                      constraints: Dict[str, Any],
                                      optimization_focus: List[str] = ["performance"]) -> Dict[str, Any]:
        """Optimize implementation to meet specific constraints."""
        
        if not self.ai_client:
            return {"success": False, "error": "AI client not available for optimization"}

        current_code = implementation.get("main_module", "")
        
        prompt = f"""
Optimize this Python code to meet the specified constraints:

CURRENT CODE:
```python
{current_code}
```

CONSTRAINTS TO MEET:
{json.dumps(constraints, indent=2)}

OPTIMIZATION FOCUS: {', '.join(optimization_focus)}

Please optimize the code while:
1. Maintaining all existing functionality
2. Meeting the specified constraints
3. Focusing on: {', '.join(optimization_focus)}
4. Keeping the code readable and maintainable

Return optimized code in JSON format:
{{
  "optimized_code": "the optimized Python code",
  "optimizations_applied": ["list of optimizations made"],
  "constraint_compliance": {{"constraint": "compliance_status"}},
  "performance_notes": "notes about performance improvements"
}}
"""

        try:
            response = self.ai_client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=3000
            )

            result = self._parse_optimization_response(response)
            result["success"] = True
            
            self.logger.info(f"Optimized implementation for {len(optimization_focus)} focus areas")
            return result

        except Exception as e:
            self.logger.error(f"Optimization failed: {e}")
            return {"success": False, "error": str(e)}

    async def _create_workspace(self,
                              project_name: str,
                              template: str = "microservice") -> Dict[str, Any]:
        """Create a new workspace for development."""
        
        import time
        
        workspace_path = self.workspace_dir / project_name
        workspace_path.mkdir(parents=True, exist_ok=True)

        # Initialize based on template
        if template == "microservice":
            await self._init_microservice_template(workspace_path)
        elif template == "library":
            await self._init_library_template(workspace_path)
        elif template == "cli":
            await self._init_cli_template(workspace_path)
        elif template == "webapp":
            await self._init_webapp_template(workspace_path)

        workspace_id = f"ws_{project_name}_{int(time.time())}"
        self.active_workspaces[workspace_id] = {
            "path": workspace_path,
            "project_name": project_name,
            "template": template
        }

        return {
            "success": True,
            "workspace_id": workspace_id,
            "path": str(workspace_path),
            "template": template
        }

    async def _write_implementation_files(self,
                                        workspace_id: str,
                                        implementation: Dict[str, Any]) -> Dict[str, Any]:
        """Write implementation files to workspace."""
        
        workspace = self.active_workspaces.get(workspace_id)
        if not workspace:
            return {"success": False, "error": "Workspace not found"}

        workspace_path = workspace["path"]
        files_written = []

        try:
            # Write main module
            if "main_module" in implementation:
                main_file = workspace_path / f"{workspace['project_name']}.py"
                main_file.write_text(implementation["main_module"])
                files_written.append(str(main_file))

            # Write test module
            if "test_module" in implementation:
                test_file = workspace_path / f"test_{workspace['project_name']}.py"
                test_file.write_text(implementation["test_module"])
                files_written.append(str(test_file))

            # Write requirements.txt
            if "dependencies" in implementation:
                deps = implementation["dependencies"]
                if isinstance(deps, list):
                    deps_content = "\n".join(deps) + "\n"
                else:
                    deps_content = str(deps)
                
                req_file = workspace_path / "requirements.txt"
                req_file.write_text(deps_content)
                files_written.append(str(req_file))

            # Write __init__.py
            init_file = workspace_path / "__init__.py"
            if "main_module" in implementation:
                init_content = self._generate_init_file(implementation["main_module"], workspace['project_name'])
                init_file.write_text(init_content)
                files_written.append(str(init_file))

            return {
                "success": True,
                "files_written": files_written,
                "workspace_path": str(workspace_path)
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    # Helper methods for prompt building and response parsing

    async def _gather_api_documentation(self, framework: str, scenarios: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Gather relevant API documentation to enhance code generation."""
        
        if not self.api_docs_server:
            self.logger.warning("No API docs server available for documentation gathering")
            return {"framework_docs": "No API docs server available", "examples": [], "best_practices": {}}
        
        try:
            # Analyze scenarios to determine what documentation we need
            use_cases = []
            for scenario in scenarios:
                when_action = scenario.get('when', '')
                then_result = scenario.get('then', '')
                if when_action and then_result:
                    use_cases.append(f"{when_action} -> {then_result}")
            
            use_case_context = f"{framework} " + " and ".join(use_cases[:3])  # Limit context
            
            self.logger.info(f"Gathering API documentation for framework: {framework}")
            self.logger.info(f"Use case context: {use_case_context}")
            
            # Get framework documentation
            framework_request = {
                "method": "tools/call",
                "params": {
                    "name": "get_api_reference",
                    "arguments": {
                        "library": framework,
                        "include_examples": True
                    }
                }
            }
            
            self.logger.info(f"📚 API Docs Request - Framework Reference: {framework_request}")
            framework_response = await self.api_docs_server.handle_mcp_request(framework_request)
            self.logger.info(f"📚 API Docs Response - Framework: {framework_response}")
            framework_docs = self._extract_mcp_content(framework_response)
            self.logger.info(f"📚 Extracted Framework Docs: {type(framework_docs)} - {str(framework_docs)[:200]}...")
            
            # Find code examples for the use case
            examples_request = {
                "method": "tools/call", 
                "params": {
                    "name": "find_code_examples",
                    "arguments": {
                        "use_case": use_case_context,
                        "complexity": "intermediate"
                    }
                }
            }
            
            self.logger.info(f"📚 API Docs Request - Code Examples: {examples_request}")
            examples_response = await self.api_docs_server.handle_mcp_request(examples_request)
            self.logger.info(f"📚 API Docs Response - Examples: {examples_response}")
            examples = self._extract_mcp_content(examples_response)
            self.logger.info(f"📚 Extracted Examples: {type(examples)} - {str(examples)[:200]}...")
            
            # Get best practices
            practices_request = {
                "method": "tools/call",
                "params": {
                    "name": "check_best_practices", 
                    "arguments": {
                        "technology": framework,
                        "focus_area": "general"
                    }
                }
            }
            
            self.logger.info(f"📚 API Docs Request - Best Practices: {practices_request}")
            practices_response = await self.api_docs_server.handle_mcp_request(practices_request)
            self.logger.info(f"📚 API Docs Response - Practices: {practices_response}")
            best_practices = self._extract_mcp_content(practices_response)
            self.logger.info(f"📚 Extracted Best Practices: {type(best_practices)} - {str(best_practices)[:200]}...")
            
            final_result = {
                "framework_docs": framework_docs,
                "examples": examples,
                "best_practices": best_practices,
                "enhanced": True
            }
            
            self.logger.info(f"📚 Final API Documentation Context Summary:")
            self.logger.info(f"   - Framework docs: {type(framework_docs)} ({len(str(framework_docs))} chars)")
            self.logger.info(f"   - Examples: {type(examples)} ({len(str(examples))} chars)")
            self.logger.info(f"   - Best practices: {type(best_practices)} ({len(str(best_practices))} chars)")
            
            return final_result
            
        except Exception as e:
            self.logger.error(f"Failed to gather API documentation: {e}", exc_info=True)
            return {"framework_docs": "Documentation gathering failed", "examples": [], "best_practices": {}}

    def _extract_mcp_content(self, response: Dict[str, Any]) -> Any:
        """Extract content from MCP response format."""
        try:
            content = response.get("result", {}).get("content", [])
            if isinstance(content, list) and content:
                if isinstance(content[0], dict) and "text" in content[0]:
                    text = content[0]["text"]
                    try:
                        return json.loads(text)
                    except json.JSONDecodeError:
                        return text
                return content[0]
            return content
        except Exception:
            return "Content extraction failed"

    def _format_api_docs_for_prompt(self, api_docs_context: Dict[str, Any]) -> str:
        """Format API documentation context for inclusion in prompts."""
        
        formatted_sections = []
        
        # Framework documentation
        framework_docs = api_docs_context.get("framework_docs", {})
        if isinstance(framework_docs, dict) and framework_docs:
            formatted_sections.append(f"Framework Reference: {json.dumps(framework_docs, indent=2)}")
        elif isinstance(framework_docs, str) and framework_docs:
            formatted_sections.append(f"Framework Info: {framework_docs}")
        
        # Code examples
        examples = api_docs_context.get("examples", [])
        if examples:
            formatted_sections.append("Code Examples:")
            if isinstance(examples, list):
                for i, example in enumerate(examples[:2]):  # Limit to 2 examples
                    if isinstance(example, dict):
                        title = example.get("title", f"Example {i+1}")
                        code = example.get("code", "")
                        formatted_sections.append(f"  {title}: {code[:200]}...")
                    else:
                        formatted_sections.append(f"  Example {i+1}: {str(example)[:200]}...")
            else:
                formatted_sections.append(f"  {str(examples)[:300]}...")
        
        # Best practices
        best_practices = api_docs_context.get("best_practices", {})
        if isinstance(best_practices, dict) and best_practices:
            practices = best_practices.get("best_practices", [])
            if practices:
                formatted_sections.append("Best Practices:")
                for practice in practices[:3]:  # Limit to 3 practices
                    if isinstance(practice, dict):
                        practice_text = practice.get("practice", "")
                        formatted_sections.append(f"  - {practice_text}")
                    else:
                        formatted_sections.append(f"  - {str(practice)}")
        
        return "\n".join(formatted_sections) if formatted_sections else "No additional API context available"

    def _build_implementation_prompt(self,
                                   scenarios: List[Dict[str, Any]],
                                   constraints: Dict[str, Any],
                                   framework: str,
                                   optimization_level: str,
                                   api_docs_context: Dict[str, Any] = {}) -> str:
        """Build comprehensive prompt for implementation generation using SDD principles."""
        
        scenarios_text = "\n".join([
            f"Scenario: {s.get('scenario', 'Unnamed')}\n"
            f"Given: {s.get('given', '')}\n"
            f"When: {s.get('when', '')}\n"
            f"Then: {s.get('then', '')}\n"
            for s in scenarios
        ])

        # Include API documentation context if available
        api_context_section = ""
        if api_docs_context.get("enhanced"):
            api_context_section = f"""
TECHNICAL CONTEXT (for implementation guidance):
{self._format_api_docs_for_prompt(api_docs_context)}

"""

        return f"""
You are implementing a Specification-Driven Development (SDD) system where behavior is paramount and implementation details are secondary.

BEHAVIORAL SPECIFICATION (this is your requirements document):
{scenarios_text}

OPERATIONAL CONSTRAINTS (non-functional requirements):
{json.dumps(constraints, indent=2) if constraints else "Infer reasonable defaults from scenarios"}

IMPLEMENTATION CONTEXT:
- Framework preference: {framework}
- Optimization focus: {optimization_level}

{api_context_section}SDD IMPLEMENTATION PRINCIPLES:
1. Each scenario describes WHAT the system should do, not HOW
2. Your code must make every scenario demonstrably true
3. Structure code to match scenario organization, not technical layers  
4. Every public function should map clearly to scenario actions
5. Error messages must reference violated scenarios, not technical details
6. Include behavior-focused comments linking code sections to scenarios
7. Generate comprehensive observability that explains business behavior
8. Code is disposable, behavior is sacred - choose the clearest implementation

MANDATORY DELIVERABLES:
1. "main_module": Complete executable Python code with scenario mappings
2. "test_module": Scenario-based tests that read like executable documentation
3. "scenario_mappings": Map each scenario to the primary function implementing it
4. "behavioral_contracts": Key interfaces that enforce scenario behavior
5. "observability_points": Where business behavior is logged/monitored

ARCHITECTURAL REQUIREMENTS:
- Every code path must trace back to a scenario
- Business logic should be separated from technical infrastructure
- Error handling must explain which scenario was violated
- Include logging that explains behavior in business terms
- Tests should verify scenarios directly, not just technical functionality

CRITICAL IMPLEMENTATION STANDARDS:
1. Generate ACTUAL EXECUTABLE PYTHON CODE (no placeholders or descriptions)
2. Include comprehensive type hints and behavior-focused docstrings
3. Implement proper error handling with scenario-referenced messages
4. Follow {framework} best practices while prioritizing behavior clarity
5. Make code {optimization_level} but never at the expense of scenario clarity

Return implementation in this JSON format:
{{
  "main_module": "COMPLETE EXECUTABLE PYTHON CODE with scenario comments",
  "test_module": "SCENARIO-BASED TESTS that read like documentation",
  "dependencies": ["packages chosen to best implement behaviors"],
  "service_name": "descriptive name reflecting primary scenarios",
  "scenario_mappings": {{
    "scenario_name": "primary_function_implementing_it"
  }},
  "behavioral_contracts": ["key interfaces that enforce scenarios"],
  "observability_points": ["where behavior is logged/monitored"],
  "api_endpoints": ["endpoint": "which scenario it serves"],
  "architecture_rationale": "why this design best serves the scenarios"
}}

Remember: Generate code that a new developer could understand by reading scenarios first, then seeing how code implements them. The test suite should read like executable documentation of the scenarios.
"""

    def _build_refinement_prompt(self,
                               current_code: str,
                               current_tests: str,
                               test_failures: List[Dict[str, Any]],
                               quality_issues: List[Dict[str, Any]],
                               refactoring_suggestions: List[Dict[str, Any]],
                               target_quality_score: int,
                               preserve_functionality: bool) -> str:
        """Build prompt for implementation refinement using SDD principles."""
        
        return f"""
You are refining an SDD implementation to better satisfy its behavioral specification while addressing quality concerns.

CURRENT SYSTEM STATE:
```python
{current_code}
```

BEHAVIORAL TESTS:
```python
{current_tests}
```

BEHAVIORAL VIOLATIONS (highest priority):
{json.dumps(test_failures, indent=2) if test_failures else "All scenarios currently satisfied"}

CODE QUALITY CONCERNS (secondary priority):
{json.dumps(quality_issues, indent=2) if quality_issues else "No quality issues identified"}

ARCHITECTURAL IMPROVEMENTS (consider if helpful):
{json.dumps(refactoring_suggestions, indent=2) if refactoring_suggestions else "Current architecture is adequate"}

REFINEMENT GOALS:
- Behavioral Integrity: {preserve_functionality} (must remain 100%)
- Code Quality Target: {target_quality_score}/100
- Scenario Clarity: How obviously code maps to scenarios

SDD REFINEMENT PRIORITIES:
1. Fix any behavioral violations (failed scenario tests) 
2. Improve scenario-to-code mapping clarity
3. Enhance observability of business behavior
4. Simplify complex code that obscures behavior
5. Add missing edge cases discovered through testing
6. Improve error messages to reference scenarios
7. Strengthen behavioral contracts and interfaces

REFINEMENT PRINCIPLES:
- Each issue represents a gap between specified and actual behavior
- Code changes must make the scenarios true
- Don't just fix symptoms - ensure the scenario is properly modeled
- Add observability to prove the behavior is now correct
- Trace each issue back to its originating scenario
- Ensure changes don't break other scenarios
- Improve code clarity around the problematic behavior

CRITICAL STANDARDS:
1. Generate ACTUAL EXECUTABLE PYTHON CODE (no placeholders)
2. Maintain all existing behavioral guarantees
3. Enhance scenario traceability in code structure
4. Improve business-focused error messages and logging
5. Strengthen the mapping between scenarios and implementation

Return refined system in JSON format:
{{
  "main_module": "COMPLETE EXECUTABLE PYTHON CODE with clearer behavior mapping",
  "test_module": "ENHANCED TESTS with better scenario coverage",
  "dependencies": ["updated if architectural changes require"],
  "behavioral_fixes": ["how each test failure was resolved"],
  "clarity_improvements": ["how scenario mapping was made clearer"],
  "edge_cases_added": ["new scenarios discovered and handled"],
  "observability_enhancements": ["better behavior monitoring added"],
  "scenario_mappings": {{"scenario": "implementing_function"}},
  "quality_score_justification": "why the code now meets quality targets"
}}

Remember: In SDD, code quality means "how clearly does this implement the specified behavior?" not just traditional metrics. The refined code should demonstrably satisfy all scenarios with obvious traceability.
"""

    def _parse_implementation_response(self, response: str, include_tests: bool = True) -> Dict[str, Any]:
        """Parse AI response into implementation structure."""
        try:
            # Extract JSON from response
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                json_text = response[start:end].strip()
            elif "{" in response and "}" in response:
                # Try to find JSON-like content in the response
                start = response.find("{")
                end = response.rfind("}") + 1
                json_text = response[start:end].strip()
            else:
                json_text = response.strip()

            data = json.loads(json_text)
            
            # Ensure required fields and validate that we have actual code, not placeholders
            main_module = data.get("main_module", "")
            if not main_module or main_module in ["main_module.py", "main_module", "# No implementation generated"]:
                self.logger.warning("AI generated placeholder content instead of actual code")
                main_module = self._generate_fallback_code_from_scenarios(data.get("scenarios", []))
            
            test_module = data.get("test_module", "")
            if include_tests and (not test_module or test_module in ["test_module.py", "test_module", "# No tests generated"]):
                test_module = self._generate_fallback_tests(main_module)
            
            implementation = {
                "main_module": main_module,
                "dependencies": data.get("dependencies", ["pytest"]),
                "service_name": data.get("service_name", "generated_service"),
                "module_name": data.get("module_name", "main"),
                "key_classes": data.get("key_classes", []),
                "key_functions": data.get("key_functions", [])
            }

            if include_tests:
                implementation["test_module"] = test_module

            if "api_endpoints" in data:
                implementation["api_endpoints"] = data["api_endpoints"]

            return implementation

        except (json.JSONDecodeError, KeyError) as e:
            self.logger.warning(f"Failed to parse implementation response: {e}. Response: {response[:200]}...")
            return self._fallback_implementation_structure()

    def _parse_code_generation_response(self, response: str) -> Dict[str, Any]:
        """Parse code generation response."""
        try:
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                json_text = response[start:end].strip()
            else:
                json_text = response.strip()

            return json.loads(json_text)

        except json.JSONDecodeError:
            return {
                "module_code": "# Code generation failed",
                "dependencies": [],
                "key_functions": [],
                "complexity_estimate": "unknown"
            }

    def _parse_optimization_response(self, response: str) -> Dict[str, Any]:
        """Parse optimization response."""
        try:
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                json_text = response[start:end].strip()
            else:
                json_text = response.strip()

            return json.loads(json_text)

        except json.JSONDecodeError:
            return {
                "optimized_code": "# Optimization failed",
                "optimizations_applied": [],
                "constraint_compliance": {},
                "performance_notes": "Optimization failed"
            }

    async def _fallback_implementation_generation(self,
                                                scenarios: List[Dict[str, Any]],
                                                constraints: Dict[str, Any],
                                                framework: str) -> Dict[str, Any]:
        """Fallback implementation when AI is not available."""
        
        # Since handoff_flow has been archived, provide a simple fallback
        return self._fallback_implementation_structure()

    def _fallback_implementation_structure(self) -> Dict[str, Any]:
        """Basic fallback implementation structure."""
        return {
            "main_module": '''\
# Basic CRUD implementation template
from typing import Dict, List, Optional, Any
import json

class DataStore:
    """Simple in-memory data store for CRUD operations."""
    
    def __init__(self):
        self._data: Dict[str, Any] = {}
        self._next_id = 1
    
    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Store new data and return it with an ID."""
        item_id = str(self._next_id)
        self._next_id += 1
        
        item = {"id": item_id, **data}
        self._data[item_id] = item
        return item
    
    def read(self, item_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve data by ID."""
        return self._data.get(item_id)
    
    def update(self, item_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update existing data."""
        if item_id in self._data:
            self._data[item_id].update(data)
            return self._data[item_id]
        return None
    
    def delete(self, item_id: str) -> bool:
        """Remove data by ID."""
        if item_id in self._data:
            del self._data[item_id]
            return True
        return False
    
    def list_all(self) -> List[Dict[str, Any]]:
        """Get all stored data."""
        return list(self._data.values())

# Example usage
if __name__ == "__main__":
    store = DataStore()
    
    # Create
    item = store.create({"name": "test", "value": 42})
    print(f"Created: {item}")
    
    # Read
    retrieved = store.read(item["id"])
    print(f"Retrieved: {retrieved}")
    
    # Update
    updated = store.update(item["id"], {"value": 100})
    print(f"Updated: {updated}")
    
    # List all
    all_items = store.list_all()
    print(f"All items: {all_items}")
    
    # Delete
    deleted = store.delete(item["id"])
    print(f"Deleted: {deleted}")
''',
            "test_module": '''\
import pytest
from main import DataStore

class TestDataStore:
    """Test cases for DataStore CRUD operations."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.store = DataStore()
    
    def test_create_item(self):
        """Test creating a new item."""
        data = {"name": "test_item", "value": 42}
        item = self.store.create(data)
        
        assert "id" in item
        assert item["name"] == "test_item"
        assert item["value"] == 42
    
    def test_read_existing_item(self):
        """Test reading an existing item."""
        # Create an item first
        created = self.store.create({"name": "test"})
        
        # Read it back
        retrieved = self.store.read(created["id"])
        
        assert retrieved is not None
        assert retrieved["id"] == created["id"]
        assert retrieved["name"] == "test"
    
    def test_read_nonexistent_item(self):
        """Test reading a non-existent item."""
        result = self.store.read("nonexistent")
        assert result is None
    
    def test_update_existing_item(self):
        """Test updating an existing item."""
        # Create an item
        created = self.store.create({"name": "original", "value": 1})
        
        # Update it
        updated = self.store.update(created["id"], {"name": "updated", "value": 2})
        
        assert updated is not None
        assert updated["name"] == "updated"
        assert updated["value"] == 2
        assert updated["id"] == created["id"]
    
    def test_update_nonexistent_item(self):
        """Test updating a non-existent item."""
        result = self.store.update("nonexistent", {"name": "test"})
        assert result is None
    
    def test_delete_existing_item(self):
        """Test deleting an existing item."""
        # Create an item
        created = self.store.create({"name": "to_delete"})
        
        # Delete it
        result = self.store.delete(created["id"])
        assert result is True
        
        # Verify it's gone
        retrieved = self.store.read(created["id"])
        assert retrieved is None
    
    def test_delete_nonexistent_item(self):
        """Test deleting a non-existent item."""
        result = self.store.delete("nonexistent")
        assert result is False
    
    def test_list_all_items(self):
        """Test listing all items."""
        # Start with empty store
        assert self.store.list_all() == []
        
        # Add some items
        item1 = self.store.create({"name": "first"})
        item2 = self.store.create({"name": "second"})
        
        # List all
        all_items = self.store.list_all()
        assert len(all_items) == 2
        assert item1 in all_items
        assert item2 in all_items
''',
            "dependencies": ["pytest"],
            "service_name": "data_store_service",
            "module_name": "main",
            "key_classes": ["DataStore"],
            "key_functions": ["create", "read", "update", "delete", "list_all"]
        }

    # Template initialization methods

    async def _init_microservice_template(self, workspace_path: Path):
        """Initialize microservice template."""
        (workspace_path / "requirements.txt").write_text("fastapi\npydantic\npytest\n")
        (workspace_path / "__init__.py").write_text("")
        (workspace_path / "README.md").write_text(f"# {workspace_path.name}\n\nMicroservice implementation\n")

    async def _init_library_template(self, workspace_path: Path):
        """Initialize library template."""
        (workspace_path / "requirements.txt").write_text("pytest\n")
        (workspace_path / "__init__.py").write_text("")
        (workspace_path / "setup.py").write_text(f"""
from setuptools import setup, find_packages

setup(
    name="{workspace_path.name}",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[],
)
""")

    async def _init_cli_template(self, workspace_path: Path):
        """Initialize CLI template."""
        (workspace_path / "requirements.txt").write_text("click\npytest\n")
        (workspace_path / "__init__.py").write_text("")

    async def _init_webapp_template(self, workspace_path: Path):
        """Initialize web app template."""
        (workspace_path / "requirements.txt").write_text("fastapi\nuvicorn\npytest\n")
        (workspace_path / "__init__.py").write_text("")

    def _generate_init_file(self, implementation_code: str, module_name: str) -> str:
        """Generate proper __init__.py that re-exports everything."""
        exports = self._extract_exports_from_code(implementation_code)
        
        if not exports:
            return ""
            
        init_content = f"from .{module_name} import {', '.join(exports)}\n\n"
        init_content += f"__all__ = {exports}\n"
        
        return init_content

    def _extract_exports_from_code(self, code: str) -> List[str]:
        """Extract class and function names from implementation code using AST."""
        exports = []
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    exports.append(node.name)
                elif isinstance(node, ast.FunctionDef) and not node.name.startswith('_'):
                    # Include public functions as well
                    exports.append(node.name)
        except SyntaxError:
            # Fallback to regex-based extraction if AST fails
            lines = code.split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('class ') and '(' in line:
                    class_name = line.split('class ')[1].split('(')[0].split(':')[0].strip()
                    exports.append(class_name)
                elif line.startswith('class ') and ':' in line:
                    class_name = line.split('class ')[1].split(':')[0].strip()
                    exports.append(class_name)
                    
        return exports

    def _generate_fallback_code_from_scenarios(self, scenarios: List[Dict[str, Any]]) -> str:
        """Generate basic implementation code from scenarios when AI fails."""
        
        # If no scenarios provided, return basic CRUD
        if not scenarios:
            return self._fallback_implementation_structure()["main_module"]
        
        # Analyze scenarios to determine what kind of implementation to generate
        scenario_text = " ".join([
            f"{s.get('scenario', '')} {s.get('when', '')} {s.get('then', '')}"
            for s in scenarios
        ]).lower()
        
        if any(keyword in scenario_text for keyword in ['store', 'create', 'add', 'save']):
            # CRUD-like scenarios detected
            return self._generate_crud_implementation(scenarios)
        elif any(keyword in scenario_text for keyword in ['api', 'endpoint', 'request', 'response']):
            # API scenarios detected
            return self._generate_api_implementation(scenarios)
        else:
            # Generic service scenarios
            return self._generate_service_implementation(scenarios)
    
    def _generate_fallback_tests(self, main_module: str) -> str:
        """Generate basic tests for the main module."""
        # Extract class names from the main module
        classes = []
        functions = []
        try:
            tree = ast.parse(main_module)
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    classes.append(node.name)
                elif isinstance(node, ast.FunctionDef) and not node.name.startswith('_'):
                    functions.append(node.name)
        except SyntaxError:
            # Fallback if AST parsing fails
            lines = main_module.split('\n')
            for line in lines:
                if line.strip().startswith('class '):
                    class_name = line.split('class ')[1].split('(')[0].split(':')[0].strip()
                    classes.append(class_name)
                elif line.strip().startswith('def ') and not line.strip().startswith('def _'):
                    func_name = line.split('def ')[1].split('(')[0].strip()
                    functions.append(func_name)
        
        # Generate basic tests
        test_code = "import pytest\n"
        if classes:
            test_code += f"from main import {', '.join(classes)}\n\n"
        
        for class_name in classes:
            test_code += f"""
class Test{class_name}:
    \"\"\"Test cases for {class_name}.\"\"\\"
    
    def setup_method(self):
        \"\"\"Set up test fixtures.\"\"\"
        self.instance = {class_name}()
    
    def test_instantiation(self):
        \"\"\"Test that {class_name} can be instantiated.\"\"\"
        assert self.instance is not None
        assert isinstance(self.instance, {class_name})
"""
        
        for func_name in functions:
            test_code += f"""
def test_{func_name}():
    \"\"\"Test {func_name} function.\"\"\"
    # TODO: Add specific test logic for {func_name}
    assert True  # Placeholder test
"""
        
        return test_code.strip()
    
    def _generate_crud_implementation(self, scenarios: List[Dict[str, Any]]) -> str:
        """Generate CRUD implementation based on scenarios."""
        return '''\
from typing import Dict, List, Optional, Any
import json
from datetime import datetime

class DataManager:
    """Enhanced data management with CRUD operations."""
    
    def __init__(self):
        self._storage: Dict[str, Any] = {}
        self._next_id = 1
        self._created_at = datetime.now()
    
    def create_item(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new item and store it."""
        if not data:
            raise ValueError("Data cannot be empty")
        
        item_id = str(self._next_id)
        self._next_id += 1
        
        item = {
            "id": item_id,
            "created_at": datetime.now().isoformat(),
            **data
        }
        
        self._storage[item_id] = item
        return item
    
    def get_item(self, item_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve an item by ID."""
        return self._storage.get(item_id)
    
    def update_item(self, item_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an existing item."""
        if item_id not in self._storage:
            return None
        
        item = self._storage[item_id]
        item.update(updates)
        item["updated_at"] = datetime.now().isoformat()
        
        return item
    
    def delete_item(self, item_id: str) -> bool:
        """Delete an item by ID."""
        if item_id in self._storage:
            del self._storage[item_id]
            return True
        return False
    
    def list_items(self) -> List[Dict[str, Any]]:
        """Get all items."""
        return list(self._storage.values())
    
    def search_items(self, query: str) -> List[Dict[str, Any]]:
        """Search items by query string."""
        results = []
        query_lower = query.lower()
        
        for item in self._storage.values():
            # Search in all string values
            for value in item.values():
                if isinstance(value, str) and query_lower in value.lower():
                    results.append(item)
                    break
        
        return results

# Example usage
if __name__ == "__main__":
    manager = DataManager()
    
    # Create items
    item1 = manager.create_item({"name": "Sample Item", "category": "test"})
    item2 = manager.create_item({"name": "Another Item", "category": "demo"})
    
    print(f"Created items: {[item1['id'], item2['id']]}")
    
    # Read item
    retrieved = manager.get_item(item1["id"])
    print(f"Retrieved: {retrieved}")
    
    # Update item
    updated = manager.update_item(item1["id"], {"status": "active"})
    print(f"Updated: {updated}")
    
    # List all
    all_items = manager.list_items()
    print(f"Total items: {len(all_items)}")
    
    # Search
    search_results = manager.search_items("Sample")
    print(f"Search results: {len(search_results)}")
        '''.strip()
    
    def _generate_api_implementation(self, scenarios: List[Dict[str, Any]]) -> str:
        """Generate API implementation based on scenarios."""
        return '''\
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import uvicorn

app = FastAPI(title="Generated API", version="1.0.0")

# Data models
class ItemCreate(BaseModel):
    name: str
    data: Dict[str, Any] = {}

class ItemResponse(BaseModel):
    id: str
    name: str
    data: Dict[str, Any]
    created_at: str

class ItemUpdate(BaseModel):
    name: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

# In-memory storage
storage: Dict[str, Dict[str, Any]] = {}
next_id = 1

@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "API is running", "status": "healthy"}

@app.post("/items/", response_model=ItemResponse)
async def create_item(item: ItemCreate):
    """Create a new item."""
    global next_id
    
    item_id = str(next_id)
    next_id += 1
    
    from datetime import datetime
    new_item = {
        "id": item_id,
        "name": item.name,
        "data": item.data,
        "created_at": datetime.now().isoformat()
    }
    
    storage[item_id] = new_item
    return ItemResponse(**new_item)

@app.get("/items/{item_id}", response_model=ItemResponse)
async def get_item(item_id: str):
    """Get an item by ID."""
    if item_id not in storage:
        raise HTTPException(status_code=404, detail="Item not found")
    
    return ItemResponse(**storage[item_id])

@app.put("/items/{item_id}", response_model=ItemResponse)
async def update_item(item_id: str, updates: ItemUpdate):
    """Update an existing item."""
    if item_id not in storage:
        raise HTTPException(status_code=404, detail="Item not found")
    
    item = storage[item_id]
    
    if updates.name is not None:
        item["name"] = updates.name
    if updates.data is not None:
        item["data"] = updates.data
    
    from datetime import datetime
    item["updated_at"] = datetime.now().isoformat()
    
    return ItemResponse(**item)

@app.delete("/items/{item_id}")
async def delete_item(item_id: str):
    """Delete an item."""
    if item_id not in storage:
        raise HTTPException(status_code=404, detail="Item not found")
    
    del storage[item_id]
    return {"message": "Item deleted successfully"}

@app.get("/items/", response_model=List[ItemResponse])
async def list_items():
    """List all items."""
    return [ItemResponse(**item) for item in storage.values()]

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
        '''.strip()
    
    def _generate_service_implementation(self, scenarios: List[Dict[str, Any]]) -> str:
        """Generate generic service implementation based on scenarios."""
        return '''\
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProcessingService:
    """Generic service for processing data based on scenarios."""
    
    def __init__(self):
        self.state: Dict[str, Any] = {}
        self.history: List[Dict[str, Any]] = []
        self.initialized_at = datetime.now()
        logger.info("ProcessingService initialized")
    
    def process_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming request data."""
        try:
            logger.info(f"Processing request: {request_data}")
            
            # Record the request in history
            request_record = {
                "timestamp": datetime.now().isoformat(),
                "request": request_data,
                "status": "processing"
            }
            self.history.append(request_record)
            
            # Basic processing logic
            result = self._perform_processing(request_data)
            
            # Update status
            request_record["status"] = "completed"
            request_record["result"] = result
            
            logger.info(f"Request processed successfully: {result}")
            return {
                "success": True,
                "result": result,
                "timestamp": request_record["timestamp"]
            }
            
        except Exception as e:
            logger.error(f"Processing failed: {e}")
            if self.history:
                self.history[-1]["status"] = "failed"
                self.history[-1]["error"] = str(e)
            
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _perform_processing(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform the actual processing logic."""
        # Update internal state
        if "state_updates" in data:
            self.state.update(data["state_updates"])
        
        # Generate response based on input
        processed_data = {}
        
        for key, value in data.items():
            if isinstance(value, str):
                processed_data[f"processed_{key}"] = value.upper()
            elif isinstance(value, (int, float)):
                processed_data[f"processed_{key}"] = value * 2
            else:
                processed_data[f"processed_{key}"] = f"Processed: {value}"
        
        return {
            "input_data": data,
            "processed_data": processed_data,
            "state_snapshot": self.state.copy(),
            "processing_time": datetime.now().isoformat()
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get current service status."""
        return {
            "status": "running",
            "initialized_at": self.initialized_at.isoformat(),
            "requests_processed": len(self.history),
            "current_state": self.state.copy(),
            "last_activity": self.history[-1]["timestamp"] if self.history else None
        }
    
    def get_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get processing history."""
        return self.history[-limit:] if self.history else []
    
    def reset_state(self) -> Dict[str, Any]:
        """Reset service state."""
        old_state = self.state.copy()
        self.state.clear()
        logger.info("Service state reset")
        
        return {
            "message": "State reset successfully",
            "previous_state": old_state,
            "reset_at": datetime.now().isoformat()
        }

# Example usage
if __name__ == "__main__":
    service = ProcessingService()
    
    # Example request processing
    test_data = {
        "name": "test_request",
        "value": 42,
        "action": "process",
        "state_updates": {"last_action": "test"}
    }
    
    result = service.process_request(test_data)
    print(f"Processing result: {result}")
    
    status = service.get_status()
    print(f"Service status: {status}")
        '''.strip()

    # Required abstract method implementations

    async def _read_resource(self, uri: str) -> str:
        """Read implementation-specific resources."""
        if uri == "implementation://templates/basic":
            return """# Basic implementation template
class Service:
    def __init__(self):
        pass
    
    def process(self, data):
        return {"status": "processed", "data": data}
"""
        elif uri == "implementation://examples/microservice":
            return """# FastAPI microservice template
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class RequestModel(BaseModel):
    data: str

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/process")
def process(request: RequestModel):
    return {"result": f"processed: {request.data}"}
"""
        return f"Resource not found: {uri}"

    async def _get_prompt(self, name: str, arguments: Dict[str, Any]) -> str:
        """Generate implementation-specific prompts."""
        if name == "implementation_generation":
            scenarios = arguments.get("scenarios", [])
            constraints = arguments.get("constraints", {})
            
            return f"""
Generate a Python implementation for these scenarios:

Scenarios:
{json.dumps(scenarios, indent=2)}

Constraints:
{json.dumps(constraints, indent=2)}

Create clean, well-documented code with proper error handling.
"""
        elif name == "code_refinement":
            code = arguments.get("code", "")
            issues = arguments.get("issues", [])
            
            return f"""
Refine this code to address the identified issues:

Code:
{code}

Issues to fix:
{json.dumps(issues, indent=2)}

Improve the code while maintaining functionality.
"""
        
        return f"Prompt template not found: {name}"