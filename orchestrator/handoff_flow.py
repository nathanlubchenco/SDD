"""
Spec-to-implementation handoff flow for SDD orchestrator.
"""

import yaml
from pathlib import Path
from core.openai_client import chat_completion

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
    else:
        feature_description = str(feature)
    scenarios = spec.get('scenarios', [])
    
    # Create prompt for OpenAI to generate implementation
    prompt_messages = [
        {
            "role": "system",
            "content": "You are an expert Python developer. Generate clean, production-ready Python code based on specifications."
        },
        {
            "role": "user", 
            "content": f"""
Generate a Python implementation for: {feature_description}

Based on these scenarios:
{yaml.dump(scenarios, indent=2)}

Requirements:
1. Use dataclasses for data models
2. Include proper error handling
3. Use type hints throughout
4. Create a TaskManager class with methods for each scenario
5. Include basic validation and business logic
6. Keep it simple but functional

IMPORTANT: Respond with ONLY valid Python code. No explanations, no markdown formatting, no additional text before or after the code.
"""
        }
    ]
    
    code = chat_completion(prompt_messages, max_tokens=2000)
    return clean_code_response(code)

def generate_tests(spec):
    """Generate test code based on scenarios."""
    
    scenarios = spec.get('scenarios', [])
    
    prompt_messages = [
        {
            "role": "system",
            "content": "You are an expert test developer. Generate comprehensive pytest test code."
        },
        {
            "role": "user",
            "content": f"""
Generate pytest test code for these scenarios:
{yaml.dump(scenarios, indent=2)}

Requirements:
1. Import TaskManager from task_manager module
2. Create one test function per scenario
3. Use descriptive test names matching scenario names
4. Test all the 'then' conditions from each scenario
5. Use pytest fixtures where appropriate
6. Include proper assertions

IMPORTANT: Respond with ONLY valid Python test code. No explanations, no markdown formatting, no additional text before or after the code.
"""
        }
    ]
    
    code = chat_completion(prompt_messages, max_tokens=2000)
    return clean_code_response(code)

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