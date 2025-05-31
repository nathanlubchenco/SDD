"""
API Documentation MCP Server for intelligent documentation access.

This server provides tools for discovering, accessing, and analyzing API documentation
across multiple sources to enhance code generation with real, up-to-date information.
"""

import json
import asyncio
import re
import urllib.parse
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from .base_mcp_server import BaseMCPServer

@dataclass
class DocSource:
    """Represents a documentation source."""
    name: str
    base_url: str
    search_pattern: str
    doc_type: str  # "official", "community", "examples"
    priority: int  # Higher = more authoritative


class APIDocsMCPServer(BaseMCPServer):
    """
    MCP Server for intelligent API documentation access.
    
    Features:
    - Dynamic discovery of documentation sources
    - Intelligent search across multiple doc types
    - Context-aware documentation retrieval
    - Code example extraction and analysis
    """

    def __init__(self, show_prompts: bool = False):
        super().__init__("api-docs-server", "1.0.0", show_prompts=show_prompts)
        
        # Documentation sources - dynamically expandable
        self.doc_sources = self._initialize_doc_sources()
        self.cache = {}  # Simple in-memory cache
        
    def _register_capabilities(self):
        """Register API documentation tools."""
        
        # Core documentation tools
        self.register_tool(
            name="find_documentation",
            description="Intelligently find documentation for a library, framework, or concept",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "What to search for (e.g., 'FastAPI middleware', 'pytest fixtures')"
                    },
                    "context": {
                        "type": "string",
                        "description": "Additional context about the use case",
                        "default": ""
                    },
                    "doc_types": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Types of docs to search: official, community, examples, tutorials",
                        "default": ["official", "community"]
                    },
                    "programming_language": {
                        "type": "string",
                        "description": "Programming language context",
                        "default": "python"
                    }
                },
                "required": ["query"]
            },
            handler=self._find_documentation
        )

        self.register_tool(
            name="get_api_reference",
            description="Get specific API reference information for a library",
            input_schema={
                "type": "object",
                "properties": {
                    "library": {
                        "type": "string",
                        "description": "Library name (e.g., 'fastapi', 'pytest', 'pydantic')"
                    },
                    "component": {
                        "type": "string",
                        "description": "Specific component or method (e.g., 'HTTPException', 'fixture')",
                        "default": ""
                    },
                    "include_examples": {
                        "type": "boolean",
                        "description": "Whether to include code examples",
                        "default": True
                    }
                },
                "required": ["library"]
            },
            handler=self._get_api_reference
        )

        self.register_tool(
            name="find_code_examples",
            description="Find real-world code examples for specific use cases",
            input_schema={
                "type": "object",
                "properties": {
                    "use_case": {
                        "type": "string",
                        "description": "Specific use case or pattern (e.g., 'FastAPI CRUD operations')"
                    },
                    "complexity": {
                        "type": "string",
                        "enum": ["basic", "intermediate", "advanced"],
                        "description": "Complexity level of examples to find",
                        "default": "intermediate"
                    },
                    "source_preference": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Preferred sources: github, official_examples, tutorials",
                        "default": ["official_examples", "github"]
                    }
                },
                "required": ["use_case"]
            },
            handler=self._find_code_examples
        )

        self.register_tool(
            name="check_best_practices",
            description="Get best practices and common patterns for a library or framework",
            input_schema={
                "type": "object",
                "properties": {
                    "technology": {
                        "type": "string",
                        "description": "Technology to get best practices for"
                    },
                    "focus_area": {
                        "type": "string",
                        "description": "Specific area (e.g., 'testing', 'security', 'performance')",
                        "default": "general"
                    }
                },
                "required": ["technology"]
            },
            handler=self._check_best_practices
        )

        self.register_tool(
            name="discover_related_libraries",
            description="Discover libraries and tools related to a specific technology or use case",
            input_schema={
                "type": "object",
                "properties": {
                    "base_technology": {
                        "type": "string",
                        "description": "Base technology or framework"
                    },
                    "use_case": {
                        "type": "string",
                        "description": "Specific use case or need",
                        "default": ""
                    },
                    "category": {
                        "type": "string",
                        "enum": ["testing", "validation", "orm", "api", "deployment", "monitoring"],
                        "description": "Category of related tools to find",
                        "default": "general"
                    }
                },
                "required": ["base_technology"]
            },
            handler=self._discover_related_libraries
        )

        # Resources for documentation templates and guides
        self.register_resource(
            uri="docs://sources/registry",
            name="Documentation Sources Registry",
            description="Registry of available documentation sources",
            mime_type="application/json"
        )

        self.register_resource(
            uri="docs://patterns/common-apis",
            name="Common API Patterns",
            description="Common patterns across different APIs and frameworks",
            mime_type="text/markdown"
        )

    def _initialize_doc_sources(self) -> List[DocSource]:
        """Initialize documentation sources with intelligent discovery."""
        
        # Core Python ecosystem documentation
        sources = [
            # Web Frameworks
            DocSource("FastAPI", "https://fastapi.tiangolo.com", "/docs/*", "official", 100),
            DocSource("Django", "https://docs.djangoproject.com", "/en/stable/*", "official", 100),
            DocSource("Flask", "https://flask.palletsprojects.com", "/en/latest/*", "official", 100),
            
            # Testing
            DocSource("pytest", "https://docs.pytest.org", "/en/stable/*", "official", 100),
            DocSource("unittest", "https://docs.python.org/3/library/unittest.html", "", "official", 100),
            
            # Data & Validation
            DocSource("Pydantic", "https://docs.pydantic.dev", "/latest/*", "official", 100),
            DocSource("SQLAlchemy", "https://docs.sqlalchemy.org", "/en/latest/*", "official", 100),
            
            # Python Standard Library
            DocSource("Python Docs", "https://docs.python.org/3", "/library/*", "official", 100),
            
            # Community & Examples
            DocSource("Real Python", "https://realpython.com", "/search/*", "community", 80),
            DocSource("Python Package Index", "https://pypi.org", "/project/*", "community", 70),
            DocSource("GitHub Examples", "https://github.com/search", "?q=*&type=code", "examples", 60),
        ]
        
        return sources

    async def _find_documentation(self, 
                                query: str,
                                context: str = "",
                                doc_types: List[str] = ["official", "community"],
                                programming_language: str = "python") -> Dict[str, Any]:
        """Intelligently find documentation for a query."""
        
        if not self.ai_client:
            return await self._fallback_find_documentation(query, doc_types)

        # Use AI to understand the query and find appropriate documentation
        search_prompt = f"""
        You are a documentation search expert. Help find the best documentation for this query:

        QUERY: {query}
        CONTEXT: {context}
        LANGUAGE: {programming_language}
        PREFERRED DOC TYPES: {', '.join(doc_types)}

        Available documentation sources:
        {self._format_doc_sources_for_prompt()}

        Analyze the query and provide:
        1. The most relevant documentation sources
        2. Specific sections or pages to look at
        3. Key concepts or terms to focus on
        4. Alternative search terms if needed

        Format as JSON:
        {{
            "primary_sources": [
                {{
                    "source": "source_name",
                    "url_pattern": "specific_url_or_search",
                    "relevance": "why this source is relevant",
                    "sections": ["section1", "section2"]
                }}
            ],
            "search_terms": ["term1", "term2"],
            "concepts": ["concept1", "concept2"],
            "alternatives": ["alternative search if primary fails"]
        }}
        """

        try:
            self._log_prompt("find_documentation", search_prompt)
            
            response = self.ai_client.chat_completion(
                messages=[{"role": "user", "content": search_prompt}],
                temperature=0.1,
                max_tokens=1500
            )
            
            self._log_prompt("find_documentation", search_prompt, response)
            
            # Parse AI response
            search_strategy = self._parse_search_response(response)
            
            # Execute the search strategy
            results = await self._execute_documentation_search(search_strategy, query)
            
            self.logger.info(f"Found documentation for query: {query}")
            return {
                "query": query,
                "strategy": search_strategy,
                "results": results,
                "summary": self._summarize_documentation_results(results)
            }

        except Exception as e:
            self.logger.error(f"AI documentation search failed: {e}")
            return await self._fallback_find_documentation(query, doc_types)

    async def _get_api_reference(self,
                               library: str,
                               component: str = "",
                               include_examples: bool = True) -> Dict[str, Any]:
        """Get specific API reference information."""
        
        # Check cache first
        cache_key = f"api_ref_{library}_{component}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        if not self.ai_client:
            return await self._fallback_api_reference(library, component)

        # Build API reference prompt
        prompt = f"""
        You are an API documentation expert. Provide comprehensive API reference information.

        LIBRARY: {library}
        COMPONENT: {component or "main API overview"}
        INCLUDE_EXAMPLES: {include_examples}

        Provide detailed information about:
        1. Purpose and functionality
        2. Method signatures and parameters
        3. Return types and values
        4. Common usage patterns
        5. Important notes or gotchas
        {"6. Code examples" if include_examples else ""}

        Format as JSON:
        {{
            "library": "{library}",
            "component": "{component}",
            "description": "clear description",
            "signature": "method signature if applicable",
            "parameters": [
                {{"name": "param", "type": "type", "description": "desc", "required": true}}
            ],
            "returns": {{"type": "return_type", "description": "what it returns"}},
            "examples": ["example1", "example2"],
            "notes": ["important note 1", "note 2"],
            "related": ["related_method1", "related_method2"]
        }}
        """

        try:
            self._log_prompt("get_api_reference", prompt)
            
            response = self.ai_client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=2000
            )
            
            self._log_prompt("get_api_reference", prompt, response)
            
            # Parse and cache the result
            result = self._parse_api_reference_response(response, library, component)
            self.cache[cache_key] = result
            
            self.logger.info(f"Retrieved API reference for {library}.{component}")
            return result

        except Exception as e:
            self.logger.error(f"API reference retrieval failed: {e}")
            return await self._fallback_api_reference(library, component)

    async def _find_code_examples(self,
                                use_case: str,
                                complexity: str = "intermediate",
                                source_preference: List[str] = ["official_examples", "github"]) -> List[Dict[str, Any]]:
        """Find real-world code examples for specific use cases."""
        
        if not self.ai_client:
            return await self._fallback_code_examples(use_case, complexity)

        prompt = f"""
        You are a code example curator. Find and provide high-quality code examples.

        USE CASE: {use_case}
        COMPLEXITY: {complexity}
        PREFERRED SOURCES: {', '.join(source_preference)}

        Provide realistic, working code examples that demonstrate:
        1. The specific use case clearly
        2. Best practices for the technology
        3. Proper error handling
        4. Clear variable names and structure

        Format as JSON array:
        [
            {{
                "title": "descriptive title",
                "description": "what this example demonstrates",
                "code": "complete working code example",
                "explanation": "step-by-step explanation",
                "complexity": "basic|intermediate|advanced",
                "technologies": ["tech1", "tech2"],
                "source_type": "official|community|synthetic"
            }}
        ]
        """

        try:
            self._log_prompt("find_code_examples", prompt)
            
            response = self.ai_client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,  # Slightly higher for variety
                max_tokens=3000
            )
            
            self._log_prompt("find_code_examples", prompt, response)
            
            examples = self._parse_code_examples_response(response)
            
            self.logger.info(f"Found {len(examples)} code examples for: {use_case}")
            return examples

        except Exception as e:
            self.logger.error(f"Code example search failed: {e}")
            return await self._fallback_code_examples(use_case, complexity)

    async def _check_best_practices(self,
                                  technology: str,
                                  focus_area: str = "general") -> Dict[str, Any]:
        """Get best practices and common patterns."""
        
        if not self.ai_client:
            return await self._fallback_best_practices(technology, focus_area)

        prompt = f"""
        You are a best practices expert for {technology}. Provide comprehensive guidance.

        TECHNOLOGY: {technology}
        FOCUS AREA: {focus_area}

        Provide authoritative best practices covering:
        1. Core principles and patterns
        2. Common mistakes to avoid
        3. Performance considerations
        4. Security implications
        5. Testing approaches
        6. Code organization

        Format as JSON:
        {{
            "technology": "{technology}",
            "focus_area": "{focus_area}",
            "core_principles": ["principle1", "principle2"],
            "best_practices": [
                {{"practice": "practice description", "reason": "why important", "example": "code example"}}
            ],
            "common_mistakes": [
                {{"mistake": "what to avoid", "consequence": "why bad", "solution": "how to fix"}}
            ],
            "performance_tips": ["tip1", "tip2"],
            "security_considerations": ["consideration1", "consideration2"],
            "testing_guidance": ["approach1", "approach2"]
        }}
        """

        try:
            self._log_prompt("check_best_practices", prompt)
            
            response = self.ai_client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=2500
            )
            
            self._log_prompt("check_best_practices", prompt, response)
            
            practices = self._parse_best_practices_response(response)
            
            self.logger.info(f"Retrieved best practices for {technology}")
            return practices

        except Exception as e:
            self.logger.error(f"Best practices retrieval failed: {e}")
            return await self._fallback_best_practices(technology, focus_area)

    async def _discover_related_libraries(self,
                                        base_technology: str,
                                        use_case: str = "",
                                        category: str = "general") -> List[Dict[str, Any]]:
        """Discover libraries and tools related to a technology."""
        
        if not self.ai_client:
            return await self._fallback_related_libraries(base_technology, category)

        prompt = f"""
        You are a technology ecosystem expert. Suggest related libraries and tools.

        BASE TECHNOLOGY: {base_technology}
        USE CASE: {use_case}
        CATEGORY: {category}

        Suggest relevant libraries/tools that:
        1. Complement the base technology
        2. Are actively maintained and popular
        3. Solve common problems in this ecosystem
        4. Are appropriate for the use case

        Format as JSON array:
        [
            {{
                "name": "library_name",
                "purpose": "what it does",
                "why_useful": "why it complements base technology",
                "popularity": "high|medium|low",
                "maintenance": "active|stable|experimental",
                "use_cases": ["case1", "case2"],
                "installation": "how to install",
                "quick_example": "simple usage example"
            }}
        ]
        """

        try:
            self._log_prompt("discover_related_libraries", prompt)
            
            response = self.ai_client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=2000
            )
            
            self._log_prompt("discover_related_libraries", prompt, response)
            
            libraries = self._parse_related_libraries_response(response)
            
            self.logger.info(f"Discovered {len(libraries)} related libraries for {base_technology}")
            return libraries

        except Exception as e:
            self.logger.error(f"Related libraries discovery failed: {e}")
            return await self._fallback_related_libraries(base_technology, category)

    # Helper methods for formatting and parsing
    def _format_doc_sources_for_prompt(self) -> str:
        """Format documentation sources for AI prompt."""
        formatted = []
        for source in self.doc_sources:
            formatted.append(f"- {source.name}: {source.base_url} (Priority: {source.priority}, Type: {source.doc_type})")
        return "\n".join(formatted)

    def _parse_search_response(self, response: str) -> Dict[str, Any]:
        """Parse AI search strategy response."""
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
                "primary_sources": [],
                "search_terms": [response[:50]],
                "concepts": [],
                "alternatives": []
            }

    def _parse_api_reference_response(self, response: str, library: str, component: str) -> Dict[str, Any]:
        """Parse API reference response."""
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
                "library": library,
                "component": component,
                "description": response[:500] + "...",
                "examples": [],
                "notes": ["AI response parsing failed"],
                "error": "Could not parse structured response"
            }

    def _parse_code_examples_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse code examples response."""
        try:
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                json_text = response[start:end].strip()
            else:
                json_text = response.strip()
            
            parsed = json.loads(json_text)
            return parsed if isinstance(parsed, list) else [parsed]
        except json.JSONDecodeError:
            return [{
                "title": "AI Response",
                "description": "Could not parse structured examples",
                "code": response[:1000],
                "explanation": "Raw AI response due to parsing error",
                "complexity": "unknown",
                "technologies": [],
                "source_type": "synthetic"
            }]

    def _parse_best_practices_response(self, response: str) -> Dict[str, Any]:
        """Parse best practices response."""
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
                "technology": "unknown",
                "focus_area": "general",
                "core_principles": [response[:200] + "..."],
                "best_practices": [],
                "common_mistakes": [],
                "error": "Could not parse structured response"
            }

    def _parse_related_libraries_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse related libraries response."""
        try:
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                json_text = response[start:end].strip()
            else:
                json_text = response.strip()
            
            parsed = json.loads(json_text)
            return parsed if isinstance(parsed, list) else [parsed]
        except json.JSONDecodeError:
            return [{
                "name": "unknown",
                "purpose": response[:200] + "...",
                "why_useful": "Could not parse response",
                "popularity": "unknown",
                "maintenance": "unknown",
                "error": "Parsing failed"
            }]

    async def _execute_documentation_search(self, strategy: Dict[str, Any], query: str) -> List[Dict[str, Any]]:
        """Execute the documentation search strategy."""
        # This would integrate with actual documentation APIs or web scraping
        # For now, return synthetic results based on the strategy
        
        results = []
        for source in strategy.get("primary_sources", []):
            results.append({
                "source": source.get("source", "unknown"),
                "url": source.get("url_pattern", ""),
                "relevance": source.get("relevance", ""),
                "content_summary": f"Documentation content for {query} from {source.get('source', 'unknown')}",
                "sections": source.get("sections", [])
            })
        
        return results

    def _summarize_documentation_results(self, results: List[Dict[str, Any]]) -> str:
        """Summarize documentation search results."""
        if not results:
            return "No documentation found"
        
        summary = f"Found {len(results)} relevant documentation sources:\n"
        for result in results:
            summary += f"- {result['source']}: {result['relevance']}\n"
        
        return summary

    # Fallback methods when AI is unavailable
    async def _fallback_find_documentation(self, query: str, doc_types: List[str]) -> Dict[str, Any]:
        """Fallback documentation search."""
        # Simple keyword matching against known sources
        relevant_sources = []
        query_lower = query.lower()
        
        for source in self.doc_sources:
            if any(keyword in source.name.lower() for keyword in query_lower.split()):
                relevant_sources.append({
                    "source": source.name,
                    "url": source.base_url,
                    "type": source.doc_type,
                    "priority": source.priority
                })
        
        return {
            "query": query,
            "results": relevant_sources,
            "method": "fallback_keyword_match"
        }

    async def _fallback_api_reference(self, library: str, component: str) -> Dict[str, Any]:
        """Fallback API reference."""
        return {
            "library": library,
            "component": component,
            "description": f"Basic reference for {library}.{component}",
            "note": "Limited information available without AI assistance",
            "suggested_sources": [f"https://docs.{library.lower()}.org" if library else ""]
        }

    async def _fallback_code_examples(self, use_case: str, complexity: str) -> List[Dict[str, Any]]:
        """Fallback code examples."""
        return [{
            "title": f"{use_case} Example",
            "description": f"Basic example for {use_case}",
            "code": f"# {use_case} example\n# TODO: Implement {use_case}",
            "complexity": complexity,
            "source_type": "fallback"
        }]

    async def _fallback_best_practices(self, technology: str, focus_area: str) -> Dict[str, Any]:
        """Fallback best practices."""
        return {
            "technology": technology,
            "focus_area": focus_area,
            "core_principles": [f"Follow {technology} documentation", "Use established patterns"],
            "note": "Limited guidance available without AI assistance"
        }

    async def _fallback_related_libraries(self, base_technology: str, category: str) -> List[Dict[str, Any]]:
        """Fallback related libraries."""
        # Basic suggestions based on common patterns
        common_suggestions = {
            "fastapi": ["pydantic", "uvicorn", "pytest", "sqlalchemy"],
            "pytest": ["pytest-cov", "pytest-mock", "pytest-asyncio"],
            "django": ["django-rest-framework", "celery", "redis"],
        }
        
        suggestions = common_suggestions.get(base_technology.lower(), [])
        
        return [
            {
                "name": lib,
                "purpose": f"Common companion to {base_technology}",
                "maintenance": "unknown",
                "source": "fallback_suggestions"
            }
            for lib in suggestions
        ]

    # Resource handlers
    async def _read_resource(self, uri: str) -> str:
        """Read documentation resources."""
        if uri == "docs://sources/registry":
            sources_data = {
                "sources": [
                    {
                        "name": source.name,
                        "base_url": source.base_url,
                        "doc_type": source.doc_type,
                        "priority": source.priority
                    }
                    for source in self.doc_sources
                ],
                "total_sources": len(self.doc_sources),
                "categories": list(set(source.doc_type for source in self.doc_sources))
            }
            return json.dumps(sources_data, indent=2)

        elif uri == "docs://patterns/common-apis":
            return """# Common API Patterns

## REST API Patterns
- Resource-based URLs
- HTTP methods for operations
- Status codes for responses

## Authentication Patterns
- JWT tokens
- API keys
- OAuth2 flows

## Error Handling Patterns
- Consistent error response format
- Appropriate HTTP status codes
- Detailed error messages for development

## Testing Patterns
- Unit tests for business logic
- Integration tests for API endpoints
- Mock external dependencies
"""

        return f"Resource not found: {uri}"

    async def _get_prompt(self, name: str, arguments: Dict[str, Any]) -> str:
        """Generate documentation-related prompts."""
        # This could be extended to provide prompt templates for documentation tasks
        return f"Documentation prompt for {name} not implemented"