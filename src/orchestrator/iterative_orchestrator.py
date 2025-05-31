"""
Iterative Orchestrator for AI-driven iterative development.

This orchestrator implements the generate→test→analyze→refine loop that enables
AI to iteratively improve its own code through testing and analysis feedback.
"""

import asyncio
import json
import logging
import yaml
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from src.mcp_servers.specification_mcp_server import SpecificationMCPServer
from src.mcp_servers.implementation_server import ImplementationMCPServer
from src.mcp_servers.testing_mcp_server import TestingMCPServer
from src.mcp_servers.analysis_mcp_server import AnalysisMCPServer
from src.mcp_servers.docker_mcp_server import DockerMCPServer
from src.mcp_servers.api_docs_mcp_server import APIDocsMCPServer
from src.core.sdd_logger import get_logger


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

    def __init__(self, workspace_path: str, max_iterations: int = 5, verbose: bool = False, show_prompts: bool = False):
        self.workspace_path = Path(workspace_path)
        self.max_iterations = max_iterations
        self.verbose = verbose
        self.show_prompts = show_prompts
        self.logger = get_logger("sdd.orchestrator")
        
        # Initialize MCP servers
        self.spec_server = SpecificationMCPServer(Path("specs"), show_prompts=show_prompts)
        self.api_docs_server = APIDocsMCPServer(show_prompts=show_prompts)
        self.impl_server = ImplementationMCPServer(show_prompts=show_prompts, api_docs_server=self.api_docs_server)
        self.test_server = TestingMCPServer(show_prompts=show_prompts)
        self.analysis_server = AnalysisMCPServer(show_prompts=show_prompts)
        self.docker_server = DockerMCPServer(show_prompts=show_prompts)
        
        # Track iteration history
        self.iteration_history = []
    
    def _verbose_log(self, message: str, code_snippet: str = None, max_lines: int = 20):
        """Log verbose information including code snippets when in verbose mode."""
        if not self.verbose:
            return
            
        print(f"🔍 {message}")
        
        if code_snippet:
            lines = code_snippet.split('\n')
            if len(lines) > max_lines:
                # Show first few and last few lines
                shown_lines = lines[:max_lines//2] + ['...'] + lines[-(max_lines//2):]
                code_snippet = '\n'.join(shown_lines)
            
            print("📝 Code:")
            print("─" * 50)
            for i, line in enumerate(code_snippet.split('\n'), 1):
                print(f"{i:3d} | {line}")
            print("─" * 50)
    
    def _verbose_log_test_results(self, test_result: Dict[str, Any], iteration: int):
        """Log detailed test results in verbose mode."""
        print(f"🧪 Test Results for Iteration {iteration}:")
        
        syntax_check = test_result.get("syntax_check", {})
        dependency_check = test_result.get("dependency_check", {})
        linting = test_result.get("linting", {})
        unit_tests = test_result.get("unit_tests", {})
        overall_success = test_result.get("overall_success", False)
        
        print(f"   Overall Success: {'✅' if overall_success else '❌'}")
        print(f"   Syntax Valid: {'✅' if syntax_check.get('valid', False) else '❌'}")
        print(f"   Dependencies Available: {'✅' if dependency_check.get('all_available', False) else '❌'}")
        
        issues_count = linting.get("issues_count", 0)
        print(f"   Linting Issues: {issues_count} {'✅' if issues_count < 5 else '⚠️'}")
        
        if unit_tests:
            unit_success = unit_tests.get("success", False)
            print(f"   Unit Tests: {'✅' if unit_success else '❌'}")
            
        # Show specific errors if any
        if syntax_check.get("error"):
            print(f"   🔍 Syntax Error: {syntax_check['error']}")
        if dependency_check.get("missing_dependencies"):
            print(f"   🔍 Missing Dependencies: {dependency_check['missing_dependencies']}")
        if test_result.get("error"):
            print(f"   🔍 Test Error: {test_result['error']}")
    
    def _verbose_log_analysis_results(self, analysis_result: Dict[str, Any], iteration: int):
        """Log detailed analysis results in verbose mode."""
        print(f"📊 Analysis Results for Iteration {iteration}:")
        
        code_quality = analysis_result.get("code_quality", {})
        performance = analysis_result.get("performance_analysis", {})
        refactoring = analysis_result.get("refactoring_suggestions", {})
        patterns = analysis_result.get("pattern_analysis", {})
        
        overall_score = code_quality.get("overall_score", 0)
        print(f"   Code Quality Score: {overall_score}/100")
        
        perf_score = performance.get("performance_score", 0)
        print(f"   Performance Score: {perf_score}/100")
        
        issues = code_quality.get("issues", [])
        if issues:
            print(f"   🔍 Quality Issues ({len(issues)}):")
            for issue in issues[:3]:  # Show first 3 issues
                severity = issue.get("severity", "unknown")
                message = issue.get("message", "Unknown issue")
                print(f"      {severity.upper()}: {message}")
            if len(issues) > 3:
                print(f"      ... and {len(issues) - 3} more issues")
        
        suggestions = refactoring.get("priority_suggestions", [])
        if suggestions:
            print(f"   💡 Refactoring Suggestions ({len(suggestions)}):")
            for suggestion in suggestions[:2]:  # Show first 2 suggestions
                print(f"      • {suggestion.get('suggestion', 'Unknown suggestion')}")
            if len(suggestions) > 2:
                print(f"      ... and {len(suggestions) - 2} more suggestions")
    
    def _verbose_log_final_implementation(self, implementation: Dict[str, Any], cycle_result: Dict[str, Any]):
        """Log the final implementation details in verbose mode."""
        print("\n" + "="*60)
        print("🎯 FINAL IMPLEMENTATION SUMMARY")
        print("="*60)
        
        # Normalize implementation format
        normalized_impl = self._normalize_implementation_format(implementation)
        
        main_code = normalized_impl.get("main_module", "")
        test_code = normalized_impl.get("test_module", "")
        dependencies = normalized_impl.get("dependencies", [])
        service_name = normalized_impl.get("service_name", "unknown")
        
        print(f"📦 Service Name: {service_name}")
        print(f"📚 Dependencies: {', '.join(dependencies) if dependencies else 'None'}")
        print(f"📊 Final Quality Score: {cycle_result.get('final_quality_score', 0)}/100")
        print(f"🔄 Iterations Completed: {len(cycle_result.get('iterations', []))}")
        print(f"✅ Success: {'Yes' if cycle_result.get('success', False) else 'No'}")
        
        if main_code:
            lines = len(main_code.split('\n'))
            print(f"📝 Main Code: {lines} lines")
            print("\n🔍 Final Main Code:")
            self._verbose_log("", main_code, max_lines=30)
        
        if test_code and test_code.strip() != "# No tests generated":
            test_lines = len(test_code.split('\n'))
            print(f"🧪 Test Code: {test_lines} lines")
            print("\n🔍 Final Test Code:")
            self._verbose_log("", test_code, max_lines=15)
        
        # Show what should be written to files
        print("\n📁 Files that should be generated:")
        main_lines = len(main_code.split('\n')) if main_code else 0
        print(f"   • {service_name}.py ({main_lines} lines)")
        if test_code and test_code.strip() != "# No tests generated":
            test_lines = len(test_code.split('\n'))
            print(f"   • test_{service_name}.py ({test_lines} lines)")
        if dependencies:
            print(f"   • requirements.txt ({len(dependencies)} dependencies)")
        
        print("="*60)
        
    async def initialize(self):
        """Initialize all MCP servers."""
        # MCP servers are initialized in their constructors
        # This method exists for compatibility but servers are already ready
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
        
        with self.logger.correlation_context(component="orchestrator", 
                                           operation="iterative_development_cycle") as correlation_id:
            self.logger.info(f"Starting iterative development cycle for {specification_path}",
                           extra_data={
                               'specification_path': specification_path,
                               'target_quality_score': target_quality_score,
                               'include_docker': include_docker,
                               'max_iterations': self.max_iterations
                           })
            
            # Load and validate specification
            with self.logger.timed_operation("load_specification", 
                                           specification_path=specification_path):
                spec_result = await self._load_specification(specification_path)
                
            if not spec_result["success"]:
                self.logger.error("Failed to load specification", 
                                extra_data={'spec_result': spec_result})
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
            self.logger.log_iteration_start(iteration, self.max_iterations, target_quality_score)
            
            with self.logger.timed_operation(f"iteration_{iteration}", 
                                           iteration=iteration, 
                                           target_quality=target_quality_score):
                iteration_result = await self._run_iteration(
                    specification=specification,
                    previous_implementation=current_implementation,
                    previous_quality_score=current_quality_score,
                    iteration_number=iteration,
                    target_quality_score=target_quality_score
                )
            
            cycle_result["iterations"].append(iteration_result)
            
            if iteration_result["success"]:
                current_implementation = self._normalize_implementation_format(iteration_result["implementation"])
                current_quality_score = iteration_result["quality_score"]
                
                self.logger.log_iteration_complete(
                    iteration, 
                    current_quality_score,
                    iteration_result.get("improvements", []),
                    iteration_result.get("issues_addressed", [])
                )
                
                # Check if we've reached target quality
                if current_quality_score >= target_quality_score:
                    self.logger.info(f"Target quality score {target_quality_score} achieved: {current_quality_score}",
                                   quality_score=current_quality_score,
                                   iteration=iteration)
                    cycle_result["success"] = True
                    break
                    
            else:
                self.logger.warning(f"Iteration {iteration} failed: {iteration_result.get('error', 'Unknown error')}",
                                  iteration=iteration,
                                  extra_data={'error': iteration_result.get('error')})
            
        # Set final results
        if current_implementation:
            cycle_result["final_implementation"] = current_implementation
            cycle_result["final_quality_score"] = current_quality_score
            cycle_result["success"] = current_quality_score >= target_quality_score
        
        # Generate Docker artifacts if requested and we have a good implementation
        if include_docker and cycle_result["success"]:
            with self.logger.timed_operation("generate_docker_artifacts"):
                docker_result = await self._generate_docker_artifacts(current_implementation)
                cycle_result["docker_artifacts"] = docker_result
                
        # Generate cycle summary
        cycle_result["cycle_summary"] = self._generate_cycle_summary(cycle_result)
        
        # Verbose logging: Show final implementation
        if self.verbose and current_implementation:
            self._verbose_log_final_implementation(current_implementation, cycle_result)
        
        self.logger.info(f"Iterative development cycle completed. Success: {cycle_result['success']}",
                       extra_data={
                           'cycle_success': cycle_result['success'],
                           'final_quality_score': cycle_result.get('final_quality_score', 0),
                           'iterations_completed': len(cycle_result['iterations']),
                           'correlation_id': correlation_id
                       })
        
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
            with self.logger.timed_operation(f"iteration_{iteration_number}_phase_1_implementation", 
                                           iteration=iteration_number):
                self.logger.info(f"Iteration {iteration_number}: Generating implementation",
                               iteration=iteration_number)
                
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
                    self.logger.error(f"Implementation generation failed in iteration {iteration_number}",
                                    iteration=iteration_number,
                                    extra_data={'error': impl_result.get('error')})
                    return iteration_result
                    
                implementation = impl_result["implementation"]
                iteration_result["implementation"] = implementation
                
                # Verbose logging: Show generated code
                normalized_impl = self._normalize_implementation_format(implementation)
                main_code = normalized_impl.get("main_module", "")
                test_code = normalized_impl.get("test_module", "")
                
                self._verbose_log(
                    f"Generated implementation in iteration {iteration_number}",
                    main_code
                )
                
                if test_code:
                    self._verbose_log(
                        f"Generated tests in iteration {iteration_number}", 
                        test_code
                    )
                
                # Log dependencies and metadata
                if self.verbose:
                    deps = normalized_impl.get("dependencies", [])
                    service_name = normalized_impl.get("service_name", "unknown")
                    print(f"📦 Dependencies: {deps}")
                    print(f"🏷️  Service name: {service_name}")
                
                # Log code generation metrics
                if isinstance(implementation, dict) and "main_module" in implementation:
                    lines_count = len(implementation["main_module"].split('\n'))
                    self.logger.log_code_generation(
                        framework=implementation.get("metadata", {}).get("framework", "unknown"),
                        optimization_level=implementation.get("metadata", {}).get("optimization_level", "unknown"),
                        scenarios_count=implementation.get("metadata", {}).get("scenarios_count", 0),
                        lines_generated=lines_count
                    )
            
            # Phase 2: Run Tests
            with self.logger.timed_operation(f"iteration_{iteration_number}_phase_2_testing", 
                                           iteration=iteration_number):
                self.logger.info(f"Iteration {iteration_number}: Running tests", iteration=iteration_number)
                
                test_result = await self._run_comprehensive_tests(implementation)
                iteration_result["test_results"] = test_result
                
                # Verbose logging: Show test results
                if self.verbose:
                    self._verbose_log_test_results(test_result, iteration_number)
            
            # Phase 3: Analyze Code Quality
            with self.logger.timed_operation(f"iteration_{iteration_number}_phase_3_analysis", 
                                           iteration=iteration_number):
                self.logger.info(f"Iteration {iteration_number}: Analyzing code quality", iteration=iteration_number)
                
                analysis_result = await self._analyze_implementation_quality(implementation)
                iteration_result["analysis_results"] = analysis_result
                
                # Verbose logging: Show analysis results
                if self.verbose:
                    self._verbose_log_analysis_results(analysis_result, iteration_number)
            
            # Phase 4: Calculate Quality Score and Determine Next Steps
            quality_score = self._calculate_iteration_quality_score(test_result, analysis_result)
            iteration_result["quality_score"] = quality_score
            
            self.logger.log_quality_metrics(f"iteration_{iteration_number}", {
                'quality_score': quality_score,
                'test_success': test_result.get("overall_success", False),
                'code_quality_score': analysis_result.get("code_quality", {}).get("overall_score", 0),
                'performance_score': analysis_result.get("performance_analysis", {}).get("performance_score", 0)
            })
            
            # Phase 5: Identify Improvements and Issues Addressed
            if previous_implementation:
                improvements, issues_addressed = await self._identify_iteration_improvements(
                    previous_implementation, implementation, previous_quality_score, quality_score
                )
                iteration_result["improvements"] = improvements
                iteration_result["issues_addressed"] = issues_addressed
                
                # Verbose logging: Show improvements
                if self.verbose and improvements:
                    print(f"🚀 Improvements in Iteration {iteration_number}:")
                    for improvement in improvements:
                        print(f"   • {improvement}")
            
            iteration_result["success"] = True
            
            # Store iteration in history
            self.iteration_history.append(iteration_result)
            
        except Exception as e:
            self.logger.error(f"Iteration {iteration_number} failed with exception: {e}",
                            iteration=iteration_number)
            iteration_result["error"] = str(e)
            
        return iteration_result

    async def _load_specification(self, specification_path: str) -> Dict[str, Any]:
        """Load and validate specification from YAML file."""
        try:
            # Load specification directly from YAML file
            spec_path = Path(specification_path)
            if not spec_path.exists():
                return {"success": False, "error": f"Specification file not found: {specification_path}"}
            
            with open(spec_path, 'r') as f:
                specification = yaml.safe_load(f)
            
            # Validate that it has required structure
            if not isinstance(specification, dict):
                return {"success": False, "error": "Specification must be a YAML dictionary"}
            
            if "scenarios" not in specification:
                return {"success": False, "error": "Specification must contain 'scenarios' section"}
            
            # Set defaults
            if "constraints" not in specification:
                specification["constraints"] = {}
            
            return {
                "success": True,
                "specification": specification
            }
            
        except yaml.YAMLError as e:
            return {"success": False, "error": f"Invalid YAML format: {e}"}
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
                
            content = response.get("result", {}).get("content", [])
            if isinstance(content, list) and content:
                try:
                    text_content = content[0].get("text", "{}")
                    # First try to parse as JSON
                    try:
                        implementation = json.loads(text_content)
                    except json.JSONDecodeError:
                        # If that fails, try to evaluate as Python literal (for string dict representations)
                        import ast
                        implementation = ast.literal_eval(text_content)
                    
                    return {
                        "success": True,
                        "implementation": implementation
                    }
                except (json.JSONDecodeError, KeyError, ValueError, SyntaxError):
                    return {"success": False, "error": "Failed to parse implementation response"}
            else:
                return {"success": False, "error": "No implementation response"}
            
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
            # Normalize implementation format first
            normalized_impl = self._normalize_implementation_format(implementation)
            
            # Extract code from implementation
            main_code = normalized_impl.get("main_module", "")
            test_code = normalized_impl.get("test_module", "")
            
            # 1. Validate syntax
            syntax_request = {
                "method": "tools/call",
                "params": {
                    "name": "validate_syntax",
                    "arguments": {"code": main_code}
                }
            }
            syntax_response = await self.test_server.handle_mcp_request(syntax_request)
            content = syntax_response.get("result", {}).get("content", [])
            if isinstance(content, list) and content:
                try:
                    test_results["syntax_check"] = json.loads(content[0].get("text", "{}"))
                except (json.JSONDecodeError, KeyError):
                    test_results["syntax_check"] = {"valid": False, "error": "Failed to parse response"}
            else:
                test_results["syntax_check"] = {"valid": False, "error": "No response"}
            
            # 2. Check dependencies
            deps_request = {
                "method": "tools/call",
                "params": {
                    "name": "check_dependencies",
                    "arguments": {"code": main_code}
                }
            }
            deps_response = await self.test_server.handle_mcp_request(deps_request)
            content = deps_response.get("result", {}).get("content", [])
            if isinstance(content, list) and content:
                try:
                    test_results["dependency_check"] = json.loads(content[0].get("text", "{}"))
                except (json.JSONDecodeError, KeyError):
                    test_results["dependency_check"] = {"all_available": False, "error": "Failed to parse response"}
            else:
                test_results["dependency_check"] = {"all_available": False, "error": "No response"}
            
            # 3. Run linting
            lint_request = {
                "method": "tools/call",
                "params": {
                    "name": "run_linting",
                    "arguments": {"code": main_code}
                }
            }
            lint_response = await self.test_server.handle_mcp_request(lint_request)
            content = lint_response.get("result", {}).get("content", [])
            if isinstance(content, list) and content:
                try:
                    test_results["linting"] = json.loads(content[0].get("text", "{}"))
                except (json.JSONDecodeError, KeyError):
                    test_results["linting"] = {"issues_count": 99, "error": "Failed to parse response"}
            else:
                test_results["linting"] = {"issues_count": 99, "error": "No response"}
            
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
                content = test_response.get("result", {}).get("content", [])
                if isinstance(content, list) and content:
                    try:
                        test_results["unit_tests"] = json.loads(content[0].get("text", "{}"))
                    except (json.JSONDecodeError, KeyError):
                        test_results["unit_tests"] = {"success": False, "error": "Failed to parse response"}
                else:
                    test_results["unit_tests"] = {"success": False, "error": "No response"}
            
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
            # Normalize implementation format first
            normalized_impl = self._normalize_implementation_format(implementation)
            
            main_code = normalized_impl.get("main_module", "")
            test_code = normalized_impl.get("test_module", "")
            
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
            content = quality_response.get("result", {}).get("content", [])
            if isinstance(content, list) and content:
                try:
                    analysis_results["code_quality"] = json.loads(content[0].get("text", "{}"))
                except (json.JSONDecodeError, KeyError):
                    analysis_results["code_quality"] = {"overall_score": 0, "error": "Failed to parse response"}
            else:
                analysis_results["code_quality"] = {"overall_score": 0, "error": "No response"}
            
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
            content = perf_response.get("result", {}).get("content", [])
            if isinstance(content, list) and content:
                try:
                    analysis_results["performance_analysis"] = json.loads(content[0].get("text", "{}"))
                except (json.JSONDecodeError, KeyError):
                    analysis_results["performance_analysis"] = {"efficiency_score": 0, "error": "Failed to parse response"}
            else:
                analysis_results["performance_analysis"] = {"efficiency_score": 0, "error": "No response"}
            
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
            content = refactor_response.get("result", {}).get("content", [])
            if isinstance(content, list) and content:
                try:
                    analysis_results["refactoring_suggestions"] = json.loads(content[0].get("text", "{}"))
                except (json.JSONDecodeError, KeyError):
                    analysis_results["refactoring_suggestions"] = {"suggestions": [], "error": "Failed to parse response"}
            else:
                analysis_results["refactoring_suggestions"] = {"suggestions": [], "error": "No response"}
            
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
            content = pattern_response.get("result", {}).get("content", [])
            if isinstance(content, list) and content:
                try:
                    analysis_results["pattern_analysis"] = json.loads(content[0].get("text", "{}"))
                except (json.JSONDecodeError, KeyError):
                    analysis_results["pattern_analysis"] = {"patterns": [], "error": "Failed to parse response"}
            else:
                analysis_results["pattern_analysis"] = {"patterns": [], "error": "No response"}
            
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
            # Normalize implementation formats - handle case where they might be MCP response lists
            previous_normalized = self._normalize_implementation_format(previous_impl)
            current_normalized = self._normalize_implementation_format(current_impl)
            
            # Use AnalysisMCPServer to compare implementations
            request = {
                "method": "tools/call",
                "params": {
                    "name": "compare_implementations",
                    "arguments": {
                        "original_code": previous_normalized.get("main_module", ""),
                        "revised_code": current_normalized.get("main_module", ""),
                        "comparison_criteria": ["functionality", "readability", "complexity", "performance"]
                    }
                }
            }
            
            response = await self.analysis_server.handle_mcp_request(request)
            
            # Handle MCP response format - content might be a list
            content = response.get("result", {}).get("content", {})
            if isinstance(content, list) and len(content) > 0:
                # Extract from MCP response format
                content_item = content[0]
                if isinstance(content_item, dict) and "text" in content_item:
                    try:
                        comparison = json.loads(content_item["text"])
                    except json.JSONDecodeError:
                        try:
                            import ast
                            comparison = ast.literal_eval(content_item["text"])
                        except (ValueError, SyntaxError):
                            comparison = {}
                else:
                    comparison = content_item if isinstance(content_item, dict) else {}
            else:
                comparison = content if isinstance(content, dict) else {}
            
            improvements = comparison.get("improvements", [])
            
            # Add score improvement if applicable
            if current_score > previous_score:
                improvements.append(f"Quality score improved from {previous_score} to {current_score}")
            
        except Exception as e:
            self.logger.error(f"Failed to compare implementations: {e}")
            # This is a critical error that should be addressed, not silently ignored
            if current_score > previous_score:
                improvements.append(f"Quality score improved from {previous_score} to {current_score}")
                
        return improvements, issues_addressed
    
    def _normalize_implementation_format(self, implementation: Any) -> Dict[str, Any]:
        """Normalize implementation to consistent dict format, handling MCP response lists."""
        if isinstance(implementation, dict):
            # Already in correct format
            return implementation
        elif isinstance(implementation, list) and len(implementation) > 0:
            # Handle MCP response format
            impl_data = implementation[0]
            if isinstance(impl_data, dict) and "text" in impl_data:
                text_content = impl_data["text"]
                try:
                    # Try to parse as JSON first
                    return json.loads(text_content)
                except json.JSONDecodeError:
                    # Try to evaluate as Python literal
                    try:
                        import ast
                        return ast.literal_eval(text_content)
                    except (ValueError, SyntaxError):
                        self.logger.error(f"Failed to parse implementation text: {text_content[:100]}...")
                        return {}
            elif isinstance(impl_data, dict):
                # Direct dict in list
                return impl_data
        
        # Fallback for unexpected formats
        self.logger.error(f"Unexpected implementation format: {type(implementation)}")
        return {}

    async def _generate_docker_artifacts(self, implementation: Dict[str, Any]) -> Dict[str, Any]:
        """Generate Docker artifacts for the final implementation."""
        try:
            # Normalize implementation format first (defensive)
            normalized_impl = self._normalize_implementation_format(implementation)
            
            # Extract dependencies from implementation
            main_code = normalized_impl.get("main_module", "")
            
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
                        "service_name": normalized_impl.get("service_name", "app"),
                        "dependencies": normalized_impl.get("dependencies", []),
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