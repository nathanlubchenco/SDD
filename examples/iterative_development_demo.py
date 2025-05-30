#!/usr/bin/env python3
"""
Demo script for Iterative AI Development System.

This demonstrates the revolutionary generate→test→analyze→refine loop
where AI iteratively improves its own code through testing and analysis.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add SDD to Python path
sys.path.append(str(Path(__file__).parent.parent))

from orchestrator.iterative_orchestrator import IterativeOrchestrator


async def demo_simple_code_iteration():
    """Demonstrate iterative improvement on a simple code snippet."""
    
    print("🔬 Iterative AI Development Demo")
    print("=" * 50)
    
    # Initialize the orchestrator
    orchestrator = IterativeOrchestrator(
        workspace_path="workspaces/demo_iteration",
        max_iterations=3
    )
    
    await orchestrator.initialize()
    
    # Test with a deliberately flawed code snippet
    flawed_code = """
def calculate_average(numbers):
    total = 0
    for i in range(len(numbers)):
        total = total + numbers[i]
    return total / len(numbers)

def find_max(items):
    max_item = items[0]
    for i in range(len(items)):
        if items[i] > max_item:
            max_item = items[i]
    return max_item

class DataProcessor:
    def __init__(self):
        self.data = []
    
    def add_data(self, value):
        self.data.append(value)
    
    def process(self):
        if len(self.data) == 0:
            return None
        avg = calculate_average(self.data)
        max_val = find_max(self.data)
        return {"average": avg, "maximum": max_val}
"""
    
    print("🎯 Testing iterative improvement on deliberately flawed code...")
    print("\nOriginal code issues:")
    print("- Non-Pythonic loops (using range(len()) instead of direct iteration)")
    print("- No error handling for empty lists")
    print("- No type hints")
    print("- Missing docstrings")
    print("- Inefficient patterns")
    
    # Run quick iteration test
    result = await orchestrator.quick_iteration_test(
        code=flawed_code,
        target_score=85
    )
    
    print(f"\n📊 Analysis Results:")
    print(f"Original Quality Score: {result['quality_score']}/100")
    
    if result.get('improvement_needed'):
        print(f"✅ Improvement was needed (score < 85)")
        
        if result.get('refined_implementation'):
            print(f"Refined Quality Score: {result.get('refined_quality_score', 'N/A')}/100")
            print(f"Improvement Achieved: {result.get('improvement_achieved', False)}")
            
            print(f"\n🔧 Test Results Summary:")
            test_results = result.get('test_results', {})
            print(f"- Syntax Valid: {test_results.get('syntax_check', {}).get('valid', 'Unknown')}")
            print(f"- Dependencies OK: {test_results.get('dependency_check', {}).get('all_available', 'Unknown')}")
            print(f"- Linting Issues: {test_results.get('linting', {}).get('issues_count', 'Unknown')}")
            
            print(f"\n🎨 Code Quality Analysis:")
            analysis = result.get('analysis_results', {})
            quality_metrics = analysis.get('code_quality', {}).get('metrics', {})
            print(f"- Complexity Score: {quality_metrics.get('complexity', {}).get('overall', 'Unknown')}")
            print(f"- Lines of Code: {quality_metrics.get('lines_of_code', 'Unknown')}")
            print(f"- Readability Score: {quality_metrics.get('readability', {}).get('avg_line_length', 'Unknown')}")
            
            if result.get('refined_implementation'):
                print(f"\n🚀 Refined Code Preview:")
                refined_code = result['refined_implementation'].get('main_module', '')
                if refined_code and refined_code != "# No implementation generated":
                    # Show first few lines of refined code
                    lines = refined_code.split('\n')[:10]
                    for i, line in enumerate(lines, 1):
                        print(f"  {i:2d}: {line}")
                    if len(refined_code.split('\n')) > 10:
                        total_lines = len(refined_code.split('\n'))
                        print(f"  ... (showing first 10 lines of {total_lines} total)")
                else:
                    print("  No refined code available")
    else:
        print(f"✅ Code quality already meets target (score >= 85)")
    
    print(f"\n🎯 Demo completed successfully!")
    return result


async def demo_full_development_cycle():
    """Demonstrate a complete development cycle from specification."""
    
    print("\n🏗️  Full Development Cycle Demo")
    print("=" * 50)
    
    # Create a simple specification
    spec_path = Path("examples/task_manager/specification.yaml")
    
    if not spec_path.exists():
        print(f"❌ Specification file not found: {spec_path}")
        print("Using mock specification instead...")
        
        # Create mock specification for demo
        mock_spec = {
            "scenarios": [
                {
                    "scenario": "Add new task",
                    "given": "A task manager system",
                    "when": "User adds a new task with title and description",
                    "then": "Task is stored with unique ID and created timestamp"
                },
                {
                    "scenario": "List all tasks",
                    "given": "Tasks exist in the system",
                    "when": "User requests all tasks",
                    "then": "All tasks are returned in creation order"
                }
            ],
            "constraints": {
                "performance": {
                    "response_time": "< 100ms for basic operations"
                },
                "reliability": {
                    "data_persistence": "Tasks must survive system restart"
                }
            }
        }
        
        # Save mock spec temporarily
        temp_spec_path = Path("workspaces/demo_iteration/mock_spec.yaml")
        temp_spec_path.parent.mkdir(parents=True, exist_ok=True)
        
        import yaml
        with open(temp_spec_path, 'w') as f:
            yaml.dump(mock_spec, f, indent=2)
        
        spec_path = temp_spec_path
    
    # Initialize orchestrator
    orchestrator = IterativeOrchestrator(
        workspace_path="workspaces/demo_full_cycle",
        max_iterations=3
    )
    
    await orchestrator.initialize()
    
    print(f"📋 Running development cycle with specification: {spec_path}")
    
    # Run full development cycle
    try:
        cycle_result = await orchestrator.iterative_development_cycle(
            specification_path=str(spec_path),
            target_quality_score=75,
            include_docker=False  # Skip Docker for demo
        )
        
        print(f"\n📈 Development Cycle Results:")
        print(f"Success: {cycle_result.get('success', False)}")
        print(f"Total Iterations: {len(cycle_result.get('iterations', []))}")
        print(f"Final Quality Score: {cycle_result.get('final_quality_score', 0)}/100")
        
        # Show iteration progress
        print(f"\n🔄 Iteration Progress:")
        for i, iteration in enumerate(cycle_result.get('iterations', []), 1):
            print(f"  Iteration {i}: Score {iteration.get('quality_score', 0)}/100 - {'✅' if iteration.get('success') else '❌'}")
        
        # Show final summary
        summary = cycle_result.get('cycle_summary', {})
        if summary:
            print(f"\n📊 Development Summary:")
            print(f"- Quality Improvement: +{summary.get('quality_improvement', 0)} points")
            print(f"- Target Achieved: {summary.get('target_achieved', False)}")
            print(f"- Development Efficiency: {summary.get('development_efficiency', {}).get('convergence_rate', 'unknown')}")
            
            key_improvements = summary.get('key_improvements', [])
            if key_improvements:
                print(f"- Key Improvements: {', '.join(key_improvements[:3])}")
        
        print(f"\n🎯 Full development cycle completed!")
        return cycle_result
        
    except Exception as e:
        print(f"❌ Development cycle failed: {e}")
        return {"success": False, "error": str(e)}


async def main():
    """Run both demos."""
    
    print("🚀 SDD Iterative AI Development System Demo")
    print("This demonstrates AI that can test and improve its own code!")
    print("=" * 60)
    
    # Demo 1: Simple code iteration
    simple_result = await demo_simple_code_iteration()
    
    # Demo 2: Full development cycle (if simple demo worked)
    if simple_result.get('quality_score', 0) > 0:
        full_result = await demo_full_development_cycle()
    else:
        print("\n⚠️  Skipping full development cycle demo due to simple demo issues")
    
    print("\n🎉 Demo completed! This system enables:")
    print("  ✅ AI-driven iterative code improvement")
    print("  ✅ Automated testing and quality analysis")
    print("  ✅ Self-healing code that fixes its own issues")
    print("  ✅ Generate→Test→Analyze→Refine loops")
    print("\nThis is the future of AI-powered software development! 🤖")


if __name__ == "__main__":
    asyncio.run(main())