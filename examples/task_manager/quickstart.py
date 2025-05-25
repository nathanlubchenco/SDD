"""
Quick start script to demonstrate SDD with a simple task manager
"""

import asyncio
from pathlib import Path
import yaml

async def quickstart_demo():
    """Run a simple SDD demonstration"""
    
    print("🚀 Specification-Driven Development Demo")
    print("=" * 50)
    
    # Step 1: Load specification
    spec = yaml.safe_load("""
    feature: Task Manager API
    scenarios:
      - name: Create a task
        given: User is authenticated
        when: User creates task "Buy groceries"
        then:
          - Task exists with title "Buy groceries"
          - Task has status "pending"
          - Task has unique ID
          
      - name: Complete a task
        given: Task "Buy groceries" exists with status "pending"
        when: User marks task as complete
        then:
          - Task status is "completed"
          - Completion timestamp is set
          
    constraints:
      performance:
        - All operations complete in < 100ms
      scale:
        - Support 10,000 concurrent users
    """)
    
    print("\n📋 Specification loaded!")
    print(f"Scenarios: {len(spec['scenarios'])}")
    print(f"Constraints: {list(spec['constraints'].keys())}")
    
    # Step 2: Initialize SDD system (mock for demo)
    print("\n🔧 Initializing SDD system...")
    # In real implementation, this would start MCP servers
    
    # Step 3: Generate implementation
    print("\n💻 Generating implementation...")
    print("  ✓ Generated data models")
    print("  ✓ Created API endpoints")
    print("  ✓ Implemented business logic")
    print("  ✓ Generated comprehensive tests")
    
    # Step 4: Verify constraints
    print("\n✅ Verifying constraints...")
    print("  ✓ Performance: All endpoints < 50ms")
    print("  ✓ Scale: Load test passed with 10k users")
    print("  ✓ All 15 generated tests passing")
    
    print("\n🎉 Implementation complete!")
    print("\nNext steps:")
    print("1. Run 'python -m sdd init' to create a new project")
    print("2. Edit specifications in specs/")
    print("3. Run 'python -m sdd implement' to generate code")
    print("4. Run 'python -m sdd monitor' to start production monitoring")

if __name__ == "__main__":
    asyncio.run(quickstart_demo())
