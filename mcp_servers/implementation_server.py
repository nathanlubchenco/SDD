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

    def __init__(self, workspace_dir: Optional[Path] = None):
        super().__init__("implementation-server", "1.0.0")
        self.workspace_dir = workspace_dir or Path("workspaces")
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
            return await self._fallback_implementation_generation(scenarios, constraints, target_framework)

        # Build comprehensive prompt for implementation generation
        prompt = self._build_implementation_prompt(
            scenarios, constraints, target_framework, optimization_level
        )

        try:
            response = self.ai_client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=4000
            )

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

        # Extract current code
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
            response = self.ai_client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=4000
            )

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

    def _build_implementation_prompt(self,
                                   scenarios: List[Dict[str, Any]],
                                   constraints: Dict[str, Any],
                                   framework: str,
                                   optimization_level: str) -> str:
        """Build comprehensive prompt for implementation generation."""
        
        scenarios_text = "\n".join([
            f"Scenario: {s.get('scenario', 'Unnamed')}\n"
            f"Given: {s.get('given', '')}\n"
            f"When: {s.get('when', '')}\n"
            f"Then: {s.get('then', '')}\n"
            for s in scenarios
        ])

        return f"""
You are an expert Python developer. Generate a complete, production-ready implementation based on these specifications:

BEHAVIORAL SCENARIOS:
{scenarios_text}

CONSTRAINTS:
{json.dumps(constraints, indent=2) if constraints else "No specific constraints"}

FRAMEWORK: {framework}
OPTIMIZATION LEVEL: {optimization_level}

Requirements:
1. Generate clean, well-structured Python code
2. Include comprehensive type hints
3. Add detailed docstrings for all classes and methods
4. Implement proper error handling
5. Follow {framework} best practices if applicable
6. Include comprehensive test code using pytest
7. Make the code {optimization_level} for the specified optimization level

Return your implementation in this JSON format:
{{
  "main_module": "complete Python implementation code",
  "test_module": "comprehensive pytest test code",
  "dependencies": ["list", "of", "required", "packages"],
  "service_name": "suggested service name",
  "module_name": "main module name",
  "key_classes": ["list", "of", "main", "classes"],
  "key_functions": ["list", "of", "main", "functions"],
  "api_endpoints": ["list", "of", "endpoints", "if", "applicable"]
}}

Generate high-quality, production-ready code that fully implements all scenarios.
"""

    def _build_refinement_prompt(self,
                               current_code: str,
                               current_tests: str,
                               test_failures: List[Dict[str, Any]],
                               quality_issues: List[Dict[str, Any]],
                               refactoring_suggestions: List[Dict[str, Any]],
                               target_quality_score: int,
                               preserve_functionality: bool) -> str:
        """Build prompt for implementation refinement."""
        
        return f"""
You are an expert Python developer. Refine this implementation to address the identified issues and improve quality.

CURRENT IMPLEMENTATION:
```python
{current_code}
```

CURRENT TESTS:
```python
{current_tests}
```

TEST FAILURES TO ADDRESS:
{json.dumps(test_failures, indent=2) if test_failures else "No test failures"}

QUALITY ISSUES TO FIX:
{json.dumps(quality_issues, indent=2) if quality_issues else "No quality issues"}

REFACTORING SUGGESTIONS:
{json.dumps(refactoring_suggestions, indent=2) if refactoring_suggestions else "No suggestions"}

TARGET QUALITY SCORE: {target_quality_score}/100
PRESERVE FUNCTIONALITY: {preserve_functionality}

Instructions:
1. Fix all test failures while preserving functionality
2. Address all quality issues (complexity, readability, maintainability)
3. Apply relevant refactoring suggestions
4. Improve code structure and design patterns
5. Enhance error handling and edge cases
6. Optimize for the target quality score
7. Update tests to match any interface changes

Return the refined implementation in JSON format:
{{
  "main_module": "refined Python implementation",
  "test_module": "updated test code",
  "dependencies": ["updated", "dependencies"],
  "improvements_made": ["list", "of", "improvements"],
  "issues_fixed": ["list", "of", "fixed", "issues"],
  "quality_enhancements": ["list", "of", "quality", "improvements"]
}}

Focus on creating high-quality, maintainable code that meets the target quality score.
"""

    def _parse_implementation_response(self, response: str, include_tests: bool = True) -> Dict[str, Any]:
        """Parse AI response into implementation structure."""
        try:
            # Extract JSON from response
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                json_text = response[start:end].strip()
            else:
                json_text = response.strip()

            data = json.loads(json_text)
            
            # Ensure required fields
            implementation = {
                "main_module": data.get("main_module", "# No implementation generated"),
                "dependencies": data.get("dependencies", ["pytest"]),
                "service_name": data.get("service_name", "generated_service"),
                "module_name": data.get("module_name", "main"),
                "key_classes": data.get("key_classes", []),
                "key_functions": data.get("key_functions", [])
            }

            if include_tests:
                implementation["test_module"] = data.get("test_module", "# No tests generated")

            if "api_endpoints" in data:
                implementation["api_endpoints"] = data["api_endpoints"]

            return implementation

        except (json.JSONDecodeError, KeyError) as e:
            self.logger.warning(f"Failed to parse implementation response: {e}")
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
        
        # Import existing handoff flow for fallback
        try:
            from ..orchestrator.handoff_flow import generate_implementation, generate_tests, _generate_filenames
            
            # Convert scenarios to old format
            spec = {"scenarios": scenarios, "constraints": constraints}
            
            implementation_code = generate_implementation(spec)
            test_code = generate_tests(spec)
            filenames = _generate_filenames(spec)
            
            return {
                "main_module": implementation_code,
                "test_module": test_code,
                "dependencies": ["fastapi", "pydantic", "pytest"],
                "service_name": filenames.get("module_name", "service"),
                "module_name": filenames.get("module_name", "main"),
                "key_classes": [],
                "key_functions": [],
                "metadata": {"generated_with_ai": False, "fallback_used": True}
            }

        except ImportError:
            return self._fallback_implementation_structure()

    def _fallback_implementation_structure(self) -> Dict[str, Any]:
        """Basic fallback implementation structure."""
        return {
            "main_module": """
# Basic implementation template
class Service:
    def __init__(self):
        pass
    
    def process(self, data):
        return {"status": "processed", "data": data}
""",
            "test_module": """
import pytest
from main import Service

def test_service():
    service = Service()
    result = service.process({"test": "data"})
    assert result["status"] == "processed"
""",
            "dependencies": ["pytest"],
            "service_name": "basic_service",
            "module_name": "main",
            "key_classes": ["Service"],
            "key_functions": ["process"]
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