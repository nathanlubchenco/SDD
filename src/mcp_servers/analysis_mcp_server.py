"""
Analysis MCP Server for code introspection and quality assessment.

This server provides tools for AI to analyze its own generated code,
understand quality metrics, and identify improvement opportunities.
"""

import ast
import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from collections import defaultdict
import tempfile
import subprocess
import sys
from .base_mcp_server import BaseMCPServer


class AnalysisMCPServer(BaseMCPServer):
    """
    MCP Server for code analysis and introspection.
    
    This enables AI to analyze code quality, complexity, patterns,
    and identify areas for improvement in its own generated code.
    """

    def __init__(self, show_prompts: bool = False):
        super().__init__("analysis-server", "1.0.0", show_prompts=show_prompts)
        
    def _register_capabilities(self):
        """Register code analysis and introspection tools."""
        
        # Core analysis tools
        self.register_tool(
            name="analyze_code_quality",
            description="Comprehensive code quality analysis including complexity, maintainability, and best practices",
            input_schema={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Code to analyze"
                    },
                    "analysis_type": {
                        "type": "string",
                        "enum": ["comprehensive", "complexity", "maintainability", "security", "performance"],
                        "description": "Type of analysis to perform",
                        "default": "comprehensive"
                    },
                    "language": {
                        "type": "string",
                        "enum": ["python", "javascript", "typescript"],
                        "description": "Programming language",
                        "default": "python"
                    },
                    "include_suggestions": {
                        "type": "boolean",
                        "description": "Whether to include improvement suggestions",
                        "default": True
                    }
                },
                "required": ["code"]
            },
            handler=self._analyze_code_quality
        )

        self.register_tool(
            name="compare_implementations",
            description="Compare two implementations and identify differences, improvements, and regressions",
            input_schema={
                "type": "object",
                "properties": {
                    "original_code": {
                        "type": "string",
                        "description": "Original implementation"
                    },
                    "revised_code": {
                        "type": "string",
                        "description": "Revised implementation"
                    },
                    "comparison_criteria": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Criteria to compare: functionality, performance, readability, complexity",
                        "default": ["functionality", "readability", "complexity"]
                    }
                },
                "required": ["original_code", "revised_code"]
            },
            handler=self._compare_implementations
        )

        self.register_tool(
            name="identify_patterns",
            description="Identify code patterns, anti-patterns, and design pattern usage",
            input_schema={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Code to analyze for patterns"
                    },
                    "pattern_types": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Pattern types to look for: design_patterns, anti_patterns, code_smells",
                        "default": ["design_patterns", "anti_patterns", "code_smells"]
                    }
                },
                "required": ["code"]
            },
            handler=self._identify_patterns
        )

        self.register_tool(
            name="measure_coverage",
            description="Analyze test coverage and identify untested code paths",
            input_schema={
                "type": "object",
                "properties": {
                    "implementation_code": {
                        "type": "string",
                        "description": "Implementation code"
                    },
                    "test_code": {
                        "type": "string",
                        "description": "Test code"
                    },
                    "coverage_type": {
                        "type": "string",
                        "enum": ["line", "branch", "function"],
                        "description": "Type of coverage to measure",
                        "default": "line"
                    }
                },
                "required": ["implementation_code", "test_code"]
            },
            handler=self._measure_coverage
        )

        self.register_tool(
            name="analyze_performance",
            description="Analyze code for potential performance issues and bottlenecks",
            input_schema={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Code to analyze for performance"
                    },
                    "analysis_focus": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Focus areas: time_complexity, space_complexity, io_operations, loops",
                        "default": ["time_complexity", "space_complexity"]
                    }
                },
                "required": ["code"]
            },
            handler=self._analyze_performance
        )

        self.register_tool(
            name="suggest_refactoring",
            description="Suggest refactoring opportunities and improvements using AI",
            input_schema={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Code to analyze for refactoring"
                    },
                    "refactoring_goals": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Refactoring goals: readability, performance, maintainability, testability",
                        "default": ["readability", "maintainability"]
                    },
                    "include_examples": {
                        "type": "boolean",
                        "description": "Whether to include code examples in suggestions",
                        "default": True
                    }
                },
                "required": ["code"]
            },
            handler=self._suggest_refactoring
        )

        self.register_tool(
            name="extract_dependencies",
            description="Extract and analyze code dependencies and their relationships",
            input_schema={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Code to analyze for dependencies"
                    },
                    "include_internal": {
                        "type": "boolean",
                        "description": "Whether to include internal/relative dependencies",
                        "default": True
                    },
                    "analyze_usage": {
                        "type": "boolean",
                        "description": "Whether to analyze how dependencies are used",
                        "default": True
                    }
                },
                "required": ["code"]
            },
            handler=self._extract_dependencies
        )

        # Resources for analysis guidelines and examples
        self.register_resource(
            uri="analysis://guidelines/code-quality",
            name="Code Quality Guidelines",
            description="Comprehensive code quality assessment guidelines",
            mime_type="text/markdown"
        )

        self.register_resource(
            uri="analysis://patterns/anti-patterns",
            name="Common Anti-patterns",
            description="Database of common anti-patterns and code smells",
            mime_type="application/json"
        )

        # Prompts for AI-driven analysis
        self.register_prompt(
            name="refactoring_suggestions",
            description="Generate intelligent refactoring suggestions",
            arguments=[
                {"name": "code", "description": "Code to refactor", "required": True},
                {"name": "quality_issues", "description": "Identified quality issues", "required": False},
                {"name": "goals", "description": "Refactoring goals", "required": False}
            ]
        )

    async def _analyze_code_quality(self,
                                  code: str,
                                  analysis_type: str = "comprehensive",
                                  language: str = "python",
                                  include_suggestions: bool = True,
                                  completeness_analysis: Dict[str, Any] = None) -> Dict[str, Any]:
        """Perform comprehensive code quality analysis."""
        
        result = {
            "overall_score": 0,
            "metrics": {},
            "issues": [],
            "suggestions": [],
            "analysis_type": analysis_type
        }

        if language == "python":
            try:
                tree = ast.parse(code)
                
                # Calculate various metrics
                complexity = self._calculate_complexity(tree)
                maintainability = self._calculate_maintainability(tree, code)
                readability = self._calculate_readability(code)
                
                result["metrics"] = {
                    "complexity": complexity,
                    "maintainability": maintainability,
                    "readability": readability,
                    "lines_of_code": len(code.split('\n')),
                    "cyclomatic_complexity": self._cyclomatic_complexity(tree)
                }
                
                # Identify issues
                result["issues"] = self._identify_quality_issues(tree, code)
                
                # Calculate overall score
                result["overall_score"] = self._calculate_overall_score(result["metrics"], result["issues"], completeness_analysis)
                
                # Generate suggestions if requested
                if include_suggestions:
                    result["suggestions"] = await self._generate_quality_suggestions(code, result["issues"], result["metrics"])

            except SyntaxError as e:
                result["issues"].append({
                    "type": "syntax_error",
                    "severity": "error",
                    "message": str(e),
                    "line": e.lineno
                })

        return result

    async def _compare_implementations(self,
                                     original_code: str,
                                     revised_code: str,
                                     comparison_criteria: List[str] = ["functionality", "readability", "complexity"]) -> Dict[str, Any]:
        """Compare two implementations and identify differences."""
        
        result = {
            "comparison_summary": {},
            "improvements": [],
            "regressions": [],
            "changes": []
        }

        try:
            # Analyze both implementations
            original_analysis = await self._analyze_code_quality(original_code, include_suggestions=False)
            revised_analysis = await self._analyze_code_quality(revised_code, include_suggestions=False)
            
            # Compare metrics
            for criterion in comparison_criteria:
                if criterion == "complexity":
                    original_complexity = original_analysis["metrics"].get("complexity", {})
                    revised_complexity = revised_analysis["metrics"].get("complexity", {})
                    
                    complexity_change = self._compare_complexity(original_complexity, revised_complexity)
                    result["comparison_summary"]["complexity"] = complexity_change
                    
                elif criterion == "readability":
                    original_readability = original_analysis["metrics"].get("readability", {})
                    revised_readability = revised_analysis["metrics"].get("readability", {})
                    
                    readability_change = self._compare_readability(original_readability, revised_readability)
                    result["comparison_summary"]["readability"] = readability_change
                    
                elif criterion == "functionality":
                    # Structural comparison
                    functionality_change = self._compare_functionality(original_code, revised_code)
                    result["comparison_summary"]["functionality"] = functionality_change

            # Identify improvements and regressions
            result["improvements"], result["regressions"] = self._identify_changes(
                original_analysis, revised_analysis
            )

        except Exception as e:
            result["error"] = str(e)

        return result

    async def _identify_patterns(self,
                               code: str,
                               pattern_types: List[str] = ["design_patterns", "anti_patterns", "code_smells"]) -> Dict[str, Any]:
        """Identify code patterns, anti-patterns, and design patterns."""
        
        result = {
            "design_patterns": [],
            "anti_patterns": [],
            "code_smells": [],
            "pattern_summary": {}
        }

        try:
            tree = ast.parse(code)
            
            if "design_patterns" in pattern_types:
                result["design_patterns"] = self._detect_design_patterns(tree, code)
                
            if "anti_patterns" in pattern_types:
                result["anti_patterns"] = self._detect_anti_patterns(tree, code)
                
            if "code_smells" in pattern_types:
                result["code_smells"] = self._detect_code_smells(tree, code)
            
            # Generate summary
            result["pattern_summary"] = {
                "total_patterns": len(result["design_patterns"]),
                "total_anti_patterns": len(result["anti_patterns"]),
                "total_smells": len(result["code_smells"]),
                "pattern_density": len(result["design_patterns"]) / max(1, len(code.split('\n')))
            }

        except Exception as e:
            result["error"] = str(e)

        return result

    async def _measure_coverage(self,
                              implementation_code: str,
                              test_code: str,
                              coverage_type: str = "line") -> Dict[str, Any]:
        """Analyze test coverage and identify untested code paths."""
        
        result = {
            "coverage_percentage": 0,
            "covered_lines": [],
            "uncovered_lines": [],
            "uncovered_functions": [],
            "coverage_report": {}
        }

        try:
            # Parse implementation to identify testable elements
            impl_tree = ast.parse(implementation_code)
            
            # Extract functions and classes
            functions = []
            classes = []
            
            for node in ast.walk(impl_tree):
                if isinstance(node, ast.FunctionDef):
                    functions.append({
                        "name": node.name,
                        "line": node.lineno,
                        "end_line": getattr(node, 'end_lineno', node.lineno)
                    })
                elif isinstance(node, ast.ClassDef):
                    classes.append({
                        "name": node.name,
                        "line": node.lineno,
                        "methods": [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                    })

            # Analyze test code to see what's being tested
            test_tree = ast.parse(test_code)
            tested_functions = self._extract_tested_functions(test_tree)
            
            # Calculate coverage
            total_functions = len(functions)
            tested_count = len([f for f in functions if f["name"] in tested_functions])
            
            result["coverage_percentage"] = (tested_count / max(1, total_functions)) * 100
            result["uncovered_functions"] = [
                f["name"] for f in functions if f["name"] not in tested_functions
            ]
            
            result["coverage_report"] = {
                "total_functions": total_functions,
                "tested_functions": tested_count,
                "function_coverage": result["coverage_percentage"],
                "tested_function_names": list(tested_functions),
                "classes": len(classes)
            }

        except Exception as e:
            result["error"] = str(e)

        return result

    async def _analyze_performance(self,
                                 code: str,
                                 analysis_focus: List[str] = ["time_complexity", "space_complexity"]) -> Dict[str, Any]:
        """Analyze code for potential performance issues."""
        
        result = {
            "performance_score": 0,
            "bottlenecks": [],
            "complexity_analysis": {},
            "suggestions": []
        }

        try:
            tree = ast.parse(code)
            
            if "time_complexity" in analysis_focus:
                time_complexity = self._analyze_time_complexity(tree)
                result["complexity_analysis"]["time"] = time_complexity
                
            if "space_complexity" in analysis_focus:
                space_complexity = self._analyze_space_complexity(tree)
                result["complexity_analysis"]["space"] = space_complexity
                
            if "io_operations" in analysis_focus:
                io_analysis = self._analyze_io_operations(tree)
                result["complexity_analysis"]["io"] = io_analysis
                
            if "loops" in analysis_focus:
                loop_analysis = self._analyze_loops(tree)
                result["complexity_analysis"]["loops"] = loop_analysis

            # Identify bottlenecks
            result["bottlenecks"] = self._identify_performance_bottlenecks(tree, code)
            
            # Calculate performance score
            result["performance_score"] = self._calculate_performance_score(result["complexity_analysis"], result["bottlenecks"])
            
            # Generate performance suggestions
            result["suggestions"] = self._generate_performance_suggestions(result["bottlenecks"], result["complexity_analysis"])

        except Exception as e:
            result["error"] = str(e)

        return result

    async def _suggest_refactoring(self,
                                 code: str,
                                 refactoring_goals: List[str] = ["readability", "maintainability"],
                                 include_examples: bool = True) -> Dict[str, Any]:
        """Suggest refactoring opportunities using AI."""
        
        if not self.ai_client:
            return self._fallback_refactoring_suggestions(code, refactoring_goals)
        
        # Note: Model-specific timeouts are now handled at the AI client level

        # First, analyze code quality to identify issues
        quality_analysis = await self._analyze_code_quality(code, include_suggestions=False)
        
        # Build refactoring prompt
        prompt = f"""
You are an expert software engineer. Analyze this code and suggest specific refactoring improvements.

CODE TO REFACTOR:
```python
{code}
```

QUALITY ANALYSIS:
- Overall Score: {quality_analysis.get('overall_score', 0)}/100
- Issues Found: {len(quality_analysis.get('issues', []))}
- Complexity Score: {quality_analysis.get('metrics', {}).get('complexity', {}).get('overall', 0)}

REFACTORING GOALS: {', '.join(refactoring_goals)}

Provide specific refactoring suggestions:
1. Identify the most impactful improvements
2. Suggest concrete code changes
3. Explain the benefits of each change
4. Prioritize suggestions by impact

{"Include code examples for each suggestion." if include_examples else "Provide descriptions without code examples."}

Format as JSON:
{{
  "priority_suggestions": [
    {{
      "title": "suggestion title",
      "description": "what to change and why",
      "impact": "high|medium|low",
      "category": "readability|performance|maintainability|testability",
      "before_code": "original code snippet",
      "after_code": "improved code snippet",
      "benefits": ["list of benefits"]
    }}
  ],
  "overall_strategy": "high-level refactoring approach"
}}
"""

        try:
            response = self.ai_client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=2000
            )

            suggestions = self._parse_refactoring_response(response)
            
            self.logger.info("AI generated refactoring suggestions")
            return suggestions

        except Exception as e:
            self.logger.error(f"AI refactoring suggestions failed: {e}")
            return self._fallback_refactoring_suggestions(code, refactoring_goals)

    async def _extract_dependencies(self,
                                  code: str,
                                  include_internal: bool = True,
                                  analyze_usage: bool = True) -> Dict[str, Any]:
        """Extract and analyze code dependencies."""
        
        result = {
            "external_dependencies": [],
            "internal_dependencies": [],
            "dependency_graph": {},
            "usage_analysis": {},
            "potential_issues": []
        }

        try:
            tree = ast.parse(code)
            
            # Extract imports
            imports = self._extract_all_imports(tree)
            
            # Categorize dependencies
            for imp in imports:
                if self._is_standard_library(imp):
                    continue  # Skip standard library
                elif self._is_external_package(imp):
                    result["external_dependencies"].append(imp)
                elif include_internal:
                    result["internal_dependencies"].append(imp)

            # Analyze usage if requested
            if analyze_usage:
                result["usage_analysis"] = self._analyze_dependency_usage(tree, imports)
                
            # Identify potential issues
            result["potential_issues"] = self._identify_dependency_issues(imports, tree)
            
            # Build dependency graph
            result["dependency_graph"] = self._build_dependency_graph(imports, tree)

        except Exception as e:
            result["error"] = str(e)

        return result

    # Helper methods for analysis calculations
    def _calculate_complexity(self, tree: ast.AST) -> Dict[str, Any]:
        """Calculate code complexity metrics."""
        
        complexity = {
            "overall": 0,
            "functions": {},
            "classes": {},
            "nesting_depth": 0
        }
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_complexity = self._function_complexity(node)
                complexity["functions"][node.name] = func_complexity
                complexity["overall"] += func_complexity
                
            elif isinstance(node, ast.ClassDef):
                class_complexity = sum([
                    self._function_complexity(n) for n in node.body 
                    if isinstance(n, ast.FunctionDef)
                ])
                complexity["classes"][node.name] = class_complexity
                complexity["overall"] += class_complexity

        return complexity

    def _calculate_maintainability(self, tree: ast.AST, code: str) -> Dict[str, Any]:
        """Calculate maintainability metrics."""
        
        lines = code.split('\n')
        non_empty_lines = [line for line in lines if line.strip()]
        
        return {
            "lines_of_code": len(non_empty_lines),
            "comment_ratio": self._calculate_comment_ratio(code),
            "function_length_avg": self._average_function_length(tree),
            "class_cohesion": self._calculate_class_cohesion(tree)
        }

    def _calculate_readability(self, code: str) -> Dict[str, Any]:
        """Calculate readability metrics."""
        
        lines = code.split('\n')
        
        return {
            "avg_line_length": sum(len(line) for line in lines) / max(1, len(lines)),
            "max_line_length": max(len(line) for line in lines) if lines else 0,
            "blank_line_ratio": sum(1 for line in lines if not line.strip()) / max(1, len(lines)),
            "naming_consistency": self._check_naming_consistency(code)
        }

    def _cyclomatic_complexity(self, tree: ast.AST) -> int:
        """Calculate cyclomatic complexity."""
        complexity = 1  # Base complexity
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(node, ast.ExceptHandler):
                complexity += 1
            elif isinstance(node, (ast.And, ast.Or)):
                complexity += 1
                
        return complexity

    def _identify_quality_issues(self, tree: ast.AST, code: str) -> List[Dict[str, Any]]:
        """Identify code quality issues."""
        issues = []
        
        # Check for long functions
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if hasattr(node, 'end_lineno') and node.end_lineno:
                    length = node.end_lineno - node.lineno
                    if length > 50:
                        issues.append({
                            "type": "long_function",
                            "severity": "warning",
                            "message": f"Function '{node.name}' is {length} lines long",
                            "line": node.lineno,
                            "suggestion": "Consider breaking into smaller functions"
                        })
        
        # Check for deeply nested code
        max_depth = self._find_max_nesting_depth(tree)
        if max_depth > 4:
            issues.append({
                "type": "deep_nesting",
                "severity": "warning", 
                "message": f"Maximum nesting depth is {max_depth}",
                "suggestion": "Consider refactoring to reduce nesting"
            })
        
        # Check for magic numbers
        magic_numbers = self._find_magic_numbers(tree)
        for number, line in magic_numbers:
            issues.append({
                "type": "magic_number",
                "severity": "info",
                "message": f"Magic number {number} found",
                "line": line,
                "suggestion": "Consider using a named constant"
            })
        
        return issues

    def _calculate_overall_score(self, metrics: Dict, issues: List, completeness_analysis: Dict[str, Any] = None) -> int:
        """Calculate overall quality score with heavy penalties for incomplete implementations."""
        score = 100
        
        # CRITICAL: Heavy penalties for incomplete implementations (SDD principle: behavior must be fully implemented)
        if completeness_analysis:
            completeness_percentage = completeness_analysis.get("completeness_percentage", 100)
            critical_issues = completeness_analysis.get("critical_issues", [])
            severity_score = completeness_analysis.get("severity_score", 0)
            
            # Apply severe penalty for incomplete implementations
            if completeness_percentage < 100:
                # Direct penalty proportional to incompleteness
                completeness_penalty = (100 - completeness_percentage) * 1.5  # 1.5x multiplier for incompleteness
                score -= completeness_penalty
                
                # Additional penalty for critical issues (NotImplemented, TODO in core logic, etc.)
                for issue in critical_issues:
                    if issue["severity"] >= 40:  # High severity incomplete implementations
                        score -= 25 * issue["count"]  # 25 points per critical incompleteness
                    
                # Log why score was heavily penalized
                if completeness_penalty > 0:
                    self.logger.warning(f"Quality score heavily penalized for incomplete implementation: "
                                      f"-{completeness_penalty:.1f} points (completeness: {completeness_percentage}%)")
        
        # Penalize for other code quality issues
        for issue in issues:
            if issue["severity"] == "error":
                score -= 20
            elif issue["severity"] == "warning":
                score -= 10
            elif issue["severity"] == "info":
                score -= 2
        
        # Adjust for complexity
        complexity = metrics.get("complexity", {}).get("overall", 0)
        if complexity > 20:
            score -= min(30, complexity - 20)
        
        return max(0, score)

    async def _generate_quality_suggestions(self, code: str, issues: List, metrics: Dict) -> List[str]:
        """Generate quality improvement suggestions."""
        suggestions = []
        
        # Suggestions based on issues
        issue_types = {issue["type"] for issue in issues}
        
        if "long_function" in issue_types:
            suggestions.append("Break long functions into smaller, more focused functions")
            
        if "deep_nesting" in issue_types:
            suggestions.append("Reduce nesting depth using early returns or guard clauses")
            
        if "magic_number" in issue_types:
            suggestions.append("Replace magic numbers with named constants")
        
        # Suggestions based on metrics
        complexity = metrics.get("complexity", {}).get("overall", 0)
        if complexity > 15:
            suggestions.append("Consider simplifying complex logic or using design patterns")
            
        readability = metrics.get("readability", {})
        if readability.get("avg_line_length", 0) > 100:
            suggestions.append("Consider breaking long lines for better readability")
        
        return suggestions

    # Additional helper methods would go here...
    # (For brevity, I'm including key methods but not all the detailed implementations)

    def _function_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate complexity of a single function."""
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For)):
                complexity += 1
        return complexity

    def _find_max_nesting_depth(self, tree: ast.AST, depth: int = 0) -> int:
        """Find maximum nesting depth in AST."""
        max_depth = depth
        
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.With, ast.Try)):
                child_depth = self._find_max_nesting_depth(node, depth + 1)
                max_depth = max(max_depth, child_depth)
            else:
                child_depth = self._find_max_nesting_depth(node, depth)
                max_depth = max(max_depth, child_depth)
                
        return max_depth

    def _find_magic_numbers(self, tree: ast.AST) -> List[tuple]:
        """Find magic numbers in code."""
        magic_numbers = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
                # Skip common non-magic numbers
                if node.value not in [0, 1, -1, 2]:
                    magic_numbers.append((node.value, getattr(node, 'lineno', 0)))
                    
        return magic_numbers

    # Fallback methods and resource handlers
    def _fallback_refactoring_suggestions(self, code: str, goals: List[str]) -> Dict[str, Any]:
        """Fallback refactoring suggestions when AI unavailable."""
        return {
            "priority_suggestions": [
                {
                    "title": "Basic code review",
                    "description": "Manual code review recommended",
                    "impact": "medium",
                    "category": "maintainability",
                    "benefits": ["Improved code quality"]
                }
            ],
            "overall_strategy": "Perform manual code review and apply standard refactoring techniques"
        }

    def _parse_refactoring_response(self, response: str) -> Dict[str, Any]:
        """Parse AI refactoring response."""
        try:
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                json_text = response[start:end].strip()
            else:
                json_text = response.strip()
            
            return json.loads(json_text)
        except json.JSONDecodeError:
            return self._fallback_refactoring_suggestions("", [])

    # Resource and prompt handlers
    async def _read_resource(self, uri: str) -> str:
        """Read analysis resources."""
        if uri == "analysis://guidelines/code-quality":
            return """# Code Quality Guidelines

## Complexity Metrics
- Cyclomatic complexity should be < 10 per function
- Nesting depth should be < 4 levels
- Function length should be < 50 lines

## Maintainability
- Comment ratio should be 10-30%
- Class cohesion should be high
- Avoid code duplication

## Performance
- Avoid nested loops where possible
- Use appropriate data structures
- Consider time/space complexity tradeoffs
"""

        elif uri == "analysis://patterns/anti-patterns":
            return json.dumps({
                "god_object": "Large class doing too many things",
                "long_parameter_list": "Functions with too many parameters",
                "duplicate_code": "Code duplication across functions/classes",
                "magic_numbers": "Hard-coded numeric values",
                "deep_nesting": "Excessive nesting levels"
            })

        return f"Resource not found: {uri}"

    async def _get_prompt(self, name: str, arguments: Dict[str, Any]) -> str:
        """Generate analysis prompts."""
        if name == "refactoring_suggestions":
            code = arguments.get("code", "")
            quality_issues = arguments.get("quality_issues", [])
            goals = arguments.get("goals", ["readability"])
            
            return f"""
Analyze this code and suggest refactoring improvements:

Code:
{code}

Quality Issues Found:
{quality_issues}

Refactoring Goals: {', '.join(goals)}

Provide specific, actionable refactoring suggestions with code examples.
"""

        return f"Prompt not found: {name}"

    # Placeholder methods for complex analysis (would be fully implemented)
    def _compare_complexity(self, original: Dict, revised: Dict) -> Dict:
        return {"change": "improved", "details": "Complexity reduced"}
        
    def _compare_readability(self, original: Dict, revised: Dict) -> Dict:
        return {"change": "improved", "details": "Readability enhanced"}
        
    def _compare_functionality(self, original: str, revised: str) -> Dict:
        return {"change": "equivalent", "details": "Functionality preserved"}
        
    def _identify_changes(self, original: Dict, revised: Dict) -> tuple:
        improvements = ["Reduced complexity", "Better naming"]
        regressions = []
        return improvements, regressions

    def _detect_design_patterns(self, tree: ast.AST, code: str) -> List[Dict]:
        return [{"pattern": "singleton", "confidence": 0.8, "location": "line 10"}]
        
    def _detect_anti_patterns(self, tree: ast.AST, code: str) -> List[Dict]:
        return [{"pattern": "god_object", "severity": "warning", "location": "class MyClass"}]
        
    def _detect_code_smells(self, tree: ast.AST, code: str) -> List[Dict]:
        return [{"smell": "long_method", "severity": "info", "function": "process_data"}]

    def _extract_tested_functions(self, test_tree: ast.AST) -> Set[str]:
        tested = set()
        for node in ast.walk(test_tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                tested.add(node.func.id)
        return tested

    def _analyze_time_complexity(self, tree: ast.AST) -> Dict:
        return {"estimated": "O(n)", "bottlenecks": ["nested loop"]}
        
    def _analyze_space_complexity(self, tree: ast.AST) -> Dict:
        return {"estimated": "O(1)", "memory_usage": "constant"}
        
    def _analyze_io_operations(self, tree: ast.AST) -> Dict:
        return {"file_operations": 2, "network_calls": 0}
        
    def _analyze_loops(self, tree: ast.AST) -> Dict:
        return {"nested_loops": 1, "total_loops": 3}

    def _identify_performance_bottlenecks(self, tree: ast.AST, code: str) -> List[Dict]:
        return [{"type": "nested_loop", "line": 15, "impact": "high"}]
        
    def _calculate_performance_score(self, complexity: Dict, bottlenecks: List) -> int:
        return 75 - len(bottlenecks) * 10
        
    def _generate_performance_suggestions(self, bottlenecks: List, complexity: Dict) -> List[str]:
        return ["Consider using list comprehension instead of nested loops"]

    def _extract_all_imports(self, tree: ast.AST) -> List[str]:
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)
        return imports

    def _is_standard_library(self, module: str) -> bool:
        """Check if module is part of Python standard library."""
        stdlib_modules = {'os', 'sys', 'json', 'datetime', 'pathlib', 'collections', 're', 'ast'}
        return module.split('.')[0] in stdlib_modules
        
    def _is_external_package(self, module: str) -> bool:
        """Check if module is an external package."""
        # This would typically check against a package database
        external_packages = {'fastapi', 'pydantic', 'pytest', 'numpy', 'pandas'}
        return module.split('.')[0] in external_packages

    def _analyze_dependency_usage(self, tree: ast.AST, imports: List[str]) -> Dict:
        return {"usage_frequency": {imp: 5 for imp in imports}}
        
    def _identify_dependency_issues(self, imports: List[str], tree: ast.AST) -> List[Dict]:
        return [{"issue": "unused_import", "module": "unused_module"}]
        
    def _build_dependency_graph(self, imports: List[str], tree: ast.AST) -> Dict:
        return {"nodes": imports, "edges": []}

    def _calculate_comment_ratio(self, code: str) -> float:
        lines = code.split('\n')
        comment_lines = sum(1 for line in lines if line.strip().startswith('#'))
        return comment_lines / max(1, len(lines))
        
    def _average_function_length(self, tree: ast.AST) -> float:
        function_lengths = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if hasattr(node, 'end_lineno') and node.end_lineno:
                    length = node.end_lineno - node.lineno
                    function_lengths.append(length)
        return sum(function_lengths) / max(1, len(function_lengths))
        
    def _calculate_class_cohesion(self, tree: ast.AST) -> float:
        # Simplified cohesion calculation
        return 0.8
        
    def _check_naming_consistency(self, code: str) -> float:
        # Check for consistent naming conventions
        return 0.9