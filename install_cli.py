#!/usr/bin/env python3
"""
SDD CLI Installation Script

This script sets up the SDD CLI for easy command-line usage.
"""

import os
import sys
import stat
from pathlib import Path

def create_sdd_wrapper():
    """Create a wrapper script that can be added to PATH."""
    
    # Get the project directory
    project_dir = Path(__file__).parent.absolute()
    cli_script = project_dir / "sdd_cli.py"
    
    # Create wrapper script content
    wrapper_content = f"""#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, "{project_dir}")
os.chdir("{project_dir}")

from sdd_cli import main
if __name__ == "__main__":
    main()
"""
    
    # Create wrapper in project directory
    wrapper_path = project_dir / "sdd"
    with open(wrapper_path, 'w') as f:
        f.write(wrapper_content)
    
    # Make it executable
    wrapper_path.chmod(wrapper_path.stat().st_mode | stat.S_IEXEC)
    
    return wrapper_path

def main():
    print("🚀 Installing SDD CLI...")
    
    # Create wrapper script
    wrapper_path = create_sdd_wrapper()
    print(f"✅ Created wrapper script: {wrapper_path}")
    
    # Instructions
    print(f"""
📋 Installation complete!

To use the SDD CLI, you have two options:

Option 1: Run directly from project directory
  cd {Path(__file__).parent}
  python sdd_cli.py <command> [options]

Option 2: Add to PATH for global access
  Add this to your shell profile (.bashrc, .zshrc, etc.):
  export PATH="{Path(__file__).parent}:$PATH"
  
  Then reload your shell or run:
  source ~/.bashrc  # or ~/.zshrc
  
  After that, you can use 'sdd' from anywhere:
  sdd generate specs/my_app.yaml --output workspaces/my_app

🔧 Quick start:
  1. Set your API key: export OPENAI_API_KEY="your-key-here"
  2. Check config: python sdd_cli.py config --show
  3. Generate code: python sdd_cli.py generate specs/my_spec.yaml

📚 For help: python sdd_cli.py --help
""")

if __name__ == "__main__":
    main()