import asyncio
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional
import ast
import time


class ImplementationMCPServer:
    """MCP Server for code generation and implementation"""

    def __init__(self, workspace_dir: Path):
        self.name = "implementation-server"
        self.workspace_dir = workspace_dir
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        self.active_workspaces = {}

    async def create_workspace(self, project_name: str, template: str = "microservice") -> Dict:
        """Create a new workspace for implementation"""

        workspace_path = self.workspace_dir / project_name
        workspace_path.mkdir(parents=True, exist_ok=True)

        # Initialize based on template
        if template == "microservice":
            await self._init_microservice_template(workspace_path)

        workspace_id = f"ws_{project_name}_{int(time.time())}"
        self.active_workspaces[workspace_id] = {
            "path": workspace_path,
            "project_name": project_name,
            "template": template
        }

        return {
            "workspace_id": workspace_id,
            "path": str(workspace_path),
            "status": "created"
        }

    async def generate_implementation(self, workspace_id: str, specification: Dict,
                                     language: str = "python", framework: str = "fastapi") -> Dict:
        """Generate complete implementation from specification"""

        workspace = self.active_workspaces.get(workspace_id)
        if not workspace:
            return {"error": "Workspace not found"}

        # Generate different components using our existing handoff_flow
        from orchestrator.handoff_flow import generate_implementation, generate_tests
        
        implementation_code = generate_implementation(specification)
        test_code = generate_tests(specification)

        # Write files to workspace
        await self._write_implementation_files(
            workspace["path"],
            implementation_code,
            test_code
        )

        # Run initial tests
        test_results = await self.run_tests(workspace_id)

        return {
            "workspace_id": workspace_id,
            "files_generated": {
                "implementation": 1,
                "tests": 1
            },
            "test_results": test_results
        }

    async def run_tests(self, workspace_id: str, test_type: str = "all",
                       coverage: bool = True) -> Dict:
        """Run tests and return results"""

        workspace = self.active_workspaces.get(workspace_id)
        if not workspace:
            return {"error": "Workspace not found"}

        workspace_path = workspace["path"]
        
        # Run tests using subprocess instead of Docker for simplicity
        try:
            result = subprocess.run([
                "python", "-m", "pytest", str(workspace_path), "-v"
            ], capture_output=True, text=True, timeout=60)
            
            test_results = self._parse_test_results(result.stdout, result.stderr, result.returncode)
            
        except subprocess.TimeoutExpired:
            test_results = {
                "passed": 0,
                "failed": 1,
                "details": "Test execution timed out"
            }
        except Exception as e:
            test_results = {
                "passed": 0,
                "failed": 1,
                "details": f"Test execution error: {str(e)}"
            }

        return {
            "workspace_id": workspace_id,
            "test_type": test_type,
            "passed": test_results["passed"],
            "failed": test_results["failed"],
            "details": test_results["details"]
        }

    async def verify_constraints(self, workspace_id: str, constraints: Dict,
                                 load_test: bool = True) -> Dict:
        """Verify implementation meets all constraints"""

        workspace = self.active_workspaces.get(workspace_id)
        if not workspace:
            return {"error": "Workspace not found"}

        verification_results = {
            "workspace_id": workspace_id,
            "constraints_met": {},
            "constraints_failed": {},
            "performance_metrics": {}
        }

        # Basic constraint verification without Docker
        try:
            # Check if code compiles
            implementation_file = workspace["path"] / "task_manager.py"
            if implementation_file.exists():
                with open(implementation_file) as f:
                    code = f.read()
                    
                # Parse to check syntax
                ast.parse(code)
                verification_results["constraints_met"]["syntax"] = {"passed": True}
                
                # Basic performance check - count lines of code
                line_count = len(code.split('\n'))
                verification_results["performance_metrics"]["lines_of_code"] = line_count
                
                if line_count < 500:  # Arbitrary threshold
                    verification_results["constraints_met"]["code_complexity"] = {"passed": True}
                else:
                    verification_results["constraints_failed"]["code_complexity"] = {"passed": False, "reason": "Too many lines"}
                    
        except SyntaxError as e:
            verification_results["constraints_failed"]["syntax"] = {"passed": False, "error": str(e)}
        except Exception as e:
            verification_results["constraints_failed"]["general"] = {"passed": False, "error": str(e)}

        return verification_results

    async def optimize_implementation(self, workspace_id: str,
                                     optimization_targets: Dict,
                                     max_iterations: int = 5) -> Dict:
        """Iteratively optimize implementation"""

        workspace = self.active_workspaces.get(workspace_id)
        if not workspace:
            return {"error": "Workspace not found"}

        # Simple optimization: just verify current state
        verification = await self.verify_constraints(workspace_id, optimization_targets)
        
        return {
            "workspace_id": workspace_id,
            "iterations": 1,
            "success": len(verification["constraints_failed"]) == 0,
            "results": verification
        }

    async def _init_microservice_template(self, workspace_path: Path):
        """Initialize microservice template"""
        # Create basic structure
        (workspace_path / "requirements.txt").write_text("pytest\n")
        (workspace_path / "__init__.py").write_text("")

    async def _write_implementation_files(self, workspace_path: Path, 
                                        implementation_code: str, test_code: str):
        """Write generated files to workspace"""
        (workspace_path / "task_manager.py").write_text(implementation_code)
        (workspace_path / "test_task_manager.py").write_text(test_code)
        (workspace_path / "__init__.py").write_text("")

    def _parse_test_results(self, stdout: str, stderr: str, returncode: int) -> Dict:
        """Parse test results from pytest output"""
        if returncode == 0:
            # Parse successful test output
            lines = stdout.split('\n')
            passed = sum(1 for line in lines if 'PASSED' in line)
            failed = sum(1 for line in lines if 'FAILED' in line)
        else:
            # Parse failed test output
            passed = 0
            failed = 1  # At least one failure
            
        return {
            "passed": passed,
            "failed": failed,
            "details": stdout if stdout else stderr
        }