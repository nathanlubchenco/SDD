# Getting Started with SDD

Welcome to **Specification-Driven Development** - the revolutionary system where AI debugs and improves its own code through iterative feedback loops!

## Quick Start (2 minutes)

### 1. Install and Setup

```bash
# Clone and setup
git clone <your-repo-url>
cd SDD
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. See the System in Action

```bash
# Demo the architecture (no API key needed)
python examples/simple_demo.py
```

This shows you:
- ✅ All 6 MCP servers initialized
- ✅ Workspace structure and file organization  
- ✅ The iterative development process (Generate→Test→Analyze→Refine)
- ✅ Quality scoring system (0-100 scale)

### 3. Test the System

```bash
# Run basic tests
python -m pytest tests/ -v
```

Expected output: **5 tests passed** ✅

## Full AI Development (Requires OpenAI API)

### 1. Set Your API Key

```bash
export OPENAI_API_KEY="your-openai-api-key-here"
```

### 2. Experience AI That Improves Its Own Code

```bash
python examples/iterative_development_demo.py
```

This demonstrates:
- 🤖 AI analyzing deliberately flawed code
- 📊 Quality analysis identifying specific issues
- ✨ Automatic code refinement and improvement
- 📈 Quality scores improving from ~45 to 85+

## What Makes This Revolutionary?

### Traditional AI Development
```
Human writes prompt → AI generates code → Hope it works → Manual debugging
```

### SDD Iterative Development  
```
Human writes specification → AI generates code → AI tests code → AI analyzes issues → AI refines code → Repeat until perfect
```

## Key Capabilities

- **🔄 Self-Healing Code**: AI fixes its own bugs through testing feedback
- **📈 Quality Convergence**: Predictable improvement toward quality targets
- **🚀 No Complexity Ceiling**: Can handle arbitrarily complex implementations
- **🤖 Autonomous Development**: Minimal human intervention required

## Architecture Overview

### 6 MCP Servers
1. **SpecificationMCPServer** - Manages behavioral specifications
2. **ImplementationMCPServer** - Generates and refines code  
3. **TestingMCPServer** - Runs tests and provides feedback
4. **AnalysisMCPServer** - Quality analysis and suggestions
5. **DockerMCPServer** - Container generation and optimization
6. **IterativeOrchestrator** - Coordinates the entire cycle

### Quality Scoring (0-100)
- **Test Results (40%)**: Syntax, dependencies, linting, unit tests
- **Code Quality (40%)**: Complexity, maintainability, readability  
- **Performance (20%)**: Efficiency analysis, bottleneck detection

### Quality Targets
- **90-100**: Excellent (production-ready) 🟢
- **75-89**: Good (minor improvements needed) 🟡  
- **60-74**: Fair (moderate refactoring required) 🟠
- **0-59**: Poor (significant improvements needed) 🔴

## Next Steps

### 1. Try Different Scenarios

Create your own specification file:

```yaml
# my_service.yaml
scenarios:
  - scenario: Process user request
    given: A web service is running
    when: User submits a valid request
    then: Response is returned within 100ms

constraints:
  performance:
    response_time: "< 100ms"
  security:
    input_validation: "All inputs must be validated"
```

### 2. Generate Implementation

```python
from orchestrator.iterative_orchestrator import IterativeOrchestrator

orchestrator = IterativeOrchestrator("my_workspace")
await orchestrator.initialize()

result = await orchestrator.iterative_development_cycle(
    specification_path="my_service.yaml",
    target_quality_score=85
)

print(f"Success: {result['success']}")
print(f"Quality Score: {result['final_quality_score']}")
```

### 3. Build and Deploy

```bash
# Navigate to generated code
cd workspaces/my_workspace/implementation

# Build Docker container
docker build -t my-service .

# Run the service
docker compose up -d

# Test it works
curl http://localhost:8000/health
```

## Troubleshooting

### Common Issues

**Import Errors**: Make sure you're in the project root and have activated the virtual environment.

**No API Key**: The simple demo works without an API key. Full AI features require `OPENAI_API_KEY`.

**Docker Issues**: Use `docker compose` (not `docker-compose`) for newer Docker versions.

**Test Failures**: Basic tests should pass without API keys. If they fail, check Python version (3.11+ recommended).

### Getting Help

- **System Architecture**: `python examples/simple_demo.py`  
- **Basic Tests**: `python -m pytest tests/ -v`
- **Full Documentation**: See `docs/ITERATIVE_DEVELOPMENT.md`

---

**🎉 Congratulations!** You're now ready to experience the future of AI-powered software development where AI debugs and improves its own code automatically! 🚀🤖