# Specification-Driven Development (SDD) Project Context
#
## Project Overview
This project implements a revolutionary approach to software development where humans write behavioral specifications and AI handles all implementation details. The system uses MCP (Model Context Protocol) servers to bridge specifications and implementation.
#
## Core Philosophy
- Humans define WHAT (behaviors and constraints), not HOW (implementation)
- AI generates, tests, optimizes, and monitors all code
- Systems are defined by scenarios (functional requirements) and constraints (non-functional requirements)
- Implementation iterates automatically until all constraints are met
#
## Architecture Overview
#
### 1. Specification Layer
- YAML files define scenarios and constraints
- Scenarios use Given/When/Then format
- Constraints cover performance, security, scalability, reliability
#
### 2. MCP Server Layer
- **SpecificationMCPServer**: Manages scenarios, validates conflicts, suggests coverage
- **ImplementationMCPServer**: Generates code, runs tests, verifies constraints
- **MonitoringMCPServer**: Tracks degradation, predicts failures, auto-remediates
- **DebuggerMCPServer**: Provides behavior-centric debugging without code exposure
#
### 3. Orchestration Layer
- **SDDOrchestrator**: Coordinates the entire flow from spec to deployment
- Integrates with AI agents (Claude, GPT-4, Codex) via MCP
- Manages human review points and iterative optimization
#
### 4. Operational Layer
- Behavior-centric monitoring (not code-centric)
- Predictive degradation detection
- Automatic performance optimization
- Incident analysis in business terms
#
## Implementation Priority
#
1. **Phase 1 (MVP)**: Basic scenario-to-code generation
   - Start with simple CRUD operations
   - Direct AI API calls
   - Basic test generation

2. **Phase 2**: MCP Integration
   - Implement core MCP servers
   - Add constraint verification
   - Enable iterative optimization

3. **Phase 3**: Production Features
   - Degradation detection
   - Auto-remediation
   - Complex distributed systems
#
## Key Files Structure
```
sdd-project/
├── PROJECT_CONTEXT.md          # This file
├── README.md                   # Human-readable overview
├── docs/
│   ├── ARCHITECTURE.md         # Detailed architecture
│   ├── PHILOSOPHY.md           # Core concepts and principles
│   └── EXAMPLES.md             # Complete examples
├── mcp_servers/
│   ├── specification_server.py # Spec management
│   ├── implementation_server.py # Code generation
│   ├── monitoring_server.py    # Production monitoring
│   └── debugger_server.py      # Behavior debugging
├── orchestrator/
│   ├── sdd_orchestrator.py     # Main orchestration
│   └── handoff_flow.py         # Spec-to-impl flow
├── core/
│   ├── scenario_validator.py   # Scenario validation
│   ├── constraint_verifier.py  # Constraint checking
│   └── degradation_hunter.py   # Predictive monitoring
├── examples/
│   ├── task_manager/           # Simple example
│   └── ecommerce_platform/     # Complex example
└── tests/
    └── integration/            # System tests
```
#
## Critical Implementation Notes
#
1. **MCP Tool Semantics**: Tools should understand business domains, not just technical operations
2. **Iterative Verification**: Every generation must be tested against constraints
3. **Human Review Points**: Only for scenario approval, never for code review
4. **Degradation Detection**: Must predict failures before they impact users
5. **Debugging Without Code**: Operators interact with behaviors, not implementations
#
## AI Agent Implementation Guide
#
When implementing this system:

1. Start with `examples/task_manager/` for a working prototype
2. Use the MCP servers as the primary interface between components
3. Ensure all generated code includes comprehensive observability
4. Test constraint verification before implementing optimization
5. Focus on semantic correctness over syntactic preferences
#
## Integration Points
#
- **AI Models**: Claude (via Anthropic API), GPT-4/o3 (via OpenAI API)
- **MCP Protocol**: Follow the official MCP specification
- **Testing**: Pytest for Python, equivalent for other languages
- **Monitoring**: Prometheus/Grafana compatible metrics
- **Deployment**: Docker containers with Kubernetes orchestration