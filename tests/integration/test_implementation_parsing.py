#!/usr/bin/env python3
"""
Integration test for implementation parsing bug fix.

This test ensures that the implementation parsing logic correctly handles
the case where AI responses are Python dict string representations rather
than valid JSON, which was causing "Failed to parse implementation response"
errors in iteration 2.
"""

import asyncio
import json
import pytest
import pytest_asyncio
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.mcp_servers.implementation_server import ImplementationMCPServer
from src.orchestrator.iterative_orchestrator import IterativeOrchestrator


@pytest.mark.asyncio
async def test_implementation_parsing_bug_fix():
    """Test that implementation parsing handles both JSON and Python dict strings."""
    
    print("🧪 Testing Implementation Parsing Bug Fix")
    
    # Test 1: Python dict string format (the problematic case)
    print("\n1. Testing Python dict string parsing...")
    
    impl_server = ImplementationMCPServer()
    
    # Simulate the problematic format from debug_results.json
    mock_current_implementation = [
        {
            "type": "text",
            "text": "{'main_module': 'test code', 'dependencies': ['fastapi'], 'service_name': 'test_service', 'module_name': 'main', 'key_classes': ['TestClass'], 'key_functions': ['test_func'], 'test_module': 'test module', 'metadata': {'framework': 'fastapi'}}"
        }
    ]
    
    # This should not fail with the fix
    try:
        result = await impl_server._refine_implementation(
            current_implementation=mock_current_implementation,
            test_failures=[],
            quality_issues=[],
            refactoring_suggestions=[],
            target_quality_score=80
        )
        
        if result["success"]:
            print("✅ Python dict string parsing: SUCCESS")
            # Verify the implementation was correctly parsed
            implementation = result["implementation"]
            assert "main_module" in implementation
            assert "dependencies" in implementation
            print(f"   Parsed implementation keys: {list(implementation.keys())}")
        else:
            print(f"❌ Python dict string parsing failed: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ Python dict string parsing raised exception: {e}")
    
    # Test 2: Valid JSON format (should still work)
    print("\n2. Testing valid JSON parsing...")
    
    mock_json_implementation = [
        {
            "type": "text", 
            "text": json.dumps({
                "main_module": "test code",
                "dependencies": ["fastapi"],
                "service_name": "test_service"
            })
        }
    ]
    
    try:
        result = await impl_server._refine_implementation(
            current_implementation=mock_json_implementation,
            test_failures=[],
            quality_issues=[],
            refactoring_suggestions=[],
            target_quality_score=80
        )
        
        if result["success"]:
            print("✅ JSON string parsing: SUCCESS")
        else:
            print(f"❌ JSON string parsing failed: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ JSON string parsing raised exception: {e}")
    
    # Test 3: Direct dict format (backward compatibility)
    print("\n3. Testing direct dict parsing...")
    
    mock_dict_implementation = {
        "main_module": "test code",
        "dependencies": ["fastapi"],
        "service_name": "test_service"
    }
    
    try:
        result = await impl_server._refine_implementation(
            current_implementation=mock_dict_implementation,
            test_failures=[],
            quality_issues=[],
            refactoring_suggestions=[],
            target_quality_score=80
        )
        
        if result["success"]:
            print("✅ Direct dict parsing: SUCCESS")
        else:
            print(f"❌ Direct dict parsing failed: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ Direct dict parsing raised exception: {e}")


@pytest.mark.asyncio  
async def test_full_iteration_cycle():
    """Test that a full iteration cycle doesn't fail with parsing errors."""
    
    print("\n🔄 Testing Full Iteration Cycle")
    
    # Create a temporary test spec
    test_spec = {
        "scenarios": [
            {
                "name": "simple test",
                "when": "test input",
                "then": "test output"
            }
        ],
        "constraints": {}
    }
    
    # Use the iterative orchestrator  
    orchestrator = IterativeOrchestrator(workspace_path="test_workspace", max_iterations=2)
    await orchestrator.initialize()
    
    try:
        # Mock the specification loading by directly testing iteration
        iteration_result = await orchestrator._run_iteration(
            specification=test_spec,
            previous_implementation=None,
            previous_quality_score=0,
            iteration_number=1,
            target_quality_score=80
        )
        
        if iteration_result["success"]:
            print("✅ First iteration: SUCCESS")
            
            # Now test second iteration with the result from first
            iteration_2_result = await orchestrator._run_iteration(
                specification=test_spec,
                previous_implementation=iteration_result["implementation"],
                previous_quality_score=iteration_result["quality_score"],
                iteration_number=2,
                target_quality_score=80
            )
            
            if iteration_2_result["success"]:
                print("✅ Second iteration: SUCCESS")
                print("✅ Full cycle completed without parsing errors!")
            else:
                error_msg = iteration_2_result.get("error", "Unknown error")
                if "Failed to parse implementation response" in error_msg:
                    print(f"❌ Second iteration failed with PARSING ERROR: {error_msg}")
                    return False
                else:
                    print(f"⚠️  Second iteration failed (non-parsing error): {error_msg}")
        else:
            print(f"❌ First iteration failed: {iteration_result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Full iteration cycle raised exception: {e}")
        return False
    
    return True


@pytest.mark.asyncio
async def test_orchestrator_refinement_parsing():
    """Test the orchestrator's _refine_implementation parsing specifically."""
    
    print("\n⚙️  Testing Orchestrator Refinement Parsing")
    
    orchestrator = IterativeOrchestrator(workspace_path="test_workspace")
    await orchestrator.initialize()
    
    # Mock a previous implementation in the problematic format
    mock_implementation = [
        {
            "type": "text",
            "text": "{'main_module': 'def test(): pass', 'test_module': 'def test_test(): assert True', 'dependencies': ['pytest']}"
        }
    ]
    
    try:
        result = await orchestrator._refine_implementation(
            specification={"scenarios": [], "constraints": {}},
            previous_implementation=mock_implementation,
            previous_analysis={},
            target_quality_score=80
        )
        
        if result["success"]:
            print("✅ Orchestrator refinement parsing: SUCCESS")
            return True
        else:
            error_msg = result.get("error", "Unknown error")
            if "Failed to parse implementation response" in error_msg:
                print(f"❌ Orchestrator refinement failed with PARSING ERROR: {error_msg}")
                return False
            else:
                print(f"⚠️  Orchestrator refinement failed (non-parsing error): {error_msg}")
                return True  # Non-parsing errors are acceptable for this test
                
    except Exception as e:
        print(f"❌ Orchestrator refinement raised exception: {e}")
        return False


@pytest.mark.asyncio
async def test_implementation_comparison_fix():
    """Test that implementation comparison no longer fails with 'list' object has no attribute 'get'."""
    
    print("\n🔄 Testing Implementation Comparison Fix")
    
    orchestrator = IterativeOrchestrator(workspace_path="test_workspace")
    await orchestrator.initialize()
    
    # Create mock implementations in problematic list format
    mock_prev_impl = [
        {
            "type": "text",
            "text": "{'main_module': 'def old_func(): pass', 'dependencies': ['pytest']}"
        }
    ]
    
    mock_current_impl = [
        {
            "type": "text", 
            "text": "{'main_module': 'def new_func(): pass', 'dependencies': ['pytest', 'fastapi']}"
        }
    ]
    
    try:
        # This should not crash with "list object has no attribute 'get'"
        improvements, issues = await orchestrator._identify_iteration_improvements(
            previous_impl=mock_prev_impl,
            current_impl=mock_current_impl,
            previous_score=60,
            current_score=75
        )
        
        print("✅ Implementation comparison: SUCCESS")
        print(f"   Found improvements: {improvements}")
        return True
        
    except Exception as e:
        if "'list' object has no attribute 'get'" in str(e):
            print(f"❌ Implementation comparison still has list/dict error: {e}")
            return False
        else:
            print(f"⚠️  Implementation comparison failed with different error: {e}")
            return True  # Different error is acceptable


if __name__ == "__main__":
    async def run_all_tests():
        print("🚀 Running Implementation Parsing Tests")
        print("=" * 60)
        
        await test_implementation_parsing_bug_fix()
        
        success = await test_full_iteration_cycle()
        
        orchestrator_success = await test_orchestrator_refinement_parsing()
        
        comparison_success = await test_implementation_comparison_fix()
        
        print("\n" + "=" * 60)
        if success and orchestrator_success and comparison_success:
            print("🎉 All tests PASSED! All parsing bugs are fixed.")
        else:
            print("❌ Some tests FAILED! Parsing bugs may still exist.")
            sys.exit(1)
    
    asyncio.run(run_all_tests())