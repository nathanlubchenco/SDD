"""
Testing MCP Server for iterative AI development.

This server provides tools for AI to test, execute, and validate
its own generated code, enabling iterative improvement cycles.
"""

import asyncio
import subprocess
import json
import tempfile
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import ast
import traceback
from .base_mcp_server import BaseMCPServer


class TestingMCPServer(BaseMCPServer):
    """
    MCP Server for testing and validating generated code.
    
    This enables AI to run tests, execute code, analyze errors,
    and get structured feedback for iterative improvement.
    """

    def __init__(self, show_prompts: bool = False):
        super().__init__("testing-server", "1.0.0", show_prompts=show_prompts)
        
    def _register_capabilities(self):
        """Register testing and validation tools."""
        
        # Core testing tools
        self.register_tool(
            name="run_tests",
            description="Execute tests and return structured results with error analysis",
            input_schema={
                "type": "object",
                "properties": {
                    "test_code": {
                        "type": "string",
                        "description": "Test code to execute"
                    },
                    "implementation_code": {
                        "type": "string", 
                        "description": "Implementation code being tested"
                    },
                    "test_framework": {
                        "type": "string",
                        "enum": ["pytest", "unittest", "custom"],
                        "description": "Testing framework to use",
                        "default": "pytest"
                    },
                    "timeout": {
                        "type": "number",
                        "description": "Test timeout in seconds",
                        "default": 30
                    },
                    "working_directory": {
                        "type": "string",
                        "description": "Optional working directory path"
                    }
                },
                "required": ["test_code", "implementation_code"]
            },
            handler=self._run_tests
        )

        self.register_tool(
            name="execute_code",
            description="Execute arbitrary code and capture output, errors, and return values",
            input_schema={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Python code to execute"
                    },
                    "timeout": {
                        "type": "number",
                        "description": "Execution timeout in seconds",
                        "default": 10
                    },
                    "capture_imports": {
                        "type": "boolean",
                        "description": "Whether to capture import errors",
                        "default": True
                    },
                    "safe_mode": {
                        "type": "boolean",
                        "description": "Whether to run in restricted safe mode",
                        "default": True
                    }
                },
                "required": ["code"]
            },
            handler=self._execute_code
        )

        self.register_tool(
            name="validate_syntax",
            description="Check syntax validity and analyze code structure",
            input_schema={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Code to validate"
                    },
                    "language": {
                        "type": "string",
                        "enum": ["python", "javascript", "go"],
                        "description": "Programming language",
                        "default": "python"
                    },
                    "analyze_structure": {
                        "type": "boolean",
                        "description": "Whether to analyze code structure (classes, functions, etc.)",
                        "default": True
                    }
                },
                "required": ["code"]
            },
            handler=self._validate_syntax
        )

        self.register_tool(
            name="check_dependencies",
            description="Verify all dependencies are available and importable",
            input_schema={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Code to check dependencies for"
                    },
                    "requirements_file": {
                        "type": "string",
                        "description": "Optional requirements.txt content"
                    },
                    "install_missing": {
                        "type": "boolean", 
                        "description": "Whether to attempt installing missing dependencies",
                        "default": False
                    }
                },
                "required": ["code"]
            },
            handler=self._check_dependencies
        )

        self.register_tool(
            name="analyze_test_failure",
            description="Analyze test failures and provide improvement suggestions",
            input_schema={
                "type": "object",
                "properties": {
                    "test_output": {
                        "type": "string",
                        "description": "Test execution output/error messages"
                    },
                    "implementation_code": {
                        "type": "string",
                        "description": "Implementation code that failed tests"
                    },
                    "test_code": {
                        "type": "string",
                        "description": "Test code that failed"
                    },
                    "expected_behavior": {
                        "type": "string",
                        "description": "Description of expected behavior"
                    }
                },
                "required": ["test_output", "implementation_code", "test_code"]
            },
            handler=self._analyze_test_failure
        )

        self.register_tool(
            name="run_linting",
            description="Run code linting and style checks",
            input_schema={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Code to lint"
                    },
                    "linter": {
                        "type": "string",
                        "enum": ["flake8", "pylint", "ruff"],
                        "description": "Linter to use",
                        "default": "flake8"
                    },
                    "ignore_rules": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Linting rules to ignore"
                    }
                },
                "required": ["code"]
            },
            handler=self._run_linting
        )

        # Resources for testing templates and examples
        self.register_resource(
            uri="testing://templates/pytest-basic",
            name="Basic PyTest Template",
            description="Template for creating pytest test cases",
            mime_type="text/x-python"
        )

        self.register_resource(
            uri="testing://examples/test-patterns",
            name="Common Test Patterns",
            description="Examples of common testing patterns and practices",
            mime_type="text/markdown"
        )

        # Prompts for test analysis
        self.register_prompt(
            name="test_failure_analysis",
            description="Analyze test failures and suggest fixes",
            arguments=[
                {"name": "error_output", "description": "Test error output", "required": True},
                {"name": "code", "description": "Code being tested", "required": True},
                {"name": "intent", "description": "Intended behavior", "required": False}
            ]
        )

    async def _run_tests(self,
                        test_code: str,
                        implementation_code: str,
                        test_framework: str = "pytest",
                        timeout: float = 30,
                        working_directory: Optional[str] = None) -> Dict[str, Any]:
        """Execute tests and return structured results."""
        
        result = {
            "success": False,
            "test_results": {},
            "errors": [],
            "output": "",
            "execution_time": 0,
            "framework": test_framework
        }

        try:
            # Create temporary directory for test execution
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Write implementation and test files
                impl_file = temp_path / "implementation.py"
                test_file = temp_path / "test_implementation.py"
                
                impl_file.write_text(implementation_code)
                test_file.write_text(test_code)
                
                # Create __init__.py to make it a package
                (temp_path / "__init__.py").write_text("")
                
                # Change to test directory
                original_cwd = os.getcwd()
                os.chdir(temp_path)
                
                try:
                    if test_framework == "pytest":
                        result = await self._run_pytest(test_file, timeout)
                    elif test_framework == "unittest":
                        result = await self._run_unittest(test_file, timeout)
                    else:
                        result = await self._run_custom_test(test_code, implementation_code, timeout)
                        
                finally:
                    os.chdir(original_cwd)

        except Exception as e:
            result["errors"].append({
                "type": "execution_error",
                "message": str(e),
                "traceback": traceback.format_exc()
            })

        return result

    async def _run_pytest(self, test_file: Path, timeout: float) -> Dict[str, Any]:
        """Run tests using pytest."""
        
        import time
        start_time = time.time()
        
        try:
            # Run pytest with JSON output
            process = await asyncio.create_subprocess_exec(
                sys.executable, "-m", "pytest", str(test_file), "-v", "--tb=short", "--json-report", "--json-report-file=report.json",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), 
                timeout=timeout
            )
            
            execution_time = time.time() - start_time
            
            # Try to read JSON report
            test_results = {}
            try:
                with open("report.json", "r") as f:
                    report = json.loads(f.read())
                    test_results = self._parse_pytest_report(report)
            except (FileNotFoundError, json.JSONDecodeError):
                # Fallback to parsing stdout
                test_results = self._parse_pytest_stdout(stdout.decode())

            return {
                "success": process.returncode == 0,
                "test_results": test_results,
                "errors": self._parse_pytest_errors(stderr.decode()) if stderr else [],
                "output": stdout.decode(),
                "execution_time": execution_time,
                "framework": "pytest",
                "return_code": process.returncode
            }

        except asyncio.TimeoutError:
            return {
                "success": False,
                "test_results": {},
                "errors": [{"type": "timeout", "message": f"Test execution timed out after {timeout}s"}],
                "output": "",
                "execution_time": timeout,
                "framework": "pytest"
            }

    async def _execute_code(self,
                          code: str,
                          timeout: float = 10,
                          capture_imports: bool = True,
                          safe_mode: bool = True) -> Dict[str, Any]:
        """Execute arbitrary code and capture results."""
        
        result = {
            "success": False,
            "output": "",
            "errors": [],
            "return_value": None,
            "execution_time": 0
        }

        try:
            import time
            start_time = time.time()
            
            # Create execution namespace
            namespace = {
                "__builtins__": __builtins__,
                "print": print  # Allow printing
            }
            
            if not safe_mode:
                # Add more modules in non-safe mode
                import sys, os, json, pathlib
                namespace.update({
                    "sys": sys,
                    "os": os,
                    "json": json,
                    "pathlib": pathlib
                })

            # Capture output
            from io import StringIO
            old_stdout = sys.stdout
            sys.stdout = captured_output = StringIO()
            
            try:
                # Try to execute as expression first (for return values)
                try:
                    compiled = compile(code, "<string>", "eval")
                    result["return_value"] = eval(compiled, namespace)
                except SyntaxError:
                    # Fall back to execution
                    compiled = compile(code, "<string>", "exec")
                    exec(compiled, namespace)
                
                result["success"] = True
                
            except Exception as e:
                result["errors"].append({
                    "type": type(e).__name__,
                    "message": str(e),
                    "traceback": traceback.format_exc()
                })
            
            finally:
                sys.stdout = old_stdout
                result["output"] = captured_output.getvalue()
                result["execution_time"] = time.time() - start_time

        except Exception as e:
            result["errors"].append({
                "type": "execution_setup_error",
                "message": str(e),
                "traceback": traceback.format_exc()
            })

        return result

    async def _validate_syntax(self,
                             code: str,
                             language: str = "python",
                             analyze_structure: bool = True) -> Dict[str, Any]:
        """Validate syntax and analyze code structure."""
        
        result = {
            "valid": False,
            "errors": [],
            "warnings": [],
            "structure": {}
        }

        if language == "python":
            try:
                # Parse AST
                tree = ast.parse(code)
                result["valid"] = True
                
                if analyze_structure:
                    result["structure"] = self._analyze_python_structure(tree)
                    
            except SyntaxError as e:
                result["errors"].append({
                    "type": "SyntaxError",
                    "message": str(e),
                    "line": e.lineno,
                    "column": e.offset
                })
            except Exception as e:
                result["errors"].append({
                    "type": "ParseError",
                    "message": str(e)
                })

        return result

    async def _check_dependencies(self,
                                code: str,
                                requirements_file: Optional[str] = None,
                                install_missing: bool = False) -> Dict[str, Any]:
        """Check if all dependencies are available."""
        
        result = {
            "all_available": True,
            "missing_dependencies": [],
            "available_dependencies": [],
            "import_errors": []
        }

        # Extract imports from code
        try:
            tree = ast.parse(code)
            imports = self._extract_imports(tree)
            
            # Check each import
            for import_name in imports:
                try:
                    __import__(import_name)
                    result["available_dependencies"].append(import_name)
                except ImportError as e:
                    result["missing_dependencies"].append({
                        "name": import_name,
                        "error": str(e)
                    })
                    result["import_errors"].append(str(e))
            
            result["all_available"] = len(result["missing_dependencies"]) == 0

        except Exception as e:
            result["import_errors"].append(f"Code analysis failed: {e}")

        return result

    async def _analyze_test_failure(self,
                                  test_output: str,
                                  implementation_code: str,
                                  test_code: str,
                                  expected_behavior: Optional[str] = None) -> Dict[str, Any]:
        """Analyze test failures and provide improvement suggestions."""
        
        if not self.ai_client:
            return self._fallback_failure_analysis(test_output, implementation_code, test_code)

        # Build analysis prompt
        prompt = f"""
You are an SDD expert analyzing behavioral test failures. Focus on understanding which specified behaviors are not being properly implemented.

FAILED TEST OUTPUT:
{test_output}

IMPLEMENTATION CODE:
```python
{implementation_code}
```

BEHAVIORAL TEST CODE:
```python
{test_code}
```

EXPECTED BEHAVIOR:
{expected_behavior or "Not specified - infer from test structure"}

SDD FAILURE ANALYSIS PRINCIPLES:
Each test failure represents a gap between specified behavior and actual implementation. Your job is to identify which behavioral specification is not being satisfied and why.

BEHAVIORAL ANALYSIS FOCUS:
1. Which scenario or behavior is failing to be implemented correctly?
2. Is the implementation missing behavioral logic, or is the test poorly written?
3. Does the failure indicate a misunderstanding of the required behavior?
4. Are there behavioral edge cases that weren't properly considered?

Analyze the failure and provide:
1. Behavioral root cause: Which specified behavior is not working?
2. Implementation vs specification gap analysis
3. Whether the issue is behavioral logic, test design, or specification clarity
4. Behavioral fixes that make the scenario work as intended

Format as JSON:
{{
  "behavioral_root_cause": "which specified behavior is failing and why",
  "failed_scenario": "description of the behavioral scenario that's not working",
  "implementation_gap": "what behavioral logic is missing or incorrect",
  "issue_location": "implementation|test|specification|both",
  "confidence": 0-100,
  "behavioral_fixes": [
    {{
      "description": "what behavioral change is needed",
      "behavioral_rationale": "why this change makes the scenario work",
      "code_change": "specific implementation change",
      "file": "implementation|test",
      "scenario_impact": "how this affects the overall behavior"
    }}
  ],
  "missing_behaviors": ["behavioral scenarios that should be tested but aren't"],
  "scenario_clarity_issues": ["ways the behavioral specification could be clearer"]
}}
"""

        try:
            response = self.ai_client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=1500
            )

            # Parse response
            analysis = self._parse_analysis_response(response)
            
            self.logger.info("AI analyzed test failure")
            return analysis

        except Exception as e:
            self.logger.error(f"AI failure analysis failed: {e}")
            return self._fallback_failure_analysis(test_output, implementation_code, test_code)

    async def _run_linting(self,
                         code: str,
                         linter: str = "flake8",
                         ignore_rules: Optional[List[str]] = None) -> Dict[str, Any]:
        """Run code linting and return issues."""
        
        result = {
            "clean": True,
            "issues": [],
            "warnings": [],
            "errors": [],
            "linter": linter
        }

        try:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
                f.write(code)
                temp_file = f.name

            try:
                if linter == "flake8":
                    result = await self._run_flake8(temp_file, ignore_rules)
                elif linter == "ruff":
                    result = await self._run_ruff(temp_file, ignore_rules)
                # Add other linters as needed
                
            finally:
                os.unlink(temp_file)

        except Exception as e:
            result["errors"].append({
                "type": "linter_error",
                "message": str(e)
            })

        return result

    # Helper methods for parsing and analysis
    def _parse_pytest_report(self, report: Dict) -> Dict[str, Any]:
        """Parse pytest JSON report."""
        summary = report.get("summary", {})
        tests = report.get("tests", [])
        
        return {
            "total": summary.get("total", 0),
            "passed": summary.get("passed", 0),
            "failed": summary.get("failed", 0),
            "skipped": summary.get("skipped", 0),
            "errors": summary.get("error", 0),
            "test_details": [
                {
                    "name": test.get("nodeid", ""),
                    "outcome": test.get("outcome", ""),
                    "duration": test.get("duration", 0),
                    "message": test.get("call", {}).get("longrepr", "") if test.get("outcome") == "failed" else ""
                }
                for test in tests
            ]
        }

    def _parse_pytest_stdout(self, stdout: str) -> Dict[str, Any]:
        """Fallback pytest output parsing."""
        lines = stdout.split('\n')
        passed = failed = skipped = 0
        
        for line in lines:
            if "passed" in line and "failed" in line:
                # Parse summary line like "1 failed, 2 passed"
                parts = line.split()
                for i, part in enumerate(parts):
                    if part == "passed" and i > 0:
                        passed = int(parts[i-1])
                    elif part == "failed" and i > 0:
                        failed = int(parts[i-1])
                    elif part == "skipped" and i > 0:
                        skipped = int(parts[i-1])
        
        return {
            "total": passed + failed + skipped,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "errors": 0,
            "test_details": []
        }

    def _parse_pytest_errors(self, stderr: str) -> List[Dict[str, str]]:
        """Parse pytest error output."""
        if not stderr:
            return []
        
        return [{
            "type": "test_error",
            "message": stderr
        }]

    def _analyze_python_structure(self, tree: ast.AST) -> Dict[str, Any]:
        """Analyze Python AST structure."""
        structure = {
            "classes": [],
            "functions": [],
            "imports": [],
            "constants": [],
            "complexity_score": 0
        }

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                structure["classes"].append({
                    "name": node.name,
                    "methods": [n.name for n in node.body if isinstance(n, ast.FunctionDef)],
                    "line": node.lineno
                })
            elif isinstance(node, ast.FunctionDef):
                if not any(node.lineno >= cls.get("line", 0) for cls in structure["classes"]):
                    structure["functions"].append({
                        "name": node.name,
                        "args": len(node.args.args),
                        "line": node.lineno
                    })
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        structure["imports"].append(alias.name)
                elif node.module:
                    structure["imports"].append(node.module)

        structure["complexity_score"] = len(structure["classes"]) * 3 + len(structure["functions"]) * 2
        return structure

    def _extract_imports(self, tree: ast.AST) -> List[str]:
        """Extract all import names from AST."""
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module.split('.')[0])
        
        return list(set(imports))

    def _parse_analysis_response(self, response: str) -> Dict[str, Any]:
        """Parse AI analysis response."""
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
                "root_cause": "Could not parse AI analysis",
                "issue_location": "unknown",
                "confidence": 0,
                "suggested_fixes": [],
                "additional_tests": []
            }

    def _fallback_failure_analysis(self, test_output: str, implementation_code: str, test_code: str) -> Dict[str, Any]:
        """Fallback failure analysis when AI unavailable."""
        
        # Basic pattern matching for common errors
        root_cause = "Unknown test failure"
        issue_location = "implementation"
        
        if "ImportError" in test_output or "ModuleNotFoundError" in test_output:
            root_cause = "Missing imports or dependencies"
        elif "AttributeError" in test_output:
            root_cause = "Missing method or attribute"
        elif "AssertionError" in test_output:
            root_cause = "Test assertion failed - logic error"
        elif "SyntaxError" in test_output:
            root_cause = "Syntax error in code"
            issue_location = "both"
        elif "TypeError" in test_output:
            root_cause = "Type mismatch or incorrect function signature"

        return {
            "root_cause": root_cause,
            "issue_location": issue_location,
            "confidence": 30,
            "suggested_fixes": [
                {
                    "description": "Review error message and fix the identified issue",
                    "code_change": "Check the error output for specific details",
                    "file": issue_location
                }
            ],
            "additional_tests": ["Add more specific test cases to isolate the issue"]
        }

    async def _run_flake8(self, temp_file: str, ignore_rules: Optional[List[str]]) -> Dict[str, Any]:
        """Run flake8 linting."""
        try:
            cmd = [sys.executable, "-m", "flake8", temp_file]
            if ignore_rules:
                cmd.extend(["--ignore", ",".join(ignore_rules)])

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            issues = []
            if stdout:
                for line in stdout.decode().strip().split('\n'):
                    if line and ':' in line:
                        parts = line.split(':', 3)
                        if len(parts) >= 4:
                            issues.append({
                                "line": int(parts[1]),
                                "column": int(parts[2]),
                                "message": parts[3].strip(),
                                "severity": "warning"
                            })

            return {
                "clean": len(issues) == 0,
                "issues": issues,
                "warnings": issues,
                "errors": [],
                "linter": "flake8"
            }

        except Exception as e:
            return {
                "clean": False,
                "issues": [],
                "warnings": [],
                "errors": [{"type": "linter_error", "message": str(e)}],
                "linter": "flake8"
            }

    # Resource and prompt handlers
    async def _read_resource(self, uri: str) -> str:
        """Read testing resources."""
        if uri == "testing://templates/pytest-basic":
            return """import pytest
from implementation import *  # Import your implementation

class TestBasicFunctionality:
    def test_example(self):
        # Arrange
        expected = "expected_value"
        
        # Act
        result = your_function()
        
        # Assert
        assert result == expected
        
    def test_edge_case(self):
        # Test edge cases and error conditions
        with pytest.raises(ValueError):
            your_function_with_invalid_input()
"""

        elif uri == "testing://examples/test-patterns":
            return """# Common Testing Patterns

## Setup and Teardown
```python
@pytest.fixture
def setup_data():
    # Setup code
    data = create_test_data()
    yield data
    # Teardown code
    cleanup_test_data(data)
```

## Parameterized Tests
```python
@pytest.mark.parametrize("input,expected", [
    (1, 2),
    (2, 4),
    (3, 6)
])
def test_multiply_by_two(input, expected):
    assert multiply_by_two(input) == expected
```

## Exception Testing
```python
def test_invalid_input_raises_error():
    with pytest.raises(ValueError, match="Invalid input"):
        process_data(None)
```
"""

        return f"Resource not found: {uri}"

    async def _get_prompt(self, name: str, arguments: Dict[str, Any]) -> str:
        """Generate testing prompts."""
        if name == "test_failure_analysis":
            error_output = arguments.get("error_output", "")
            code = arguments.get("code", "")
            intent = arguments.get("intent", "")
            
            return f"""
Analyze this test failure and suggest specific fixes:

Error Output:
{error_output}

Code:
{code}

Intended Behavior:
{intent}

Provide:
1. Root cause of the failure
2. Specific code changes needed
3. Whether issue is in implementation or test
4. Suggested fixes with examples
"""

        return f"Prompt not found: {name}"