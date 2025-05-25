import sys
import subprocess
from pathlib import Path

# Ensure project root is on sys.path for imports
sys.path.insert(0, str(Path(__file__).parents[2]))

import pytest

from orchestrator.handoff_flow import handoff_flow


def test_spec_to_code_pipeline(tmp_path):
    """
    Integration test for spec-to-code generation pipeline.

    Given a sample specification, invoke the handoff flow and verify that
    generated code compiles and passes its own unit tests.
    """
    # Path to the sample specification in the examples directory
    spec_path = Path(__file__).parents[2] / "examples" / "task_manager" / "specification.yaml"
    output_dir = tmp_path / "generated"
    # Execute the pipeline (expected to raise NotImplementedError for now)
    with pytest.raises(NotImplementedError):
        handoff_flow(spec_path, output_dir)

    # In future, once implemented, we will assert:
    # - output_dir contains generated code and tests
    # - pytest passes within output_dir
    # Example:
    # result = subprocess.run(["pytest", "-q"], cwd=output_dir)
    # assert result.returncode == 0, result.stdout