# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Specification-Driven Development (SDD) is a research project exploring AI-powered software development where humans define behaviors in plain English and AI generates, optimizes, and maintains the implementation.

**Status**: Complete Vaporware (research/prototype phase)

## Common Commands

### Development Setup
```bash
# Local Python setup
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Install SDD CLI (optional)
python install_cli.py

# Docker alternative
docker-compose up -d
docker-compose exec python bash
```

## SDD CLI Tool

The SDD CLI provides a convenient command-line interface for generating, testing, and analyzing code.

### Installation and Setup
```bash
# Basic setup - run from project directory
python sdd_cli.py --help

# Optional: Install for global access
python install_cli.py
# Then add to PATH as instructed
```

### CLI Commands

#### Generate Code from Specification
```bash
# Basic generation
python sdd_cli.py generate specs/my_app.yaml

# Full options
python sdd_cli.py generate specs/my_app.yaml \
  --output workspaces/my_app \
  --model gpt-4 \
  --target-score 85 \
  --max-iterations 5 \
  --include-docker \
  --framework fastapi \
  --verbose

# Save detailed results
python sdd_cli.py generate specs/my_app.yaml --save-results results.json
```

#### Test Existing Implementation
```bash
# Test workspace
python sdd_cli.py test workspaces/my_app --verbose

# Save test results
python sdd_cli.py test workspaces/my_app --save-results test_results.json
```

#### Analyze Code Quality
```bash
# Basic analysis
python sdd_cli.py analyze src/my_code.py

# Comprehensive analysis with suggestions
python sdd_cli.py analyze src/my_code.py \
  --include-suggestions \
  --analysis-type comprehensive \
  --save-results analysis.json
```

#### Configuration Management
```bash
# Show current configuration
python sdd_cli.py config --show

# List available AI models
python sdd_cli.py config --list-models

# Test AI connection
python sdd_cli.py config --test-connection --provider openai
```

### Quick Start with CLI
```bash
# 1. Set up your API key
export OPENAI_API_KEY="your-api-key-here"

# 2. Check configuration
python sdd_cli.py config --show

# 3. Create a specification file
mkdir -p specs
cat > specs/calculator.yaml << 'EOF'
scenarios:
  - scenario: Add two numbers
    given: A calculator service
    when: User requests addition of 5 and 3
    then: Result is 8
    
  - scenario: Handle division by zero
    given: A calculator service
    when: User attempts to divide by zero
    then: Error message is returned
    
constraints:
  performance:
    response_time: "< 100ms"
  reliability:
    error_handling: "Graceful handling of invalid inputs"
EOF

# 4. Generate code (starts generation, may require manual file extraction)
python sdd_cli.py generate specs/calculator.yaml \
  --output workspaces/calculator \
  --max-iterations 1 \
  --no-docker

# 5. Check results and next steps (shown by CLI)
cd workspaces/calculator
# Follow the next steps provided by the CLI output
```

### Current CLI Status
✅ **Working Features:**
- Specification loading and validation
- AI-powered code generation 
- Configuration management
- Code analysis (basic)
- Comprehensive help system

⚠️ **Current Limitations (Expected for prototype):**
- Quality scoring returns 0 (mock servers)
- File extraction may require manual steps
- Refinement iterations have issues
- Docker generation limited

💡 **Recommended Usage:**
```bash
# Most reliable current workflow
python sdd_cli.py generate specs/my_app.yaml \
  --max-iterations 1 \
  --no-docker \
  --save-results results.json

# Extract generated code from results (manual step currently required)
python -c "
import json
with open('results.json', 'r') as f:
    data = json.load(f)
    iterations = data.get('iterations', [])
    if iterations:
        impl = iterations[0].get('implementation')
        if impl and hasattr(impl, 'get'):
            print('Generated code available in results.json')
            print('Main module:', len(impl.get('main_module', '')), 'characters')
"
```

📋 **CLI Testing Results**: See `CLI_TEST_SUMMARY.md` for comprehensive testing results and current capabilities.

### Testing
```bash
# Run all tests
pytest tests/ -v

# Run specific test categories
pytest tests/unit/ -v          # Unit tests
pytest tests/integration/ -v   # Integration tests  
pytest tests/mcp/ -v          # MCP server tests

# Run individual test files
python tests/integration/test_logging_integration.py
python tests/mcp/test_specification_mcp.py
python tests/mcp/test_docker_mcp.py

# Run system demos (no API key required)
python examples/simple_demo.py

# Run full AI development demo (requires OpenAI API key - shows system architecture)
python examples/iterative_development_demo.py

# Via Docker
docker-compose run --rm python pytest
```

## Architecture

### Core Components
- **src/core/**: Core SDD functionality (constraint verification, performance optimization, scenario validation, centralized logging via sdd_logger.py)
- **src/mcp_servers/**: MCP (Model Context Protocol) servers - specialized AI agents for different aspects:
  - `base_mcp_server.py`: Foundation for all MCP server implementations
  - `specification_mcp_server.py` & `specification_server.py`: Manages scenarios and constraints
  - `implementation_server.py`: Handles code generation and testing
  - `testing_mcp_server.py`: Comprehensive testing with structured feedback
  - `analysis_mcp_server.py`: Code quality analysis and AI-powered suggestions
  - `docker_mcp_server.py`: AI-driven Docker artifact generation
  - `monitoring_server.py`: Production monitoring and auto-remediation
  - `debugger_server.py`: Behavior-focused debugging
- **src/orchestrator/**: Coordinates the end-to-end SDD workflow from specification to deployment
- **examples/**: Real-world examples showing SDD specifications (task_manager, ecommerce_platform)
- **tests/**: Organized test suite with unit, integration, and MCP tests
- **workspaces/**: Generated implementations and artifacts from SDD development cycles
- **archive_deprecated/**: Historical code for reference (not actively maintained)
- **docs/**: Documentation including architecture, examples, and logging guides
  - `ARCHITECTURE.md`: Technical deep dive into system design
  - `EXAMPLES.md`: Detailed examples and patterns  
  - `ITERATIVE_DEVELOPMENT.md`: Complete development process documentation
  - `PHILOSOPHY.md`: Why specification-driven development matters
  - `GETTING_STARTED.md`: Quick start guide
  - `LOGGING_SUMMARY.md`: Logging integration details

### Specification Format
SDD uses YAML-based specifications with two key components:

1. **Scenarios**: Given/When/Then behavior descriptions
2. **Constraints**: Non-functional requirements (performance, security, scalability, reliability)

Example:
```yaml
scenario: Process payment
  given: Customer has items in cart totaling $100
  when: Customer submits valid credit card
  then: 
    - Payment is processed within 5 seconds
    - Order confirmation is sent
    - Inventory is updated

constraints:
  performance:
    - name: API response time
      requirement: p95 latency < 100ms for all read operations
```

### Implementation Flow
1. Human writes scenarios → AI generates edge cases → Human reviews/approves
2. AI generates implementation → Tests → Constraint verification
3. If constraints fail → AI optimizes → Repeat verification
4. Deploy → Continuous monitoring → Auto-remediation

## Key Philosophy
- **Behavior-First**: Everything defined in terms of observable behavior, not code
- **Constraint-Driven**: Non-functional requirements are first-class citizens  
- **Human-in-the-Loop**: Humans approve behaviors, AI handles implementation details
- **Self-Healing**: Systems detect and fix their own degradation

## AI Client Configuration

The system supports both OpenAI and Anthropic models. Configure via environment variables:

```bash
# Provider selection (defaults to openai)
export AI_PROVIDER=anthropic  # or openai

# API keys (at least one required)
export OPENAI_API_KEY=your_openai_key
export ANTHROPIC_API_KEY=your_anthropic_key

# Optional: Override default models
export OPENAI_MODEL=gpt-4-turbo
export ANTHROPIC_MODEL=claude-3-opus-20240229
```

### Available Commands
```bash
# Show current configuration
python src/core/ai_config.py config

# List available models
python src/core/ai_config.py models

# Test connection
python src/core/ai_config.py test --provider anthropic --model claude-3-sonnet-20240229
```

## Dependencies
- Python 3.11+
- OpenAI API (configured via OPENAI_API_KEY environment variable)
- Anthropic API (configured via ANTHROPIC_API_KEY environment variable)
- pytest for testing
- PyYAML for specification parsing

## Other AI Agents
Sometimes you cooperate with codex-cli.  Codex context can be found in codex.md or codex_memory.txt.  You can also write notes and research to yourself in claude_memory.txt.
