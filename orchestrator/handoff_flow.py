"""
Spec-to-implementation handoff flow for SDD orchestrator.
"""

import yaml
from pathlib import Path
from core.ai_client import chat_completion

def handoff_flow(spec_path: Path, output_dir: Path):
    """
    Entry point for spec-to-implementation pipeline.

    Args:
        spec_path: Path to the specification YAML file.
        output_dir: Directory where generated code will be placed.
    """
    # Load and parse the specification
    with open(spec_path, 'r') as f:
        spec = yaml.safe_load(f)
    
    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate implementation based on spec
    implementation_code = generate_implementation(spec)
    
    # Generate tests based on scenarios
    test_code = generate_tests(spec)
    
    # Write generated files
    (output_dir / "task_manager.py").write_text(implementation_code)
    (output_dir / "test_task_manager.py").write_text(test_code)
    (output_dir / "__init__.py").write_text("")

def generate_implementation(spec):
    """Generate Python implementation code from specification."""
    
    feature = spec.get('feature', {})
    if isinstance(feature, dict):
        feature_description = feature.get('name', 'Unknown Feature')
        feature_desc_full = feature.get('description', '')
    else:
        feature_description = str(feature)
        feature_desc_full = ''
    
    scenarios = spec.get('scenarios', [])
    constraints = spec.get('constraints', {})
    
    # Generate comprehensive prompt
    prompt_messages = build_implementation_prompt(
        feature_description, feature_desc_full, scenarios, constraints
    )
    
    code = chat_completion(prompt_messages, max_tokens=3000)
    return clean_code_response(code)

def generate_tests(spec):
    """Generate test code based on scenarios."""
    
    feature = spec.get('feature', {})
    if isinstance(feature, dict):
        feature_name = feature.get('name', 'Unknown Feature')
    else:
        feature_name = str(feature)
    
    scenarios = spec.get('scenarios', [])
    
    prompt_messages = build_test_prompt(feature_name, scenarios)
    
    code = chat_completion(prompt_messages, max_tokens=2500)
    return clean_code_response(code)

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
    """Format constraints for the implementation prompt."""
    if not constraints:
        return "NON-FUNCTIONAL REQUIREMENTS: None specified"
    
    formatted = ["NON-FUNCTIONAL REQUIREMENTS:"]
    requirements = extract_constraint_requirements(constraints)
    
    for req in requirements:
        formatted.append(f"- {req}")
    
    if not requirements:
        formatted.append("- None specified")
    
    # Add implementation notes for common constraint types
    if any('latency' in req.lower() or 'response time' in req.lower() for req in requirements):
        formatted.append("\nImplementation Note: Consider adding timing/performance monitoring")
    
    if any('authentication' in req.lower() or 'jwt' in req.lower() for req in requirements):
        formatted.append("\nImplementation Note: Add authentication validation to relevant methods")
        
    return '\n'.join(formatted)