# Task Manager Example

This example demonstrates the Scenario-Driven Development (SDD) prototype for a Task Management System.

## Specification

See `specification.yaml` for the scenarios and constraints defining the system behavior.

## Usage

```bash
# Run quickstart demo with predefined specification
python quickstart.py

# Review and approve scenarios interactively
python scenario_reviewer.py specification.yaml

# Execute the SDD prototype loop
python sdd_prototype.py specification.yaml
```

## Files

- `specification.yaml`: Defines feature, constraints, and scenarios.
- `quickstart.py`: Demonstrates a scripted SDD workflow without AI.
- `scenario_reviewer.py`: Interactive scenario review loop.
- `sdd_prototype.py`: Core SDD prototype class and AI prompt stubs.