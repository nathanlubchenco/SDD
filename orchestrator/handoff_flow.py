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
        _write_files_safely(output_dir, implementation_code, test_code)
        
        logger.info(f"Successfully generated code in {output_dir}")
        
    except Exception as e:
        logger.error(f"Handoff flow failed: {str(e)}")
        # Clean up partial files on failure
        _cleanup_on_failure(output_dir)
        raise

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
1. Import all necessary classes from task_manager module
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

def _write_files_safely(output_dir: Path, implementation_code: str, test_code: str):
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
        
        # If validation passes, move to final location
        shutil.move(tmp_impl_path, output_dir / "task_manager.py")
        shutil.move(tmp_test_path, output_dir / "test_task_manager.py")
        
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

def _cleanup_on_failure(output_dir: Path):
    """Clean up any partially created files on failure."""
    try:
        if output_dir.exists():
            for file in ["task_manager.py", "test_task_manager.py", "__init__.py"]:
                (output_dir / file).unlink(missing_ok=True)
    except Exception:
        pass  # Best effort cleanup