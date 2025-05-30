"""
Spec-to-implementation handoff flow for SDD orchestrator.
"""

import yaml
import hashlib
import json
import time
from pathlib import Path
from core.ai_client import chat_completion

# In-memory cache for generated code
_generation_cache = {}
_cache_max_age = 3600  # 1 hour in seconds

def handoff_flow(spec_path: Path, output_dir: Path, max_retries: int = 3):
    """
    Entry point for spec-to-implementation pipeline with enhanced error handling.

    Args:
        spec_path: Path to the specification YAML file.
        output_dir: Directory where generated code will be placed.
        max_retries: Maximum number of retries for failed operations.
    """
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        # Load and parse the specification with validation
        with open(spec_path, 'r') as f:
            spec = yaml.safe_load(f)
        
        # Validate specification structure
        _validate_specification(spec)
        
        # Generate appropriate file names based on feature
        filenames = _generate_filenames(spec)
        
        # Create output directory if it doesn't exist
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate implementation with retry logic
        implementation_code = _generate_with_retry(
            lambda: generate_implementation(spec),
            "implementation",
            max_retries
        )
        
        # Generate tests with retry logic
        test_code = _generate_with_retry(
            lambda: generate_tests(spec),
            "tests", 
            max_retries
        )
        
        # Write generated files with error handling
        _write_files_safely(output_dir, implementation_code, test_code, filenames)
        
        # Generate Docker configuration
        docker_files = _generate_docker_configuration(
            implementation_code, test_code, spec, output_dir, filenames
        )
        
        logger.info(f"Successfully generated code and Docker configuration in {output_dir}")
        
    except Exception as e:
        logger.error(f"Handoff flow failed: {str(e)}")
        # Clean up partial files on failure
        _cleanup_on_failure(output_dir, filenames)
        raise

def _generate_filenames(spec: dict) -> dict:
    """Generate appropriate filenames based on the feature specification."""
    import re
    
    feature = spec.get('feature', {})
    if isinstance(feature, dict):
        feature_name = feature.get('name', 'service')
    else:
        feature_name = str(feature) if feature else 'service'
    
    # Convert feature name to snake_case for Python files
    snake_case_name = re.sub(r'[^a-zA-Z0-9]+', '_', feature_name).lower().strip('_')
    
    # Ensure it's a valid Python module name
    if not snake_case_name or snake_case_name[0].isdigit():
        snake_case_name = f"service_{snake_case_name}"
    
    return {
        'implementation': f"{snake_case_name}.py",
        'test': f"test_{snake_case_name}.py",
        'module_name': snake_case_name
    }

def generate_implementation(spec):
    """Generate Python implementation code from specification with caching."""
    
    # Create cache key from spec content
    cache_key = _create_cache_key(spec, "implementation")
    
    # Check cache first
    cached_result = _get_from_cache(cache_key)
    if cached_result:
        return cached_result
    
    feature = spec.get('feature', {})
    if isinstance(feature, dict):
        feature_description = feature.get('name', 'Unknown Feature')
        feature_desc_full = feature.get('description', '')
    else:
        feature_description = str(feature)
        feature_desc_full = ''
    
    scenarios = spec.get('scenarios', [])
    constraints = spec.get('constraints', {})
    
    # Generate comprehensive prompt with optimizations
    prompt_messages = build_implementation_prompt(
        feature_description, feature_desc_full, scenarios, constraints
    )
    
    # Use optimized parameters for better performance
    code = chat_completion(
        prompt_messages, 
        max_tokens=3000,
        temperature=0.1  # Lower temperature for more consistent results
    )
    
    result = clean_code_response(code)
    
    # Cache the result
    _store_in_cache(cache_key, result)
    
    return result

def generate_tests(spec):
    """Generate test code based on scenarios with caching."""
    
    # Create cache key from spec content
    cache_key = _create_cache_key(spec, "tests")
    
    # Check cache first
    cached_result = _get_from_cache(cache_key)
    if cached_result:
        return cached_result
    
    feature = spec.get('feature', {})
    if isinstance(feature, dict):
        feature_name = feature.get('name', 'Unknown Feature')
    else:
        feature_name = str(feature)
    
    scenarios = spec.get('scenarios', [])
    
    prompt_messages = build_test_prompt(feature_name, scenarios)
    
    # Use optimized parameters for better performance
    code = chat_completion(
        prompt_messages, 
        max_tokens=2500,
        temperature=0.1  # Lower temperature for more consistent results
    )
    
    result = clean_code_response(code)
    
    # Cache the result
    _store_in_cache(cache_key, result)
    
    return result

def build_test_prompt(feature_name, scenarios):
    """Build comprehensive test generation prompt."""
    
    system_prompt = """You are an expert test developer specializing in behavior-driven testing for SDD systems.

Testing Principles:
1. Each scenario maps to exactly one test function
2. All 'then' conditions must be verified with assertions
3. Tests should be independent and repeatable
4. Use descriptive test names that explain the behavior being tested
5. Include proper setup and teardown
6. Test both happy paths and error conditions

Generate comprehensive pytest test code that validates all specified behaviors."""

    user_prompt = f"""
FEATURE UNDER TEST: {feature_name}

SCENARIOS TO TEST:
{format_scenarios_for_test_prompt(scenarios)}

TEST REQUIREMENTS:
1. Import all necessary classes from the generated module
2. Create one test function per scenario with descriptive names
3. Use pytest fixtures for common setup (TaskManager instances, etc.)
4. Test ALL 'then' conditions with specific assertions
5. For error scenarios, use pytest.raises() appropriately
6. Include assertions for data types, values, and object state
7. Add comments explaining complex test logic

TEST STRUCTURE:
- Import statements at the top
- Fixtures for common test objects
- One test function per scenario
- Clear assertion messages for failures

RESPONSE FORMAT: Provide ONLY valid Python pytest code. No explanations, markdown, or additional text.
"""

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

def format_scenarios_for_test_prompt(scenarios):
    """Format scenarios specifically for test generation."""
    formatted = []
    for i, scenario in enumerate(scenarios, 1):
        name = scenario.get('name', f'Scenario {i}')
        formatted.append(f"\nScenario {i}: {name}")
        formatted.append(f"Test Function Name: test_{name.lower().replace(' ', '_')}")
        
        if scenario.get('given'):
            formatted.append(f"  Setup: {scenario['given']}")
        if scenario.get('when'):
            formatted.append(f"  Action: {scenario['when']}")
        if scenario.get('then'):
            formatted.append(f"  Assertions Required:")
            for j, condition in enumerate(scenario['then'], 1):
                formatted.append(f"    {j}. Verify: {condition}")
        formatted.append("")  # blank line between scenarios
    
    return '\n'.join(formatted)

def clean_code_response(response):
    """Remove markdown code blocks and other formatting from AI response."""
    lines = response.strip().split('\n')
    
    # Filter out all lines that are markdown code block markers
    cleaned_lines = []
    code_started = False
    
    for line in lines:
        # Skip lines that are just markdown code block markers
        if line.strip().startswith('```'):
            continue
            
        # Look for Python imports or class definitions to detect start of actual code
        if not code_started and (line.strip().startswith(('import ', 'from ', 'class ', 'def ', '@dataclass'))):
            code_started = True
            
        # Once we hit code that looks like explanatory text after actual Python code, stop
        if code_started and line.strip() and not line.startswith((' ', '\t')) and not any(
            line.strip().startswith(prefix) for prefix in [
                'import ', 'from ', 'class ', 'def ', '@', '#', 'if ', 'else:', 'elif ', 
                'try:', 'except', 'finally:', 'with ', 'for ', 'while ', 'return', 'yield',
                'raise', 'assert', 'pass', 'break', 'continue'
            ]
        ) and not line.strip().endswith(':') and '=' not in line:
            # This looks like explanatory text, stop here
            break
            
        if code_started:
            cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines)

def build_implementation_prompt(feature_name, feature_description, scenarios, constraints):
    """Build comprehensive implementation prompt following SDD principles."""
    
    # Analyze scenarios to extract requirements
    scenario_analysis = analyze_scenarios(scenarios)
    constraint_requirements = extract_constraint_requirements(constraints)
    
    system_prompt = """You are an expert Python developer specializing in Specification-Driven Development (SDD).

Key SDD Principles:
1. Behavior-First: Implementation must satisfy all specified behaviors
2. Constraint-Driven: Non-functional requirements are enforced in code
3. Self-Validating: Code includes validation for all business rules
4. Observable: All behaviors should be easily testable and monitorable

Generate clean, production-ready Python code that strictly adheres to the specification."""

    user_prompt = f"""
FEATURE: {feature_name}
DESCRIPTION: {feature_description}

BEHAVIORAL REQUIREMENTS (must be satisfied):
{format_scenarios_for_prompt(scenarios)}

{format_constraints_for_prompt(constraints)}

CODE STRUCTURE REQUIREMENTS:
{scenario_analysis['code_structure']}

IMPLEMENTATION GUIDELINES:
1. Use dataclasses with proper field ordering (required fields first, optional fields with defaults last)
2. Create custom exception classes for business rule violations
3. Include comprehensive type hints throughout
4. Add input validation for all public methods
5. Implement proper error handling with descriptive messages
6. Use clear, descriptive method and variable names
7. Add docstrings for all public methods

CRITICAL: The implementation must pass all scenarios when tested. Each 'then' condition must be verifiable through the API.

RESPONSE FORMAT: Provide ONLY valid Python code. No explanations, markdown, or additional text.
"""

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

def analyze_scenarios(scenarios):
    """Analyze scenarios to determine required code structure."""
    entities = set()
    operations = set()
    validations = set()
    
    for scenario in scenarios:
        # Extract entities mentioned in scenarios
        scenario_text = str(scenario)
        if 'task' in scenario_text.lower():
            entities.add('Task')
        if 'user' in scenario_text.lower():
            entities.add('User')
            
        # Extract operations
        if scenario.get('when'):
            when_text = scenario['when'].lower()
            if 'create' in when_text:
                operations.add('create')
            if 'mark' in when_text or 'complete' in when_text:
                operations.add('complete')
            if 'list' in when_text:
                operations.add('list')
                
        # Extract validations from 'then' conditions
        if scenario.get('then'):
            for condition in scenario['then']:
                if 'error' in condition.lower():
                    validations.add('error_handling')
                if 'should have' in condition.lower():
                    validations.add('property_validation')
    
    code_structure = f"""
Required Entities: {', '.join(entities)}
Required Operations: {', '.join(operations)}
Required Validations: {', '.join(validations)}

Suggested Class Structure:
- Data models using @dataclass
- Manager class with methods for each operation
- Custom exception classes for validation errors
"""
    
    return {
        'entities': entities,
        'operations': operations,
        'validations': validations,
        'code_structure': code_structure
    }

def format_scenarios_for_prompt(scenarios):
    """Format scenarios in a clear, structured way for the prompt."""
    formatted = []
    for i, scenario in enumerate(scenarios, 1):
        name = scenario.get('name', f'Scenario {i}')
        formatted.append(f"\nScenario {i}: {name}")
        
        if scenario.get('given'):
            formatted.append(f"  Given: {scenario['given']}")
        if scenario.get('when'):
            formatted.append(f"  When: {scenario['when']}")
        if scenario.get('then'):
            formatted.append(f"  Then:")
            for condition in scenario['then']:
                formatted.append(f"    - {condition}")
    
    return '\n'.join(formatted)

def extract_constraint_requirements(constraints):
    """Extract implementable requirements from constraints."""
    requirements = []
    
    for category, constraint_list in constraints.items():
        if isinstance(constraint_list, list):
            for constraint in constraint_list:
                if isinstance(constraint, dict) and constraint.get('requirement'):
                    requirements.append(f"{category}: {constraint['requirement']}")
    
    return requirements

def format_constraints_for_prompt(constraints):
    """Format constraints for the implementation prompt with enhanced integration."""
    if not constraints:
        return "NON-FUNCTIONAL REQUIREMENTS: None specified"
    
    formatted = ["NON-FUNCTIONAL REQUIREMENTS:"]
    requirements = extract_constraint_requirements(constraints)
    
    for req in requirements:
        formatted.append(f"- {req}")
    
    if not requirements:
        formatted.append("- None specified")
    
    # Enhanced constraint integration with specific implementation guidance
    constraint_implementations = generate_constraint_implementations(constraints)
    if constraint_implementations:
        formatted.append("\nCONSTRAINT IMPLEMENTATION REQUIREMENTS:")
        for impl in constraint_implementations:
            formatted.append(f"- {impl}")
        
    return '\n'.join(formatted)

def generate_constraint_implementations(constraints):
    """Generate specific implementation requirements from constraints."""
    implementations = []
    
    for category, constraint_list in constraints.items():
        if not isinstance(constraint_list, list):
            continue
            
        for constraint in constraint_list:
            if not isinstance(constraint, dict):
                continue
                
            requirement = constraint.get('requirement', '').lower()
            name = constraint.get('name', '').lower()
            
            # Performance constraints
            if category.lower() == 'performance':
                if 'response time' in requirement or 'latency' in requirement:
                    implementations.extend([
                        "Add timing decorators to all public methods",
                        "Include performance logging with method execution times",
                        "Add timeout handling for operations that might exceed limits",
                        "Consider adding async/await for I/O operations if applicable"
                    ])
                elif 'throughput' in requirement or 'requests per second' in requirement:
                    implementations.extend([
                        "Implement connection pooling for database operations",
                        "Add rate limiting mechanisms",
                        "Consider batch processing for bulk operations"
                    ])
                elif 'memory' in requirement:
                    implementations.extend([
                        "Use generators for large data sets",
                        "Implement proper resource cleanup (context managers)",
                        "Add memory usage monitoring"
                    ])
            
            # Security constraints
            elif category.lower() == 'security':
                if 'authentication' in requirement or 'auth' in requirement:
                    implementations.extend([
                        "Add user authentication validation to all protected methods",
                        "Implement JWT token verification decorator",
                        "Include user permission checks based on roles"
                    ])
                elif 'validation' in requirement or 'input' in requirement:
                    implementations.extend([
                        "Add comprehensive input validation using pydantic models",
                        "Implement sanitization for all user inputs",
                        "Add parameter type checking and bounds validation"
                    ])
                elif 'encryption' in requirement:
                    implementations.append("Add encryption for sensitive data fields")
                elif 'audit' in requirement or 'logging' in requirement:
                    implementations.extend([
                        "Implement audit logging for all state changes",
                        "Add user action tracking with timestamps",
                        "Include security event logging"
                    ])
            
            # Reliability constraints
            elif category.lower() == 'reliability':
                if 'availability' in requirement or 'uptime' in requirement:
                    implementations.extend([
                        "Add health check endpoints",
                        "Implement graceful error handling with retry logic",
                        "Add circuit breaker pattern for external dependencies"
                    ])
                elif 'backup' in requirement or 'recovery' in requirement:
                    implementations.extend([
                        "Implement data backup mechanisms",
                        "Add transaction rollback support",
                        "Include disaster recovery procedures"
                    ])
            
            # Scalability constraints
            elif category.lower() == 'scalability':
                if 'concurrent' in requirement or 'parallel' in requirement:
                    implementations.extend([
                        "Implement thread-safe operations using locks where needed",
                        "Add async processing capabilities",
                        "Consider using connection pooling"
                    ])
                elif 'load' in requirement:
                    implementations.extend([
                        "Implement caching mechanisms for frequently accessed data",
                        "Add horizontal scaling support through stateless design",
                        "Consider database indexing for query optimization"
                    ])
    
    return list(set(implementations))  # Remove duplicates

# Cache management functions
def _create_cache_key(spec: dict, generation_type: str) -> str:
    """Create a deterministic cache key from specification content."""
    # Create a normalized representation of the spec
    spec_str = json.dumps(spec, sort_keys=True, ensure_ascii=True)
    combined = f"{generation_type}:{spec_str}"
    return hashlib.sha256(combined.encode()).hexdigest()

def _get_from_cache(cache_key: str):
    """Retrieve cached result if valid and not expired."""
    if cache_key in _generation_cache:
        cached_item = _generation_cache[cache_key]
        if time.time() - cached_item['timestamp'] < _cache_max_age:
            return cached_item['result']
        else:
            # Remove expired cache entry
            del _generation_cache[cache_key]
    return None

def _store_in_cache(cache_key: str, result: str):
    """Store result in cache with timestamp."""
    _generation_cache[cache_key] = {
        'result': result,
        'timestamp': time.time()
    }

def clear_generation_cache():
    """Clear the generation cache (useful for testing or manual cache management)."""
    global _generation_cache
    _generation_cache = {}

def get_cache_stats():
    """Get cache statistics for monitoring."""
    current_time = time.time()
    total_entries = len(_generation_cache)
    expired_entries = sum(1 for item in _generation_cache.values() 
                         if current_time - item['timestamp'] >= _cache_max_age)
    active_entries = total_entries - expired_entries
    
    return {
        'total_entries': total_entries,
        'active_entries': active_entries,
        'expired_entries': expired_entries,
        'cache_hit_potential': active_entries > 0
    }

# Error handling and reliability functions
def _validate_specification(spec: dict):
    """Validate the specification structure."""
    if not isinstance(spec, dict):
        raise ValueError("Specification must be a dictionary")
    
    if 'feature' not in spec:
        raise ValueError("Specification missing required 'feature' field")
    
    scenarios = spec.get('scenarios', [])
    if not isinstance(scenarios, list) or len(scenarios) == 0:
        raise ValueError("Specification must have at least one scenario")
    
    # Validate scenario structure
    for i, scenario in enumerate(scenarios):
        if not isinstance(scenario, dict):
            raise ValueError(f"Scenario {i} must be a dictionary")
        
        required_fields = ['name', 'when', 'then']
        for field in required_fields:
            if field not in scenario:
                raise ValueError(f"Scenario {i} missing required field: {field}")
        
        # 'given' is optional for some scenarios

def _generate_with_retry(generate_func, operation_type: str, max_retries: int):
    """Execute generation function with retry logic."""
    import logging
    import time
    
    logger = logging.getLogger(__name__)
    
    for attempt in range(max_retries):
        try:
            result = generate_func()
            if result and len(result.strip()) > 50:  # Basic sanity check
                logger.info(f"Successfully generated {operation_type} on attempt {attempt + 1}")
                return result
            else:
                raise ValueError(f"Generated {operation_type} is too short or empty")
                
        except Exception as e:
            logger.warning(f"Generation attempt {attempt + 1} failed for {operation_type}: {str(e)}")
            if attempt == max_retries - 1:
                raise
            else:
                # Exponential backoff
                time.sleep(2 ** attempt)
    
    raise RuntimeError(f"Failed to generate {operation_type} after {max_retries} attempts")

def _write_files_safely(output_dir: Path, implementation_code: str, test_code: str, filenames: dict):
    """Write generated files with atomic operations and validation."""
    import tempfile
    import shutil
    
    # Write to temporary files first
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp_impl:
        tmp_impl.write(implementation_code)
        tmp_impl_path = tmp_impl.name
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp_test:
        tmp_test.write(test_code)
        tmp_test_path = tmp_test.name
    
    try:
        # Validate generated code syntax
        _validate_python_syntax(tmp_impl_path)
        _validate_python_syntax(tmp_test_path)
        
        # If validation passes, move to final location with proper names
        shutil.move(tmp_impl_path, output_dir / filenames['implementation'])
        shutil.move(tmp_test_path, output_dir / filenames['test'])
        
        # Create __init__.py
        (output_dir / "__init__.py").write_text("")
        
    except Exception as e:
        # Clean up temp files on error
        Path(tmp_impl_path).unlink(missing_ok=True)
        Path(tmp_test_path).unlink(missing_ok=True)
        raise

def _validate_python_syntax(file_path: str):
    """Validate that a Python file has correct syntax."""
    import ast
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    try:
        ast.parse(content)
    except SyntaxError as e:
        raise ValueError(f"Generated Python code has syntax errors: {str(e)}")

def _cleanup_on_failure(output_dir: Path, filenames: dict = None):
    """Clean up any partially created files on failure."""
    try:
        if output_dir.exists():
            cleanup_files = ["__init__.py", "Dockerfile", "docker-compose.yml", "requirements.txt", 
                           ".dockerignore", ".env.development", ".env.production", ".env.testing",
                           "docker-compose.override.yml", "docker-compose.prod.yml", "docker-compose.test.yml",
                           "DEPLOYMENT.md"]
            
            if filenames:
                cleanup_files.extend([filenames['implementation'], filenames['test']])
            else:
                # Fallback: cleanup any Python files (except __init__.py)
                for py_file in output_dir.glob("*.py"):
                    if py_file.name != "__init__.py":
                        cleanup_files.append(py_file.name)
                
            for file in cleanup_files:
                (output_dir / file).unlink(missing_ok=True)
    except Exception:
        pass  # Best effort cleanup

# Docker configuration generation functions
def _generate_docker_configuration(implementation_code: str, test_code: str, spec: dict, output_dir: Path, filenames: dict) -> dict:
    """Generate Docker configuration files based on code analysis and constraints."""
    
    # Analyze code for dependencies and runtime requirements
    analysis = _analyze_code_for_docker(implementation_code, test_code, spec)
    
    # Generate Dockerfile
    dockerfile_content = _generate_dockerfile(analysis, filenames)
    
    # Generate docker-compose.yml
    compose_content = _generate_docker_compose(analysis, spec, filenames)
    
    # Generate requirements.txt based on detected dependencies
    requirements_content = _generate_requirements_txt(analysis)
    
    # Generate .dockerignore
    dockerignore_content = _generate_dockerignore()
    
    # Generate environment files
    env_files = _generate_environment_files(analysis, spec)
    
    # Write Docker files
    docker_files = {
        'Dockerfile': dockerfile_content,
        'docker-compose.yml': compose_content,
        'requirements.txt': requirements_content,
        '.dockerignore': dockerignore_content,
        **env_files
    }
    
    for filename, content in docker_files.items():
        (output_dir / filename).write_text(content)
    
    return docker_files

def _extract_imports_from_code(code: str) -> set:
    """Extract all imported module names from Python code using AST."""
    import ast
    
    imported_modules = set()
    
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    # Get the top-level module name (e.g., fastapi_limiter from fastapi_limiter.depends)
                    module_name = alias.name.split('.')[0]
                    imported_modules.add(module_name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    # Get the top-level module name
                    module_name = node.module.split('.')[0]
                    imported_modules.add(module_name)
    except SyntaxError:
        # Fallback to regex if AST parsing fails
        import re
        import_patterns = [
            r'from\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            r'import\s+([a-zA-Z_][a-zA-Z0-9_]*)'
        ]
        for pattern in import_patterns:
            matches = re.findall(pattern, code)
            imported_modules.update(matches)
    
    return imported_modules

def _analyze_code_for_docker(implementation_code: str, test_code: str, spec: dict) -> dict:
    """Analyze generated code to determine Docker requirements using AST parsing."""
    import ast
    import re
    
    analysis = {
        'python_version': '3.11',
        'dependencies': set(),
        'has_web_server': False,
        'has_database': False,
        'has_async': False,
        'has_jwt_auth': False,
        'has_monitoring': False,
        'ports': [],
        'environment_vars': set(),
        'volumes': [],
        'health_check_endpoint': None
    }
    
    # Extract all imports using AST parsing
    combined_code = implementation_code + test_code
    imported_modules = _extract_imports_from_code(combined_code)
    
    # Package mapping - map module names to pip package names
    package_mapping = {
        'fastapi': ('fastapi', True, [8000]),
        'fastapi_limiter': ('fastapi-limiter', False, []),
        'flask': ('flask', True, [5000]),
        'django': ('django', True, [8000]),
        'jwt': ('PyJWT', False, []),
        'redis': ('redis', False, []),
        'psycopg2': ('psycopg2-binary', False, []),
        'pymongo': ('pymongo', False, []),
        'sqlalchemy': ('sqlalchemy', False, []),
        'pydantic': ('pydantic', False, []),
        'celery': ('celery', False, []),
        'prometheus_client': ('prometheus-client', False, []),
        'uvicorn': ('uvicorn', False, []),
        'aiofiles': ('aiofiles', False, []),
        'starlette': ('starlette', False, []),
        'passlib': ('passlib', False, []),
        'bcrypt': ('bcrypt', False, []),
        'cryptography': ('cryptography', False, []),
        'requests': ('requests', False, []),
        'httpx': ('httpx', False, []),
        'jinja2': ('jinja2', False, []),
        'aioredis': ('aioredis', False, []),
    }
    
    # Analyze imports and add dependencies
    for module in imported_modules:
        if module in package_mapping:
            package_name, is_web_server, default_ports = package_mapping[module]
            analysis['dependencies'].add(package_name)
            if is_web_server:
                analysis['has_web_server'] = True
                analysis['ports'].extend(default_ports)
    
    # Detect async usage
    if re.search(r'async def|await ', combined_code):
        analysis['has_async'] = True
        
    # Always add testing dependencies if pytest imports detected
    if 'pytest' in imported_modules or '@pytest' in combined_code:
        analysis['dependencies'].add('pytest')
        analysis['dependencies'].add('pytest-asyncio')
    
    # Detect JWT authentication
    if re.search(r'jwt\.|JWT|token', combined_code, re.IGNORECASE):
        analysis['has_jwt_auth'] = True
        analysis['environment_vars'].add('JWT_SECRET_KEY')
    
    # Detect database usage
    if any(db_pattern in combined_code.lower() for db_pattern in ['database', 'db', 'postgres', 'mongo', 'redis']):
        analysis['has_database'] = True
        analysis['environment_vars'].add('DATABASE_URL')
    
    # Detect monitoring/health endpoints
    if re.search(r'/health|/status|/metrics', combined_code):
        analysis['has_monitoring'] = True
        analysis['health_check_endpoint'] = '/health'
    
    # Analyze constraints for additional requirements
    constraints = spec.get('constraints', {})
    
    # Performance constraints might need monitoring
    if constraints.get('performance'):
        analysis['dependencies'].add('prometheus-client')
        analysis['has_monitoring'] = True
    
    # Security constraints
    if constraints.get('security'):
        analysis['environment_vars'].update(['SECRET_KEY', 'JWT_SECRET_KEY'])
    
    # Add common testing dependencies
    analysis['dependencies'].update(['pytest', 'pytest-asyncio'])
    
    return analysis

def _generate_dockerfile(analysis: dict, filenames: dict) -> str:
    """Generate Dockerfile content based on code analysis."""
    
    dockerfile_lines = [
        f"# Auto-generated Dockerfile for SDD project",
        f"FROM python:{analysis['python_version']}-slim",
        "",
        "# Set working directory",
        "WORKDIR /app",
        "",
        "# Install system dependencies",
        "RUN apt-get update && apt-get install -y \\",
        "    gcc \\",
        "    && rm -rf /var/lib/apt/lists/*",
        "",
        "# Copy requirements and install Python dependencies",
        "COPY requirements.txt .",
        "RUN pip install --no-cache-dir --upgrade pip",
        "RUN pip install --no-cache-dir -r requirements.txt",
        "",
        "# Copy application code",
        "COPY . .",
        "",
    ]
    
    # Add curl for health checks and general utility
    dockerfile_lines[7] = "RUN apt-get update && apt-get install -y \\"
    dockerfile_lines[8] = "    gcc \\"
    dockerfile_lines.insert(9, "    curl \\")
    dockerfile_lines[10] = "    && rm -rf /var/lib/apt/lists/*"
    
    # Add health check if available
    if analysis['health_check_endpoint']:
        dockerfile_lines.extend([
            "# Health check",
            f"HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \\",
            f"    CMD curl -f http://localhost:{analysis['ports'][0] if analysis['ports'] else 8000}{analysis['health_check_endpoint']} || exit 1",
            "",
        ])
    elif analysis['has_web_server']:
        # Default health check for web servers
        dockerfile_lines.extend([
            "# Default health check for web server",
            f"HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \\",
            f"    CMD curl -f http://localhost:{analysis['ports'][0] if analysis['ports'] else 8000}/ || exit 1",
            "",
        ])
    
    # Expose ports
    if analysis['ports']:
        for port in analysis['ports']:
            dockerfile_lines.append(f"EXPOSE {port}")
        dockerfile_lines.append("")
    
    # Add non-root user for security
    dockerfile_lines.extend([
        "# Create non-root user",
        "RUN groupadd -r appuser && useradd -r -g appuser appuser",
        "RUN chown -R appuser:appuser /app",
        "USER appuser",
        "",
    ])
    
    # Set default command based on web server detection
    module_name = filenames['module_name']
    if analysis['has_web_server']:
        if 'fastapi' in analysis['dependencies']:
            dockerfile_lines.append(f'CMD ["uvicorn", "{module_name}:app", "--host", "0.0.0.0", "--port", "8000"]')
        elif 'flask' in analysis['dependencies']:
            dockerfile_lines.append('CMD ["python", "-m", "flask", "run", "--host=0.0.0.0"]')
        elif 'django' in analysis['dependencies']:
            dockerfile_lines.append('CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]')
        else:
            dockerfile_lines.append(f'CMD ["python", "{filenames["implementation"]}"]')
    else:
        dockerfile_lines.append(f'CMD ["python", "{filenames["implementation"]}"]')
    
    return '\n'.join(dockerfile_lines)

def _generate_docker_compose(analysis: dict, spec: dict, filenames: dict) -> str:
    """Generate docker-compose.yml content with enhanced networking and volumes."""
    
    service_name = spec.get('feature', {}).get('name', 'sdd-service').lower().replace(' ', '-')
    
    compose_content = {
        'version': '3.8',
        'networks': {
            'sdd-network': {
                'driver': 'bridge'
            }
        },
        'services': {
            service_name: {
                'build': '.',
                'ports': [f"{port}:{port}" for port in analysis['ports']] if analysis['ports'] else ["8000:8000"],
                'environment': [],
                'depends_on': [],
                'volumes': ['./:/app'] if not analysis['has_web_server'] else [],
                'restart': 'unless-stopped',
                'networks': ['sdd-network'],
                'healthcheck': {
                    'test': ['CMD', 'curl', '-f', f"http://localhost:{analysis['ports'][0] if analysis['ports'] else 8000}/health"],
                    'interval': '30s',
                    'timeout': '3s',
                    'start_period': '5s',
                    'retries': 3
                } if analysis['has_web_server'] else None
            }
        }
    }
    
    # Add environment variables
    env_vars = []
    for env_var in analysis['environment_vars']:
        env_vars.append(f"{env_var}=${{{env_var}:-default_value}}")
    
    if env_vars:
        compose_content['services'][service_name]['environment'] = env_vars
    
    # Add database service if needed
    if analysis['has_database']:
        compose_content['services']['database'] = {
            'image': 'postgres:15-alpine',
            'environment': [
                'POSTGRES_DB=sdd_db',
                'POSTGRES_USER=sdd_user',
                'POSTGRES_PASSWORD=sdd_password'
            ],
            'ports': ['5432:5432'],
            'volumes': ['postgres_data:/var/lib/postgresql/data'],
            'restart': 'unless-stopped',
            'networks': ['sdd-network'],
            'healthcheck': {
                'test': ['CMD-SHELL', 'pg_isready -U sdd_user -d sdd_db'],
                'interval': '10s',
                'timeout': '5s',
                'retries': 5
            }
        }
        compose_content['services'][service_name]['depends_on'].append('database')
        compose_content['services'][service_name]['environment'].append('DATABASE_URL=postgresql://sdd_user:sdd_password@database:5432/sdd_db')
    
    # Add Redis if detected
    if 'redis' in analysis['dependencies']:
        compose_content['services']['redis'] = {
            'image': 'redis:7-alpine',
            'ports': ['6379:6379'],
            'restart': 'unless-stopped',
            'networks': ['sdd-network'],
            'healthcheck': {
                'test': ['CMD', 'redis-cli', 'ping'],
                'interval': '10s',
                'timeout': '3s',
                'retries': 3
            }
        }
        compose_content['services'][service_name]['depends_on'].append('redis')
        compose_content['services'][service_name]['environment'].append('REDIS_URL=redis://redis:6379')
    
    # Add monitoring if needed
    if analysis['has_monitoring']:
        compose_content['services']['prometheus'] = {
            'image': 'prom/prometheus:latest',
            'ports': ['9090:9090'],
            'volumes': ['./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml'],
            'restart': 'unless-stopped',
            'networks': ['sdd-network']
        }
    
    # Add volumes section if needed
    if analysis['has_database']:
        compose_content['volumes'] = {'postgres_data': {}}
    
    # Convert to YAML format
    import yaml
    return yaml.dump(compose_content, default_flow_style=False, sort_keys=False)

def _generate_requirements_txt(analysis: dict) -> str:
    """Generate requirements.txt based on detected dependencies."""
    
    # Base requirements mapping with versions
    dependency_versions = {
        'fastapi': 'fastapi>=0.104.0',
        'fastapi-limiter': 'fastapi-limiter>=0.1.6',
        'uvicorn': 'uvicorn[standard]>=0.24.0',
        'flask': 'flask>=3.0.0',
        'django': 'django>=4.2.0',
        'PyJWT': 'PyJWT>=2.8.0',
        'redis': 'redis>=5.0.0',
        'aioredis': 'aioredis>=2.0.0',
        'psycopg2-binary': 'psycopg2-binary>=2.9.0',
        'pymongo': 'pymongo>=4.6.0',
        'sqlalchemy': 'sqlalchemy>=2.0.0',
        'pydantic': 'pydantic>=2.5.0',
        'celery': 'celery>=5.3.0',
        'prometheus-client': 'prometheus-client>=0.19.0',
        'pytest': 'pytest>=7.4.0',
        'pytest-asyncio': 'pytest-asyncio>=0.21.0',
        'aiofiles': 'aiofiles>=23.2.0',
        'starlette': 'starlette>=0.27.0',
        'passlib': 'passlib[bcrypt]>=1.7.4',
        'bcrypt': 'bcrypt>=4.0.0',
        'cryptography': 'cryptography>=41.0.0',
        'requests': 'requests>=2.31.0',
        'httpx': 'httpx>=0.25.0',
        'jinja2': 'jinja2>=3.1.2',
    }
    
    requirements = []
    
    # Add detected dependencies
    for dep in sorted(analysis['dependencies']):
        if dep in dependency_versions:
            requirements.append(dependency_versions[dep])
        else:
            requirements.append(dep)
    
    # Add FastAPI dependencies if FastAPI is detected
    if 'fastapi' in analysis['dependencies']:
        requirements.append('uvicorn[standard]>=0.24.0')
    
    # Add async dependencies if async is detected
    if analysis['has_async']:
        requirements.append('aiofiles>=23.2.0')
    
    return '\n'.join(requirements)

def _generate_dockerignore() -> str:
    """Generate .dockerignore content."""
    
    dockerignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Git
.git/
.gitignore

# Docker
Dockerfile*
docker-compose*
.dockerignore

# Testing
.coverage
.pytest_cache/
.tox/
htmlcov/

# Logs
*.log
logs/

# Temporary files
*.tmp
*.temp
"""
    
    return dockerignore_content

def _generate_environment_files(analysis: dict, spec: dict) -> dict:
    """Generate environment configuration files for different deployment scenarios."""
    
    # Generate base environment variables
    base_env_vars = {}
    
    for env_var in analysis['environment_vars']:
        if env_var == 'JWT_SECRET_KEY':
            base_env_vars[env_var] = 'your-super-secret-jwt-key-change-in-production'
        elif env_var == 'SECRET_KEY':
            base_env_vars[env_var] = 'your-secret-key-change-in-production'
        elif env_var == 'DATABASE_URL':
            base_env_vars[env_var] = 'postgresql://sdd_user:sdd_password@database:5432/sdd_db'
        else:
            base_env_vars[env_var] = f'your-{env_var.lower().replace("_", "-")}-here'
    
    # Add common environment variables
    base_env_vars.update({
        'ENVIRONMENT': 'development',
        'LOG_LEVEL': 'INFO',
        'DEBUG': 'false'
    })
    
    # Generate different environment files
    env_files = {}
    
    # Development environment
    dev_env = base_env_vars.copy()
    dev_env.update({
        'ENVIRONMENT': 'development',
        'DEBUG': 'true',
        'LOG_LEVEL': 'DEBUG'
    })
    
    # Production environment
    prod_env = base_env_vars.copy()
    prod_env.update({
        'ENVIRONMENT': 'production',
        'DEBUG': 'false',
        'LOG_LEVEL': 'INFO'
    })
    
    # Testing environment  
    test_env = base_env_vars.copy()
    test_env.update({
        'ENVIRONMENT': 'testing',
        'DEBUG': 'true',
        'LOG_LEVEL': 'DEBUG',
        'DATABASE_URL': 'postgresql://test_user:test_password@database:5432/test_db'
    })
    
    # Convert to .env file format
    def dict_to_env_file(env_dict):
        lines = ['# Auto-generated environment configuration']
        for key, value in sorted(env_dict.items()):
            lines.append(f'{key}={value}')
        return '\n'.join(lines)
    
    env_files['.env.development'] = dict_to_env_file(dev_env)
    env_files['.env.production'] = dict_to_env_file(prod_env)
    env_files['.env.testing'] = dict_to_env_file(test_env)
    
    # Generate docker-compose override files
    env_files['docker-compose.override.yml'] = _generate_compose_override('development', spec)
    env_files['docker-compose.prod.yml'] = _generate_compose_override('production', spec)
    env_files['docker-compose.test.yml'] = _generate_compose_override('testing', spec)
    
    # Generate deployment README
    env_files['DEPLOYMENT.md'] = _generate_deployment_readme(analysis, spec)
    
    return env_files

def _generate_compose_override(environment: str, spec: dict) -> str:
    """Generate docker-compose override files for different environments."""
    
    # Generate appropriate module name
    filenames = _generate_filenames(spec)
    module_name = filenames['module_name']
    
    if environment == 'development':
        override_content = {
            'version': '3.8',
            'services': {
                'app': {
                    'volumes': ['./:/app'],
                    'environment': [
                        'DEBUG=true',
                        'LOG_LEVEL=DEBUG'
                    ],
                    'command': ['uvicorn', f'{module_name}:app', '--host', '0.0.0.0', '--port', '8000', '--reload']
                }
            }
        }
    elif environment == 'production':
        override_content = {
            'version': '3.8',
            'services': {
                'app': {
                    'environment': [
                        'DEBUG=false',
                        'LOG_LEVEL=INFO'
                    ],
                    'deploy': {
                        'replicas': 2,
                        'resources': {
                            'limits': {
                                'cpus': '1',
                                'memory': '1G'
                            },
                            'reservations': {
                                'cpus': '0.5',
                                'memory': '512M'
                            }
                        }
                    }
                }
            }
        }
    else:  # testing
        override_content = {
            'version': '3.8',
            'services': {
                'app': {
                    'environment': [
                        'DEBUG=true',
                        'LOG_LEVEL=DEBUG'
                    ],
                    'command': ['python', '-m', 'pytest', '-v']
                },
                'database': {
                    'environment': [
                        'POSTGRES_DB=test_db',
                        'POSTGRES_USER=test_user',
                        'POSTGRES_PASSWORD=test_password'
                    ]
                }
            }
        }
    
    import yaml
    return yaml.dump(override_content, default_flow_style=False, sort_keys=False)

def _generate_deployment_readme(analysis: dict, spec: dict) -> str:
    """Generate deployment documentation."""
    
    service_name = spec.get('feature', {}).get('name', 'SDD Service')
    
    readme_content = f"""# {service_name} - Deployment Guide

This guide covers deploying your {service_name} using Docker and docker-compose.

## Quick Start

### Development
```bash
# Start development environment with hot reload
docker-compose -f docker-compose.yml -f docker-compose.override.yml up

# Or use the shortcut (override.yml is loaded by default)
docker-compose up
```

### Production
```bash
# Start production environment
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Testing
```bash
# Run tests in containerized environment
docker-compose -f docker-compose.yml -f docker-compose.test.yml up --abort-on-container-exit
```

## Environment Configuration

The application supports three environments:

- **Development** (`.env.development`): Debug enabled, hot reload, verbose logging
- **Production** (`.env.production`): Optimized for performance and security
- **Testing** (`.env.testing`): Configured for automated testing

## Services

### Application
- **Port**: {analysis['ports'][0] if analysis['ports'] else 8000}
- **Health Check**: Available at `/health` endpoint
- **Networks**: Connected to `sdd-network`

"""

    if analysis['has_database']:
        readme_content += """### Database (PostgreSQL)
- **Port**: 5432
- **Database**: sdd_db
- **Default Credentials**: sdd_user/sdd_password (change in production!)
- **Health Check**: pg_isready command
- **Persistence**: Data stored in `postgres_data` volume

"""

    if 'redis' in analysis['dependencies']:
        readme_content += """### Redis Cache
- **Port**: 6379  
- **Health Check**: Redis ping command
- **Use**: Caching and session storage

"""

    if analysis['has_monitoring']:
        readme_content += """### Monitoring (Prometheus)
- **Port**: 9090
- **Metrics**: Application metrics collected automatically
- **Dashboard**: Access Prometheus UI at http://localhost:9090

"""

    readme_content += """## Security Considerations

1. **Change default passwords** in production environment
2. **Set strong JWT secrets** in environment variables
3. **Use HTTPS** in production (configure reverse proxy)
4. **Review exposed ports** and limit access as needed
5. **Regular security updates** for base images

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
"""

    for env_var in sorted(analysis['environment_vars']):
        description = {
            'JWT_SECRET_KEY': 'Secret key for JWT token signing',
            'SECRET_KEY': 'General application secret key',
            'DATABASE_URL': 'PostgreSQL connection string',
        }.get(env_var, f'Configuration for {env_var}')
        
        readme_content += f"| `{env_var}` | {description} | See .env files |\n"

    readme_content += """
## Scaling

For production scaling:

```bash
# Scale application instances
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --scale app=3

# Or use Docker Swarm for production orchestration
docker stack deploy -c docker-compose.yml -c docker-compose.prod.yml myapp
```

## Troubleshooting

### Common Issues

1. **Port conflicts**: Change port mappings in docker-compose.yml
2. **Database connection issues**: Ensure database service is healthy
3. **Permission issues**: Check file ownership for volumes

### Logs

```bash
# View application logs
docker-compose logs app

# Follow logs in real-time
docker-compose logs -f app

# View all service logs
docker-compose logs
```

### Health Checks

All services include health checks. Check status with:

```bash
docker-compose ps
```

## Generated Files

This deployment was auto-generated by SDD (Specification-Driven Development) based on your requirements and detected dependencies.

- `Dockerfile`: Optimized Python container
- `docker-compose.yml`: Multi-service orchestration
- `requirements.txt`: Python dependencies
- `.env.*`: Environment-specific configurations
- Override files: Environment-specific docker-compose configurations

For more information about SDD, visit the project documentation.
"""

    return readme_content