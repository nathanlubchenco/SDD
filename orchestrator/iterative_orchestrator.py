"""
Iterative Orchestrator for AI-driven iterative development.

This orchestrator implements the generate→test→analyze→refine loop that enables
AI to iteratively improve its own code through testing and analysis feedback.
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from mcp_servers.specification_mcp_server import SpecificationMCPServer
from mcp_servers.implementation_server import ImplementationMCPServer
from mcp_servers.testing_mcp_server import TestingMCPServer
from mcp_servers.analysis_mcp_server import AnalysisMCPServer
from mcp_servers.docker_mcp_server import DockerMCPServer


class IterativeOrchestrator:
    """
    Orchestrates iterative AI development with generate→test→refine loops.
    
    This enables AI to:
    1. Generate initial implementation from specifications
    2. Run tests and get structured feedback
    3. Analyze code quality and identify issues
    4. Refine implementation based on test results and analysis
    5. Repeat until satisfactory quality is achieved
    """

    def __init__(self, workspace_path: str, max_iterations: int = 5):
        self.workspace_path = Path(workspace_path)
        self.max_iterations = max_iterations
        self.logger = logging.getLogger(__name__)
        
        # Initialize MCP servers
        self.spec_server = SpecificationMCPServer(Path("specs"))
        self.impl_server = ImplementationMCPServer()
        self.test_server = TestingMCPServer()
        self.analysis_server = AnalysisMCPServer()
        self.docker_server = DockerMCPServer()
        
        # Track iteration history
        self.iteration_history = []
        
    async def initialize(self):
        """Initialize all MCP servers."""
        servers = [
            self.spec_server,
            self.impl_server, 
            self.test_server,
            self.analysis_server,
            self.docker_server
        ]
        
        for server in servers:
            await server.initialize()
            
        self.logger.info("All MCP servers initialized")

    async def iterative_development_cycle(self, 
                                        specification_path: str,
                                        target_quality_score: int = 80,
                                        include_docker: bool = True) -> Dict[str, Any]:
        """
        Run complete iterative development cycle from specification to deployment.
        
        Args:
            specification_path: Path to YAML specification file
            target_quality_score: Minimum quality score to achieve (0-100)
            include_docker: Whether to generate Docker artifacts
            
        Returns:
            Complete development cycle results including all iterations
        """
        
        self.logger.info(f"Starting iterative development cycle for {specification_path}")
        
        # Load and validate specification
        spec_result = await self._load_specification(specification_path)
        if not spec_result["success"]:
            return {"success": False, "error": "Failed to load specification", "details": spec_result}
        
        specification = spec_result["specification"]
        
        # Initialize iteration tracking
        cycle_result = {
            "success": False,
            "specification": specification,
            "iterations": [],
            "final_implementation": {},
            "final_quality_score": 0,
            "docker_artifacts": {},
            "cycle_summary": {}
        }
        
        current_implementation = None
        current_quality_score = 0
        
        # Iterative development loop
        for iteration in range(1, self.max_iterations + 1):
            self.logger.info(f"Starting iteration {iteration}/{self.max_iterations}")
            
            iteration_result = await self._run_iteration(
                specification=specification,
                previous_implementation=current_implementation,
                previous_quality_score=current_quality_score,
                iteration_number=iteration,
                target_quality_score=target_quality_score
            )
            
            cycle_result["iterations"].append(iteration_result)
            
            if iteration_result["success"]:
                current_implementation = iteration_result["implementation"]
                current_quality_score = iteration_result["quality_score"]
                
                # Check if we've reached target quality
                if current_quality_score >= target_quality_score:
                    self.logger.info(f"Target quality score {target_quality_score} achieved: {current_quality_score}")
                    cycle_result["success"] = True
                    break
                    
            else:
                self.logger.warning(f"Iteration {iteration} failed: {iteration_result.get('error', 'Unknown error')}")
                
        # Set final results
        if current_implementation:
            cycle_result["final_implementation"] = current_implementation
            cycle_result["final_quality_score"] = current_quality_score
            cycle_result["success"] = current_quality_score >= target_quality_score
            
        # Generate Docker artifacts if requested and we have a good implementation
        if include_docker and cycle_result["success"]:
            docker_result = await self._generate_docker_artifacts(current_implementation)
            cycle_result["docker_artifacts"] = docker_result
            
        # Generate cycle summary
        cycle_result["cycle_summary"] = self._generate_cycle_summary(cycle_result)
        
        self.logger.info(f"Iterative development cycle completed. Success: {cycle_result['success']}")
        return cycle_result

    async def _run_iteration(self,
                           specification: Dict[str, Any],
                           previous_implementation: Optional[Dict[str, Any]],
                           previous_quality_score: int,
                           iteration_number: int,
                           target_quality_score: int) -> Dict[str, Any]:
        """
        Run a single iteration of the generate→test→analyze→refine cycle.
        """
        
        iteration_result = {
            "iteration": iteration_number,
            "success": False,
            "implementation": {},
            "test_results": {},
            "analysis_results": {},
            "quality_score": 0,
            "improvements": [],
            "issues_addressed": [],
            "error": None
        }
        
        try:
            # Phase 1: Generate/Refine Implementation
            self.logger.info(f"Iteration {iteration_number}: Generating implementation")
            
            if previous_implementation is None:
                # First iteration - generate initial implementation
                impl_result = await self._generate_initial_implementation(specification)
            else:
                # Subsequent iterations - refine based on feedback
                impl_result = await self._refine_implementation(
                    specification=specification,
                    previous_implementation=previous_implementation,
                    previous_analysis=self.iteration_history[-1].get("analysis_results") if self.iteration_history else {},
                    target_quality_score=target_quality_score
                )
            
            if not impl_result["success"]:
                iteration_result["error"] = f"Implementation generation failed: {impl_result.get('error')}"
                return iteration_result
                
            implementation = impl_result["implementation"]
            iteration_result["implementation"] = implementation
            
            # Phase 2: Run Tests
            self.logger.info(f"Iteration {iteration_number}: Running tests")
            
            test_result = await self._run_comprehensive_tests(implementation)
            iteration_result["test_results"] = test_result
            
            # Phase 3: Analyze Code Quality
            self.logger.info(f"Iteration {iteration_number}: Analyzing code quality")
            
            analysis_result = await self._analyze_implementation_quality(implementation)
            iteration_result["analysis_results"] = analysis_result
            
            # Phase 4: Calculate Quality Score and Determine Next Steps
            quality_score = self._calculate_iteration_quality_score(test_result, analysis_result)
            iteration_result["quality_score"] = quality_score
            
            # Phase 5: Identify Improvements and Issues Addressed
            if previous_implementation:
                improvements, issues_addressed = await self._identify_iteration_improvements(
                    previous_implementation, implementation, previous_quality_score, quality_score
                )
                iteration_result["improvements"] = improvements
                iteration_result["issues_addressed"] = issues_addressed
            
            iteration_result["success"] = True
            
            # Store iteration in history
            self.iteration_history.append(iteration_result)
            
        except Exception as e:
            self.logger.error(f"Iteration {iteration_number} failed with exception: {e}")
            iteration_result["error"] = str(e)
            
        return iteration_result

    async def _load_specification(self, specification_path: str) -> Dict[str, Any]:
        """Load and validate specification using SpecificationMCPServer."""
        try:
            # Use MCP call to get scenarios from specification
            request = {
                "method": "tools/call",
                "params": {
                    "name": "get_scenarios",
                    "arguments": {
                        "specification_path": specification_path,
                        "include_constraints": True
                    }
                }
            }
            
            response = await self.spec_server.handle_mcp_request(request)
            
            if response.get("error"):
                return {"success": False, "error": response["error"]}
                
            return {
                "success": True,
                "specification": response["result"]["content"]
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _generate_initial_implementation(self, specification: Dict[str, Any]) -> Dict[str, Any]:
        """Generate initial implementation from specification."""
        try:
            # Use ImplementationMCPServer to generate initial code
            request = {
                "method": "tools/call",
                "params": {
                    "name": "generate_implementation",
                    "arguments": {
                        "scenarios": specification.get("scenarios", []),
                        "constraints": specification.get("constraints", {}),
                        "target_framework": "fastapi",  # Could be configurable
                        "include_tests": True,
                        "optimization_level": "balanced"
                    }
                }
            }
            
            response = await self.impl_server.handle_mcp_request(request)
            
            if response.get("error"):
                return {"success": False, "error": response["error"]}
                
            return {
                "success": True, 
                "implementation": response["result"]["content"]
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _refine_implementation(self,
                                   specification: Dict[str, Any],
                                   previous_implementation: Dict[str, Any],
                                   previous_analysis: Dict[str, Any],
                                   target_quality_score: int) -> Dict[str, Any]:
        """Refine implementation based on previous iteration feedback."""
        try:
            # Extract issues and suggestions from previous analysis
            quality_issues = previous_analysis.get("code_quality", {}).get("issues", [])
            test_failures = previous_analysis.get("test_results", {}).get("failed_tests", [])
            refactoring_suggestions = previous_analysis.get("refactoring_suggestions", {}).get("priority_suggestions", [])
            
            # Use ImplementationMCPServer to refine code
            request = {
                "method": "tools/call",
                "params": {
                    "name": "refine_implementation",
                    "arguments": {
                        "current_implementation": previous_implementation,
                        "test_failures": test_failures,
                        "quality_issues": quality_issues,
                        "refactoring_suggestions": refactoring_suggestions,
                        "target_quality_score": target_quality_score,
                        "preserve_functionality": True
                    }
                }
            }
            
            response = await self.impl_server.handle_mcp_request(request)
            
            if response.get("error"):
                return {"success": False, "error": response["error"]}
                
            return {
                "success": True,
                "implementation": response["result"]["content"] 
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _run_comprehensive_tests(self, implementation: Dict[str, Any]) -> Dict[str, Any]:
        """Run comprehensive tests using TestingMCPServer."""
        test_results = {
            "syntax_check": {},
            "unit_tests": {},
            "dependency_check": {},
            "linting": {},
            "overall_success": False
        }
        
        try:
            # Extract code from implementation
            main_code = implementation.get("main_module", "")
            test_code = implementation.get("test_module", "")
            
            # 1. Validate syntax
            syntax_request = {
                "method": "tools/call",
                "params": {
                    "name": "validate_syntax",
                    "arguments": {"code": main_code}
                }
            }
            syntax_response = await self.test_server.handle_mcp_request(syntax_request)
            test_results["syntax_check"] = syntax_response.get("result", {}).get("content", {})
            
            # 2. Check dependencies
            deps_request = {
                "method": "tools/call",
                "params": {
                    "name": "check_dependencies",
                    "arguments": {"code": main_code}
                }
            }
            deps_response = await self.test_server.handle_mcp_request(deps_request)
            test_results["dependency_check"] = deps_response.get("result", {}).get("content", {})
            
            # 3. Run linting
            lint_request = {
                "method": "tools/call",
                "params": {
                    "name": "run_linting",
                    "arguments": {"code": main_code}
                }
            }
            lint_response = await self.test_server.handle_mcp_request(lint_request)
            test_results["linting"] = lint_response.get("result", {}).get("content", {})
            
            # 4. Run unit tests if we have test code
            if test_code:
                test_request = {
                    "method": "tools/call",
                    "params": {
                        "name": "run_tests",
                        "arguments": {
                            "implementation_code": main_code,
                            "test_code": test_code,
                            "test_framework": "pytest"
                        }
                    }
                }
                test_response = await self.test_server.handle_mcp_request(test_request)
                test_results["unit_tests"] = test_response.get("result", {}).get("content", {})
            
            # Determine overall success
            test_results["overall_success"] = (
                test_results["syntax_check"].get("valid", False) and
                test_results["dependency_check"].get("all_available", False) and
                test_results["linting"].get("issues_count", 10) < 5 and
                test_results["unit_tests"].get("success", True)
            )
            
        except Exception as e:
            test_results["error"] = str(e)
            
        return test_results

    async def _analyze_implementation_quality(self, implementation: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze implementation quality using AnalysisMCPServer."""
        analysis_results = {
            "code_quality": {},
            "performance_analysis": {},
            "refactoring_suggestions": {},
            "pattern_analysis": {},
            "overall_assessment": {}
        }
        
        try:
            main_code = implementation.get("main_module", "")
            test_code = implementation.get("test_module", "")
            
            # 1. Comprehensive code quality analysis
            quality_request = {
                "method": "tools/call",
                "params": {
                    "name": "analyze_code_quality",
                    "arguments": {
                        "code": main_code,
                        "analysis_type": "comprehensive",
                        "include_suggestions": True
                    }
                }
            }
            quality_response = await self.analysis_server.handle_mcp_request(quality_request)
            analysis_results["code_quality"] = quality_response.get("result", {}).get("content", {})
            
            # 2. Performance analysis
            perf_request = {
                "method": "tools/call",
                "params": {
                    "name": "analyze_performance",
                    "arguments": {
                        "code": main_code,
                        "analysis_focus": ["time_complexity", "space_complexity", "loops"]
                    }
                }
            }
            perf_response = await self.analysis_server.handle_mcp_request(perf_request)
            analysis_results["performance_analysis"] = perf_response.get("result", {}).get("content", {})
            
            # 3. Refactoring suggestions
            refactor_request = {
                "method": "tools/call",
                "params": {
                    "name": "suggest_refactoring",
                    "arguments": {
                        "code": main_code,
                        "refactoring_goals": ["readability", "maintainability", "performance"],
                        "include_examples": True
                    }
                }
            }
            refactor_response = await self.analysis_server.handle_mcp_request(refactor_request)
            analysis_results["refactoring_suggestions"] = refactor_response.get("result", {}).get("content", {})
            
            # 4. Pattern analysis
            pattern_request = {
                "method": "tools/call",
                "params": {
                    "name": "identify_patterns",
                    "arguments": {
                        "code": main_code,
                        "pattern_types": ["design_patterns", "anti_patterns", "code_smells"]
                    }
                }
            }
            pattern_response = await self.analysis_server.handle_mcp_request(pattern_request)
            analysis_results["pattern_analysis"] = pattern_response.get("result", {}).get("content", {})
            
            # 5. Generate overall assessment
            analysis_results["overall_assessment"] = self._generate_overall_assessment(analysis_results)
            
        except Exception as e:
            analysis_results["error"] = str(e)
            
        return analysis_results

    def _calculate_iteration_quality_score(self, test_results: Dict, analysis_results: Dict) -> int:
        """Calculate overall quality score for this iteration."""
        score = 0
        
        # Test results contribution (40%)
        if test_results.get("overall_success", False):
            score += 40
        else:
            # Partial credit for individual test components
            if test_results.get("syntax_check", {}).get("valid", False):
                score += 10
            if test_results.get("dependency_check", {}).get("all_available", False):
                score += 10
            if test_results.get("linting", {}).get("issues_count", 10) < 5:
                score += 10
            if test_results.get("unit_tests", {}).get("success", False):
                score += 10
        
        # Code quality contribution (40%)
        quality_score = analysis_results.get("code_quality", {}).get("overall_score", 0)
        score += int(quality_score * 0.4)
        
        # Performance contribution (20%)
        perf_score = analysis_results.get("performance_analysis", {}).get("performance_score", 0)
        score += int(perf_score * 0.2)
        
        return min(100, max(0, score))

    async def _identify_iteration_improvements(self,
                                             previous_impl: Dict[str, Any],
                                             current_impl: Dict[str, Any],
                                             previous_score: int,
                                             current_score: int) -> Tuple[List[str], List[str]]:
        """Identify improvements made in this iteration."""
        improvements = []
        issues_addressed = []
        
        try:
            # Use AnalysisMCPServer to compare implementations
            request = {
                "method": "tools/call",
                "params": {
                    "name": "compare_implementations",
                    "arguments": {
                        "original_code": previous_impl.get("main_module", ""),
                        "revised_code": current_impl.get("main_module", ""),
                        "comparison_criteria": ["functionality", "readability", "complexity", "performance"]
                    }
                }
            }
            
            response = await self.analysis_server.handle_mcp_request(request)
            comparison = response.get("result", {}).get("content", {})
            
            improvements = comparison.get("improvements", [])
            
            # Add score improvement if applicable
            if current_score > previous_score:
                improvements.append(f"Quality score improved from {previous_score} to {current_score}")
            
        except Exception as e:
            self.logger.warning(f"Could not compare implementations: {e}")
            if current_score > previous_score:
                improvements.append(f"Quality score improved from {previous_score} to {current_score}")
                
        return improvements, issues_addressed

    async def _generate_docker_artifacts(self, implementation: Dict[str, Any]) -> Dict[str, Any]:
        """Generate Docker artifacts for the final implementation."""
        try:
            # Extract dependencies from implementation
            main_code = implementation.get("main_module", "")
            
            # Use DockerMCPServer to generate Dockerfile
            dockerfile_request = {
                "method": "tools/call",
                "params": {
                    "name": "generate_dockerfile",
                    "arguments": {
                        "code": main_code,
                        "framework": "fastapi",
                        "optimization_level": "production"
                    }
                }
            }
            
            dockerfile_response = await self.docker_server.handle_mcp_request(dockerfile_request)
            
            # Generate docker-compose.yml
            compose_request = {
                "method": "tools/call",
                "params": {
                    "name": "generate_docker_compose",
                    "arguments": {
                        "service_name": implementation.get("service_name", "app"),
                        "dependencies": implementation.get("dependencies", []),
                        "environment": "production"
                    }
                }
            }
            
            compose_response = await self.docker_server.handle_mcp_request(compose_request)
            
            return {
                "dockerfile": dockerfile_response.get("result", {}).get("content", {}),
                "docker_compose": compose_response.get("result", {}).get("content", {}),
                "success": True
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _generate_overall_assessment(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate overall assessment from all analysis results."""
        quality_score = analysis_results.get("code_quality", {}).get("overall_score", 0)
        perf_score = analysis_results.get("performance_analysis", {}).get("performance_score", 0)
        
        issues_count = len(analysis_results.get("code_quality", {}).get("issues", []))
        suggestions_count = len(analysis_results.get("refactoring_suggestions", {}).get("priority_suggestions", []))
        
        assessment = {
            "overall_quality": "excellent" if quality_score >= 90 else 
                             "good" if quality_score >= 75 else
                             "fair" if quality_score >= 60 else "poor",
            "performance_rating": "excellent" if perf_score >= 90 else
                                "good" if perf_score >= 75 else
                                "fair" if perf_score >= 60 else "poor",
            "issues_severity": "low" if issues_count <= 2 else
                             "medium" if issues_count <= 5 else "high",
            "improvement_potential": "low" if suggestions_count <= 2 else
                                   "medium" if suggestions_count <= 5 else "high",
            "ready_for_production": quality_score >= 80 and perf_score >= 70 and issues_count <= 3
        }
        
        return assessment

    def _generate_cycle_summary(self, cycle_result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary of the entire development cycle."""
        iterations = cycle_result.get("iterations", [])
        
        if not iterations:
            return {"error": "No iterations completed"}
        
        initial_score = iterations[0].get("quality_score", 0) if iterations else 0
        final_score = cycle_result.get("final_quality_score", 0)
        
        summary = {
            "total_iterations": len(iterations),
            "initial_quality_score": initial_score,
            "final_quality_score": final_score,
            "quality_improvement": final_score - initial_score,
            "target_achieved": cycle_result.get("success", False),
            "key_improvements": [],
            "remaining_issues": [],
            "development_efficiency": self._calculate_efficiency_metrics(iterations)
        }
        
        # Collect key improvements across all iterations
        for iteration in iterations:
            summary["key_improvements"].extend(iteration.get("improvements", []))
        
        # Get remaining issues from final analysis
        if iterations:
            final_analysis = iterations[-1].get("analysis_results", {})
            final_issues = final_analysis.get("code_quality", {}).get("issues", [])
            summary["remaining_issues"] = [issue.get("message", "") for issue in final_issues[:5]]
        
        return summary

    def _calculate_efficiency_metrics(self, iterations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate development efficiency metrics."""
        if not iterations:
            return {}
        
        # Quality improvement per iteration
        quality_scores = [iter.get("quality_score", 0) for iter in iterations]
        
        improvements = []
        for i in range(1, len(quality_scores)):
            improvement = quality_scores[i] - quality_scores[i-1]
            improvements.append(improvement)
        
        return {
            "avg_quality_improvement_per_iteration": sum(improvements) / max(1, len(improvements)),
            "iterations_with_improvement": sum(1 for imp in improvements if imp > 0),
            "largest_single_improvement": max(improvements) if improvements else 0,
            "convergence_rate": "fast" if len(improvements) <= 2 else
                              "medium" if len(improvements) <= 4 else "slow"
        }

    async def save_results(self, cycle_result: Dict[str, Any], output_path: str):
        """Save complete cycle results to file."""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Save main results
        with open(output_file, 'w') as f:
            json.dump(cycle_result, f, indent=2)
        
        # Save final implementation files
        if cycle_result.get("success") and cycle_result.get("final_implementation"):
            impl_dir = output_file.parent / "implementation"
            impl_dir.mkdir(exist_ok=True)
            
            implementation = cycle_result["final_implementation"]
            
            # Save main module
            if "main_module" in implementation:
                with open(impl_dir / "main.py", 'w') as f:
                    f.write(implementation["main_module"])
            
            # Save test module
            if "test_module" in implementation:
                with open(impl_dir / "test_main.py", 'w') as f:
                    f.write(implementation["test_module"])
            
            # Save Docker artifacts
            docker_artifacts = cycle_result.get("docker_artifacts", {})
            if docker_artifacts.get("success"):
                if "dockerfile" in docker_artifacts:
                    with open(impl_dir / "Dockerfile", 'w') as f:
                        f.write(docker_artifacts["dockerfile"].get("content", ""))
                
                if "docker_compose" in docker_artifacts:
                    with open(impl_dir / "docker-compose.yml", 'w') as f:
                        f.write(docker_artifacts["docker_compose"].get("content", ""))
        
        self.logger.info(f"Results saved to {output_path}")

    async def quick_iteration_test(self, code: str, target_score: int = 75) -> Dict[str, Any]:
        """
        Quick test of iteration capabilities on a code snippet.
        Useful for testing the iterative improvement system.
        """
        
        # Create mock implementation
        mock_implementation = {
            "main_module": code,
            "test_module": "# Test module placeholder",
            "dependencies": ["fastapi", "pydantic"],
            "service_name": "test_service"
        }
        
        # Run single iteration analysis and improvement
        test_results = await self._run_comprehensive_tests(mock_implementation)
        analysis_results = await self._analyze_implementation_quality(mock_implementation)
        quality_score = self._calculate_iteration_quality_score(test_results, analysis_results)
        
        result = {
            "original_code": code,
            "quality_score": quality_score,
            "test_results": test_results,
            "analysis_results": analysis_results,
            "improvement_needed": quality_score < target_score
        }
        
        # If improvement needed, try one refinement
        if quality_score < target_score:
            refined_result = await self._refine_implementation(
                specification={"scenarios": [], "constraints": {}},
                previous_implementation=mock_implementation,
                previous_analysis=analysis_results,
                target_quality_score=target_score
            )
            
            if refined_result["success"]:
                refined_impl = refined_result["implementation"]
                refined_tests = await self._run_comprehensive_tests(refined_impl)
                refined_analysis = await self._analyze_implementation_quality(refined_impl)
                refined_score = self._calculate_iteration_quality_score(refined_tests, refined_analysis)
                
                result["refined_implementation"] = refined_impl
                result["refined_quality_score"] = refined_score
                result["improvement_achieved"] = refined_score > quality_score
        
        return result