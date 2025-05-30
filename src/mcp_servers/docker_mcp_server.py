"""
Docker MCP Server for AI-driven container generation.

This server provides tools for generating, optimizing, and managing
Docker configurations using AI instead of hardcoded templates.
"""

import json
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional
from .base_mcp_server import BaseMCPServer


class DockerMCPServer(BaseMCPServer):
    """
    MCP Server for AI-driven Docker configuration generation.
    
    This replaces the hardcoded template-based Docker generation
    with intelligent, adaptive container configuration.
    """

    def __init__(self, show_prompts: bool = False):
        super().__init__("docker-server", "1.0.0", show_prompts=show_prompts)
        
    def _register_capabilities(self):
        """Register Docker-related tools, resources, and prompts."""
        
        # Tools for Docker generation
        self.register_tool(
            name="generate_dockerfile",
            description="Generate an optimized Dockerfile based on code analysis and constraints",
            input_schema={
                "type": "object",
                "properties": {
                    "code_analysis": {
                        "type": "object",
                        "description": "Analysis of the codebase including dependencies, frameworks, and patterns"
                    },
                    "constraints": {
                        "type": "object", 
                        "description": "Performance, security, and deployment constraints"
                    },
                    "environment": {
                        "type": "string",
                        "description": "Target deployment environment (development, staging, production)",
                        "enum": ["development", "staging", "production"]
                    },
                    "optimization_goals": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optimization priorities: security, performance, size, build_speed"
                    }
                },
                "required": ["code_analysis"]
            },
            handler=self._generate_dockerfile
        )

        self.register_tool(
            name="generate_docker_compose",
            description="Generate docker-compose.yml for multi-service deployment",
            input_schema={
                "type": "object",
                "properties": {
                    "services": {
                        "type": "array",
                        "items": {"type": "object"},
                        "description": "List of services to include in the composition"
                    },
                    "networking": {
                        "type": "object",
                        "description": "Network configuration requirements"
                    },
                    "volumes": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Required persistent volumes"
                    },
                    "environment": {
                        "type": "string",
                        "enum": ["development", "staging", "production"]
                    }
                },
                "required": ["services"]
            },
            handler=self._generate_docker_compose
        )

        self.register_tool(
            name="optimize_container",
            description="Optimize existing Dockerfile for specific goals",
            input_schema={
                "type": "object",
                "properties": {
                    "dockerfile": {
                        "type": "string",
                        "description": "Current Dockerfile content"
                    },
                    "optimization_target": {
                        "type": "string",
                        "enum": ["size", "security", "build_speed", "runtime_performance"],
                        "description": "Primary optimization goal"
                    },
                    "constraints": {
                        "type": "object",
                        "description": "Any constraints to maintain during optimization"
                    }
                },
                "required": ["dockerfile", "optimization_target"]
            },
            handler=self._optimize_container
        )

        self.register_tool(
            name="analyze_dependencies",
            description="Analyze code to detect dependencies and runtime requirements",
            input_schema={
                "type": "object",
                "properties": {
                    "implementation_code": {
                        "type": "string",
                        "description": "Implementation source code"
                    },
                    "test_code": {
                        "type": "string", 
                        "description": "Test source code"
                    },
                    "language": {
                        "type": "string",
                        "description": "Programming language (auto-detected if not specified)"
                    }
                },
                "required": ["implementation_code"]
            },
            handler=self._analyze_dependencies
        )

        # Resources for Docker templates and examples
        self.register_resource(
            uri="docker://templates/multi-stage",
            name="Multi-stage Dockerfile Template", 
            description="Template for multi-stage Docker builds",
            mime_type="text/x-dockerfile"
        )

        self.register_resource(
            uri="docker://examples/best-practices",
            name="Docker Best Practices",
            description="Curated Docker best practices and security guidelines",
            mime_type="text/markdown"
        )

        # Prompts for Docker generation
        self.register_prompt(
            name="dockerfile_generation",
            description="Generate optimized Dockerfile with AI",
            arguments=[
                {"name": "language", "description": "Programming language", "required": True},
                {"name": "framework", "description": "Framework used", "required": False},
                {"name": "dependencies", "description": "Dependencies list", "required": True},
                {"name": "constraints", "description": "Performance/security constraints", "required": False}
            ]
        )

    async def _generate_dockerfile(self, 
                                 code_analysis: Dict[str, Any],
                                 constraints: Optional[Dict[str, Any]] = None,
                                 environment: str = "production",
                                 optimization_goals: Optional[List[str]] = None) -> str:
        """Generate an optimized Dockerfile using AI."""
        
        if not self.ai_client:
            return self._fallback_dockerfile_generation(code_analysis, environment)

        # Build comprehensive prompt for AI
        prompt = self._build_dockerfile_prompt(code_analysis, constraints, environment, optimization_goals)
        
        try:
            content = self.ai_client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,  # Low temperature for consistent, reliable output
                max_tokens=2000
            )
            
            # Post-process the response to ensure it's a valid Dockerfile
            dockerfile = self._post_process_dockerfile(content)
            
            self.logger.info(f"Generated Dockerfile for {code_analysis.get('language', 'unknown')} project")
            return dockerfile
            
        except Exception as e:
            self.logger.error(f"AI Dockerfile generation failed: {e}")
            return self._fallback_dockerfile_generation(code_analysis, environment)

    async def _generate_docker_compose(self,
                                     services: List[Dict[str, Any]],
                                     networking: Optional[Dict[str, Any]] = None,
                                     volumes: Optional[List[str]] = None,
                                     environment: str = "development") -> str:
        """Generate docker-compose.yml using AI."""
        
        if not self.ai_client:
            return self._fallback_compose_generation(services, environment)

        prompt = self._build_compose_prompt(services, networking, volumes, environment)
        
        try:
            content = self.ai_client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=1500
            )
            
            compose_yaml = self._post_process_compose(content)
            
            self.logger.info(f"Generated docker-compose.yml for {len(services)} services")
            return compose_yaml
            
        except Exception as e:
            self.logger.error(f"AI Compose generation failed: {e}")
            return self._fallback_compose_generation(services, environment)

    async def _optimize_container(self,
                                dockerfile: str,
                                optimization_target: str,
                                constraints: Optional[Dict[str, Any]] = None) -> str:
        """Optimize existing Dockerfile for specific goals."""
        
        if not self.ai_client:
            return dockerfile  # Return original if AI unavailable

        prompt = f"""
You are a Docker optimization expert. Optimize this Dockerfile for {optimization_target}.

Current Dockerfile:
```dockerfile
{dockerfile}
```

Optimization target: {optimization_target}
Constraints: {json.dumps(constraints or {}, indent=2)}

Generate an optimized Dockerfile that:
1. Maintains all functionality
2. Optimizes specifically for {optimization_target}
3. Follows Docker best practices
4. Respects any provided constraints

Return only the optimized Dockerfile content.
"""

        try:
            content = self.ai_client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=2000
            )
            
            optimized = self._post_process_dockerfile(content)
            
            self.logger.info(f"Optimized Dockerfile for {optimization_target}")
            return optimized
            
        except Exception as e:
            self.logger.error(f"Dockerfile optimization failed: {e}")
            return dockerfile

    async def _analyze_dependencies(self,
                                  implementation_code: str,
                                  test_code: Optional[str] = None,
                                  language: Optional[str] = None) -> Dict[str, Any]:
        """Analyze code to detect dependencies and runtime requirements."""
        
        # Use the enhanced dependency detection from handoff_flow
        try:
            from orchestrator.handoff_flow import _analyze_code_for_docker
            
            analysis = _analyze_code_for_docker(
                implementation_code, 
                test_code or "", 
                {}
            )
            
            self.logger.info(f"Analyzed dependencies: {len(analysis['dependencies'])} found")
            return analysis
            
        except Exception as e:
            self.logger.error(f"Dependency analysis failed: {e}")
            return {
                "dependencies": [],
                "has_web_server": False,
                "has_database": False,
                "has_async": False,
                "python_version": "3.11"
            }

    def _build_dockerfile_prompt(self, 
                               code_analysis: Dict[str, Any],
                               constraints: Optional[Dict[str, Any]],
                               environment: str,
                               optimization_goals: Optional[List[str]]) -> str:
        """Build comprehensive prompt for Dockerfile generation."""
        
        optimization_goals = optimization_goals or ["security", "performance"]
        constraints = constraints or {}
        
        return f"""
You are a Docker expert specializing in optimized container generation. Generate a production-ready Dockerfile for this project.

## Code Analysis
Language: {code_analysis.get('language', 'Python')}
Dependencies: {list(code_analysis.get('dependencies', []))}
Has Web Server: {code_analysis.get('has_web_server', False)}
Has Database: {code_analysis.get('has_database', False)}
Has Async: {code_analysis.get('has_async', False)}
Ports: {code_analysis.get('ports', [])}

## Environment & Requirements
Target Environment: {environment}
Optimization Goals: {', '.join(optimization_goals)}
Constraints: {json.dumps(constraints, indent=2)}

## Requirements
Generate a Dockerfile that:
1. Uses appropriate base image for the detected language/framework
2. Implements multi-stage builds if beneficial for size optimization
3. Follows security best practices (non-root user, minimal attack surface)
4. Optimizes for the specified goals: {', '.join(optimization_goals)}
5. Includes proper health checks if web server detected
6. Handles dependencies efficiently with layer caching
7. Sets appropriate environment variables and working directory

## Output Format
Return ONLY the Dockerfile content, no explanations or markdown formatting.
Start with FROM instruction and include all necessary commands.
"""

    def _build_compose_prompt(self,
                            services: List[Dict[str, Any]],
                            networking: Optional[Dict[str, Any]],
                            volumes: Optional[List[str]],
                            environment: str) -> str:
        """Build prompt for docker-compose generation."""
        
        return f"""
You are a Docker Compose expert. Generate a docker-compose.yml file for this multi-service application.

## Services
{json.dumps(services, indent=2)}

## Networking Requirements  
{json.dumps(networking or {}, indent=2)}

## Volume Requirements
{volumes or []}

## Environment
Target: {environment}

## Requirements
Generate a docker-compose.yml that:
1. Defines all required services with proper configuration
2. Sets up appropriate networking between services
3. Configures required volumes for data persistence
4. Includes health checks and restart policies
5. Uses environment-appropriate settings for {environment}
6. Follows Docker Compose best practices

Return ONLY the docker-compose.yml content in valid YAML format.
"""

    def _post_process_dockerfile(self, response: str) -> str:
        """Clean and validate AI-generated Dockerfile."""
        
        # Extract Dockerfile content from response
        lines = response.strip().split('\n')
        dockerfile_lines = []
        
        in_dockerfile = False
        for line in lines:
            # Skip markdown formatting
            if line.strip().startswith('```'):
                in_dockerfile = not in_dockerfile
                continue
                
            if line.strip().startswith('FROM ') or in_dockerfile or not dockerfile_lines:
                dockerfile_lines.append(line)
        
        # Ensure it starts with FROM
        if dockerfile_lines and not dockerfile_lines[0].strip().startswith('FROM '):
            dockerfile_lines.insert(0, "FROM python:3.11-slim")
        
        return '\n'.join(dockerfile_lines)

    def _post_process_compose(self, response: str) -> str:
        """Clean and validate AI-generated docker-compose.yml."""
        
        # Extract YAML content from response
        lines = response.strip().split('\n')
        yaml_lines = []
        
        in_yaml = False
        for line in lines:
            if line.strip().startswith('```'):
                in_yaml = not in_yaml
                continue
                
            if line.strip().startswith('version:') or in_yaml or 'services:' in line:
                yaml_lines.append(line)
        
        return '\n'.join(yaml_lines)

    def _fallback_dockerfile_generation(self, code_analysis: Dict[str, Any], environment: str) -> str:
        """Fallback Dockerfile generation when AI is unavailable."""
        
        python_version = code_analysis.get('python_version', '3.11')
        dependencies = code_analysis.get('dependencies', [])
        has_web_server = code_analysis.get('has_web_server', False)
        
        dockerfile = f"""# Auto-generated Dockerfile (fallback mode)
FROM python:{python_version}-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app
USER appuser
"""

        if has_web_server:
            ports = code_analysis.get('ports', [8000])
            port = ports[0] if ports else 8000
            dockerfile += f"""
# Expose port
EXPOSE {port}

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:{port}/health || exit 1
"""

        return dockerfile

    def _fallback_compose_generation(self, services: List[Dict[str, Any]], environment: str) -> str:
        """Fallback docker-compose generation when AI is unavailable."""
        
        compose = f"""# Auto-generated docker-compose.yml (fallback mode)
version: '3.8'

services:
"""
        
        for service in services:
            name = service.get('name', 'app')
            compose += f"""  {name}:
    build: .
    ports:
      - "8000:8000"
    environment:
      - NODE_ENV={environment}
    restart: unless-stopped
    
"""
        
        return compose

    async def _read_resource(self, uri: str) -> str:
        """Read Docker-related resources."""
        
        if uri == "docker://templates/multi-stage":
            return """# Multi-stage Dockerfile template
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

FROM node:18-alpine AS runtime
WORKDIR /app
COPY --from=builder /app/node_modules ./node_modules
COPY . .
EXPOSE 3000
CMD ["npm", "start"]
"""
        
        elif uri == "docker://examples/best-practices":
            return """# Docker Best Practices

## Security
- Use non-root user
- Minimize attack surface
- Keep base images updated
- Use specific image tags

## Performance  
- Multi-stage builds for smaller images
- Layer caching optimization
- .dockerignore for faster builds

## Reliability
- Health checks
- Proper signal handling
- Resource limits
"""
        
        return f"Resource not found: {uri}"

    async def _get_prompt(self, name: str, arguments: Dict[str, Any]) -> str:
        """Generate Docker-related prompts."""
        
        if name == "dockerfile_generation":
            language = arguments.get("language", "python")
            framework = arguments.get("framework", "")
            dependencies = arguments.get("dependencies", [])
            constraints = arguments.get("constraints", {})
            
            return self._build_dockerfile_prompt(
                {
                    "language": language,
                    "dependencies": dependencies,
                    "has_web_server": "fastapi" in str(dependencies).lower()
                },
                constraints,
                "production",
                ["security", "performance"]
            )
        
        return f"Prompt not found: {name}"