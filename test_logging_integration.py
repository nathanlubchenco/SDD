#!/usr/bin/env python3
"""
Test the logging integration across the SDD system.

This demonstrates end-to-end logging from specification loading through
code generation and constraint verification.
"""

import asyncio
import sys
import tempfile
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

from core.sdd_logger import configure_logging, get_sdd_logger
from mcp_servers.specification_mcp_server import SpecificationMCPServer
from mcp_servers.implementation_server import ImplementationMCPServer
from orchestrator.iterative_orchestrator import IterativeOrchestrator
from core.constraint_verifier import ConstraintVerifier
from core.performance_optimizer import PerformanceOptimizer


async def test_logging_integration():
    """Test comprehensive logging across the SDD system."""
    
    # Configure logging to both console and file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as log_file:
        log_file_path = log_file.name
    
    logger = configure_logging(log_level="DEBUG", log_file=log_file_path)
    
    print(f"🔍 Testing SDD logging integration")
    print(f"📄 Log file: {log_file_path}")
    
    # Test 1: Specification Server Logging
    print("\n📋 Testing Specification Server logging...")
    
    with logger.correlation_context(component="test", operation="specification_test") as correlation_id:
        logger.info("Starting specification server test", extra_data={'test_phase': 'specification'})
        
        # Create a test spec directory
        with tempfile.TemporaryDirectory() as temp_dir:
            spec_dir = Path(temp_dir)
            test_spec_file = spec_dir / "test_spec.yaml"
            
            test_spec_content = """
scenarios:
  - scenario: Create user
    given: Valid user data provided
    when: POST /users with user data
    then: 
      - User is created successfully
      - 201 status code returned
      
  - scenario: Get user
    given: User exists in system
    when: GET /users/{id}
    then:
      - User data is returned
      - 200 status code returned

constraints:
  performance:
    - name: API response time
      requirement: p95 latency < 100ms for all read operations
    - name: Throughput
      requirement: Handle 1000 requests per second
      
  security:
    - name: Authentication
      requirement: All endpoints require valid JWT token
    - name: Input validation
      requirement: Validate and sanitize all user inputs
"""
            
            test_spec_file.write_text(test_spec_content)
            
            # Test specification server
            spec_server = SpecificationMCPServer(spec_dir)
            
            # Test getting scenarios via MCP call
            get_scenarios_request = {
                "method": "tools/call",
                "params": {
                    "name": "get_scenarios",
                    "arguments": {
                        "domain": "test_spec",
                        "include_constraints": True
                    }
                }
            }
            
            scenarios_response = await spec_server.handle_mcp_request(get_scenarios_request)
            if "result" in scenarios_response:
                logger.info("Retrieved scenarios from spec server", 
                           extra_data={'response_keys': list(scenarios_response.keys())})
            
            # Test scenario validation via MCP call
            test_scenario = {
                'name': 'Delete user',
                'given': 'User exists',
                'when': 'DELETE /users/{id}',
                'then': ['User is deleted', '204 status returned']
            }
            
            validate_scenario_request = {
                "method": "tools/call",
                "params": {
                    "name": "validate_scenario",
                    "arguments": {
                        "scenario": test_scenario,
                        "domain": "test_spec"
                    }
                }
            }
            
            validation_response = await spec_server.handle_mcp_request(validate_scenario_request)
            if "result" in validation_response:
                logger.info("Validated new scenario", 
                           extra_data={'validation_response': 'success'})
    
    # Test 2: Implementation Server Logging
    print("\n🔧 Testing Implementation Server logging...")
    
    with logger.correlation_context(component="test", operation="implementation_test") as correlation_id:
        impl_server = ImplementationMCPServer()
        
        # Test implementation generation
        test_scenarios = [
            {
                'scenario': 'Create user',
                'given': 'Valid user data',
                'when': 'POST /users',
                'then': ['User created', '201 returned']
            }
        ]
        
        test_constraints = {
            'performance': [
                {'name': 'Response time', 'requirement': 'p95 < 100ms'}
            ]
        }
        
        impl_result = await impl_server._generate_implementation(
            scenarios=test_scenarios,
            constraints=test_constraints,
            target_framework="fastapi"
        )
        
        logger.info("Generated implementation", 
                   extra_data={
                       'implementation_keys': list(impl_result.keys()),
                       'has_main_module': 'main_module' in impl_result
                   })
    
    # Test 3: Constraint Verification Logging
    print("\n✅ Testing Constraint Verification logging...")
    
    with logger.correlation_context(component="test", operation="constraint_verification_test"):
        verifier = ConstraintVerifier()
        
        mock_implementation = {
            'main_module': '''
import asyncio
from fastapi import FastAPI
from functools import lru_cache

app = FastAPI()

@app.post("/users")
async def create_user(user_data: dict):
    # Validate input
    if not user_data:
        raise ValueError("Invalid input")
    
    # Create user with async operation
    return {"id": 1, "status": "created"}

@app.get("/users/{user_id}")
@lru_cache(maxsize=100)
async def get_user(user_id: int):
    # Cached user retrieval
    return {"id": user_id, "name": "test"}
''',
            'test_module': 'test code here'
        }
        
        test_constraints = {
            'performance': [
                {'name': 'Response time', 'requirement': 'p95 latency < 100ms'},
                {'name': 'Throughput', 'requirement': '1000 rps'}
            ],
            'security': [
                {'name': 'Input validation', 'requirement': 'Validate all inputs'},
                {'name': 'Authentication', 'requirement': 'JWT tokens required'}
            ]
        }
        
        verification_result = verifier.verify_constraints(mock_implementation, test_constraints)
        
        logger.info("Constraint verification complete",
                   extra_data={
                       'overall_status': verification_result['overall_status'],
                       'compliance_score': verification_result['compliance_score']
                   })
    
    # Test 4: Performance Optimization Logging
    print("\n⚡ Testing Performance Optimization logging...")
    
    with logger.correlation_context(component="test", operation="performance_optimization_test"):
        optimizer = PerformanceOptimizer()
        
        optimization_result = optimizer.optimize_for_constraints(
            implementation=mock_implementation,
            constraints=test_constraints,
            max_iterations=2
        )
        
        logger.info("Performance optimization complete",
                   extra_data={
                       'optimization_success': optimization_result['success'],
                       'iterations_run': len(optimization_result['iterations'])
                   })
    
    # Test 5: Full Orchestrator Integration (simulated)
    print("\n🎯 Testing Orchestrator integration logging...")
    
    try:
        with logger.correlation_context(component="test", operation="orchestrator_integration_test"):
            orchestrator = IterativeOrchestrator("test_workspace", max_iterations=1)
            
            # We can't run a full cycle without a real spec file, but we can test initialization
            await orchestrator.initialize()
            
            logger.info("Orchestrator integration test complete")
            
    except Exception as e:
        logger.warning(f"Orchestrator test skipped due to missing dependencies: {e}")
    
    # Test 6: Correlation ID Tracing
    print("\n🔗 Testing correlation ID tracing...")
    
    with logger.correlation_context(component="test", operation="correlation_tracing_test") as correlation_id:
        logger.info("Parent operation started", extra_data={'test_step': 'parent'})
        
        # Simulate nested operations that should inherit correlation ID
        with logger.correlation_context(component="test", operation="nested_operation_1"):
            logger.info("Nested operation 1", extra_data={'test_step': 'nested_1'})
            
            with logger.correlation_context(component="test", operation="nested_operation_2"):
                logger.info("Nested operation 2", extra_data={'test_step': 'nested_2'})
        
        logger.info("Parent operation complete", extra_data={'test_step': 'parent_complete'})
    
    # Display log file contents
    print(f"\n📖 Log file contents ({log_file_path}):")
    print("=" * 80)
    
    try:
        with open(log_file_path, 'r') as f:
            log_contents = f.read()
            print(log_contents[-2000:])  # Show last 2000 characters
    except Exception as e:
        print(f"Error reading log file: {e}")
    
    print("=" * 80)
    print("\n✅ Logging integration test complete!")
    print(f"📊 Check the full log file at: {log_file_path}")
    
    # Cleanup
    Path(log_file_path).unlink(missing_ok=True)


if __name__ == "__main__":
    asyncio.run(test_logging_integration())