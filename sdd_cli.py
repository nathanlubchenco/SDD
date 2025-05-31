#!/usr/bin/env python3
"""
SDD CLI Tool - Specification-Driven Development Command Line Interface

Generate, test, and analyze code using AI-powered iterative development.
"""

import argparse
import ast
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.orchestrator.iterative_orchestrator import IterativeOrchestrator
from src.core.ai_client import get_current_config, list_available_models
from src.core.ai_config import test_client
from src.core.sdd_logger import get_logger

def fix_test_imports(test_code: str, actual_service_name: str) -> str:
    """Fix common import issues in generated test code."""
    import re
    
    # Common problematic import patterns to replace
    problematic_imports = [
        r'from main_module import',
        r'from main import',
        r'import main_module',
        r'import main(?!\w)',  # import main but not mainframe, etc.
        r'from \.main_module import',
        r'from \.main import'
    ]
    
    # Replace with correct import
    fixed_code = test_code
    for pattern in problematic_imports:
        if re.search(pattern, fixed_code):
            # Replace with actual service name
            fixed_code = re.sub(pattern, f'from {actual_service_name} import', fixed_code)
    
    # Also fix any comments that still reference wrong module names
    fixed_code = re.sub(r'# test_module\.py', f'# test_{actual_service_name}.py', fixed_code)
    fixed_code = re.sub(r'""".*test_module.*"""', f'"""\nBehavioral tests for {actual_service_name}\n"""', fixed_code, flags=re.DOTALL)
    
    return fixed_code


class SDDCli:
    """Main CLI application for SDD."""
    
    def __init__(self):
        self.logger = get_logger("sdd.cli")
        
    def create_parser(self) -> argparse.ArgumentParser:
        """Create the main argument parser."""
        parser = argparse.ArgumentParser(
            prog='sdd',
            description='Specification-Driven Development CLI - Generate code from behavioral specifications',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Generate code from specification
  sdd generate specs/my_app.yaml --output workspaces/my_app --model gpt-4
  
  # Generate with specific options
  sdd generate specs/api.yaml -o workspaces/api --target-score 90 --include-docker
  
  # Test existing implementation
  sdd test workspaces/my_app --verbose
  
  # Analyze code quality
  sdd analyze src/my_code.py --include-suggestions
  
  # Show configuration
  sdd config --show
            """
        )
        
        subparsers = parser.add_subparsers(dest='command', help='Available commands')
        
        # Generate command
        self._add_generate_parser(subparsers)
        
        # Test command
        self._add_test_parser(subparsers)
        
        # Analyze command  
        self._add_analyze_parser(subparsers)
        
        # Config command
        self._add_config_parser(subparsers)
        
        return parser
    
    def _add_generate_parser(self, subparsers):
        """Add the generate subcommand parser."""
        generate_parser = subparsers.add_parser(
            'generate',
            help='Generate code from specification file',
            description='Generate implementation from YAML specification using AI-powered iterative development'
        )
        
        # Required arguments
        generate_parser.add_argument(
            'spec_file',
            type=str,
            help='Path to YAML specification file'
        )
        
        # Output options
        generate_parser.add_argument(
            '--output', '-o',
            type=str,
            help='Output directory (default: workspaces/<spec_name>)'
        )
        
        # AI model options
        generate_parser.add_argument(
            '--model', '-m',
            type=str,
            help='AI model to use (e.g., gpt-4, gpt-3.5-turbo, claude-3-opus)'
        )
        
        generate_parser.add_argument(
            '--provider',
            type=str,
            choices=['openai', 'anthropic'],
            help='AI provider to use (default: openai)'
        )
        
        # Quality options
        generate_parser.add_argument(
            '--target-score',
            type=int,
            default=80,
            help='Target quality score (0-100, default: 80)'
        )
        
        generate_parser.add_argument(
            '--max-iterations',
            type=int,
            default=5,
            help='Maximum improvement iterations (default: 5)'
        )
        
        # Framework options
        generate_parser.add_argument(
            '--framework',
            type=str,
            choices=['fastapi', 'flask', 'plain', 'auto'],
            default='auto',
            help='Target framework (default: auto)'
        )
        
        # Docker options
        generate_parser.add_argument(
            '--include-docker',
            action='store_true',
            help='Generate Docker configuration files'
        )
        
        generate_parser.add_argument(
            '--no-docker',
            action='store_true',
            help='Skip Docker generation (overrides --include-docker)'
        )
        
        # Output options
        generate_parser.add_argument(
            '--verbose', '-v',
            action='store_true',
            help='Verbose output'
        )
        
        generate_parser.add_argument(
            '--show-prompts',
            action='store_true',
            help='Display AI prompts and responses for debugging'
        )
        
        generate_parser.add_argument(
            '--quiet', '-q',
            action='store_true',
            help='Minimal output'
        )
        
        generate_parser.add_argument(
            '--save-results',
            type=str,
            help='Save detailed results to JSON file'
        )
    
    def _add_test_parser(self, subparsers):
        """Add the test subcommand parser."""
        test_parser = subparsers.add_parser(
            'test',
            help='Test existing implementation',
            description='Run comprehensive tests on existing implementation'
        )
        
        test_parser.add_argument(
            'workspace',
            type=str,
            help='Path to workspace directory'
        )
        
        test_parser.add_argument(
            '--verbose', '-v',
            action='store_true',
            help='Verbose test output'
        )
        
        test_parser.add_argument(
            '--show-prompts',
            action='store_true',
            help='Display AI prompts and responses for debugging'
        )
        
        test_parser.add_argument(
            '--save-results',
            type=str,
            help='Save test results to JSON file'
        )
    
    def _add_analyze_parser(self, subparsers):
        """Add the analyze subcommand parser."""
        analyze_parser = subparsers.add_parser(
            'analyze',
            help='Analyze code quality',
            description='Analyze code quality and get improvement suggestions'
        )
        
        analyze_parser.add_argument(
            'code_file',
            type=str,
            help='Path to code file to analyze'
        )
        
        analyze_parser.add_argument(
            '--include-suggestions',
            action='store_true',
            help='Include refactoring suggestions'
        )
        
        analyze_parser.add_argument(
            '--analysis-type',
            type=str,
            choices=['basic', 'comprehensive', 'performance'],
            default='comprehensive',
            help='Type of analysis to perform (default: comprehensive)'
        )
        
        analyze_parser.add_argument(
            '--show-prompts',
            action='store_true',
            help='Display AI prompts and responses for debugging'
        )
        
        analyze_parser.add_argument(
            '--save-results',
            type=str,
            help='Save analysis results to JSON file'
        )
    
    def _add_config_parser(self, subparsers):
        """Add the config subcommand parser."""
        config_parser = subparsers.add_parser(
            'config',
            help='Show or configure AI settings',
            description='Display current configuration or test AI connections'
        )
        
        config_parser.add_argument(
            '--show',
            action='store_true',
            help='Show current configuration'
        )
        
        config_parser.add_argument(
            '--list-models',
            action='store_true',
            help='List available AI models'
        )
        
        config_parser.add_argument(
            '--test-connection',
            action='store_true',
            help='Test AI provider connections'
        )
        
        config_parser.add_argument(
            '--provider',
            type=str,
            choices=['openai', 'anthropic'],
            help='Test specific provider'
        )
    
    async def run_generate(self, args) -> int:
        """Run the generate command."""
        try:
            # Validate spec file
            spec_path = Path(args.spec_file)
            if not spec_path.exists():
                print(f"❌ Specification file not found: {spec_path}")
                return 1
            
            # Determine output directory
            if args.output:
                output_dir = Path(args.output)
            else:
                spec_name = spec_path.stem
                output_dir = Path("workspaces") / spec_name
            
            if not args.quiet:
                print(f"🚀 Generating code from specification: {spec_path}")
                print(f"📁 Output directory: {output_dir}")
            
            # Configure AI model if specified
            if args.model:
                os.environ['ANTHROPIC_MODEL' if 'claude' in args.model.lower() else 'OPENAI_MODEL'] = args.model
            if args.provider:
                os.environ['AI_PROVIDER'] = args.provider
            
            # Initialize orchestrator
            orchestrator = IterativeOrchestrator(
                workspace_path=str(output_dir),
                max_iterations=args.max_iterations,
                verbose=args.verbose,
                show_prompts=getattr(args, 'show_prompts', False)
            )
            await orchestrator.initialize()
            
            # Determine Docker inclusion
            include_docker = args.include_docker and not args.no_docker
            
            if not args.quiet:
                print(f"⚙️  Target quality score: {args.target_score}/100")
                print(f"🔄 Max iterations: {args.max_iterations}")
                print(f"🐳 Docker generation: {'enabled' if include_docker else 'disabled'}")
                print(f"🎯 Framework: {args.framework}")
            
            # Run generation
            result = await orchestrator.iterative_development_cycle(
                specification_path=str(spec_path),
                target_quality_score=args.target_score,
                include_docker=include_docker
            )
            
            # Check if any implementation was generated
            iterations = result.get('iterations', [])
            has_implementation = any(iter_result.get('implementation') for iter_result in iterations)
            final_implementation = result.get('final_implementation', {})
            
            if result.get('success') or has_implementation or final_implementation:
                print(f"\n✅ Code generation completed!")
                
                # Show quality score with appropriate messaging
                final_score = result.get('final_quality_score', 0)
                if final_score > 0:
                    print(f"📊 Final quality score: {final_score}/100")
                else:
                    print(f"📊 Quality scoring: Mock/Limited (expected for demo system)")
                
                print(f"🔄 Iterations used: {len(iterations)}")
                
                # Try to write implementation to output directory
                if has_implementation or final_implementation:
                    output_dir.mkdir(parents=True, exist_ok=True)
                    
                    # Use final_implementation if available (preferred), otherwise use latest iteration
                    impl = None
                    
                    if final_implementation and isinstance(final_implementation, dict):
                        impl = final_implementation
                        if not args.quiet:
                            print(f"🔍 Using final_implementation for file extraction")
                    elif iterations:
                        # Fallback to latest iteration implementation
                        for iter_result in reversed(iterations):
                            iter_impl = iter_result.get('implementation')
                            
                            # Handle MCP-format responses (list with text content)
                            if iter_impl and isinstance(iter_impl, list) and iter_impl:
                                try:
                                    impl_text = iter_impl[0].get('text', '{}')
                                    # Try JSON first, then ast.literal_eval for Python dict format
                                    try:
                                        impl = json.loads(impl_text)
                                    except json.JSONDecodeError:
                                        impl = ast.literal_eval(impl_text)
                                    break
                                except (json.JSONDecodeError, ValueError, KeyError, IndexError, SyntaxError):
                                    if not args.quiet:
                                        print(f"⚠️  Could not parse implementation from MCP response")
                                    continue
                            elif iter_impl and isinstance(iter_impl, dict):
                                impl = iter_impl
                                break
                        
                        if impl and not args.quiet:
                            print(f"🔍 Using iteration implementation for file extraction")
                    
                    if impl and isinstance(impl, dict):
                        try:
                            files_written = []
                            
                            # Write main module - use service_name if available, otherwise fallback to output_dir.name
                            main_code = impl.get('main_module', '')
                            service_name = impl.get('service_name', output_dir.name)
                            # Ensure service_name is valid Python module name
                            if service_name:
                                # Convert to snake_case and remove invalid characters
                                import re
                                service_name = re.sub(r'[^a-zA-Z0-9_]', '_', service_name.lower())
                                service_name = re.sub(r'_+', '_', service_name).strip('_')
                            else:
                                service_name = output_dir.name
                            
                            if main_code:
                                main_file = output_dir / f"{service_name}.py"
                                with open(main_file, 'w') as f:
                                    f.write(main_code)
                                files_written.append(main_file.name)
                            
                            # Write test module - use same service_name for consistency
                            test_code = impl.get('test_module', '')
                            if test_code:
                                # Fix common import issues in test code
                                test_code = fix_test_imports(test_code, service_name)
                                test_file = output_dir / f"test_{service_name}.py"
                                with open(test_file, 'w') as f:
                                    f.write(test_code)
                                files_written.append(test_file.name)
                            
                            # Write requirements
                            deps = impl.get('dependencies', [])
                            if deps:
                                req_file = output_dir / "requirements.txt"
                                with open(req_file, 'w') as f:
                                    f.write('\n'.join(deps))
                                files_written.append(req_file.name)
                            
                            if files_written and not args.quiet:
                                print(f"✅ Successfully extracted {len(files_written)} files")
                                
                        except Exception as e:
                            if not args.quiet:
                                print(f"⚠️  Note: Could not extract files automatically: {e}")
                    else:
                        if not args.quiet:
                            print(f"⚠️  No valid implementation found for file extraction")
                
                print(f"\n📁 Output directory: {output_dir}")
                if output_dir.exists():
                    files = list(output_dir.glob("*"))
                    if files:
                        print("Generated files:")
                        for file_path in sorted(files):
                            if file_path.is_file():
                                print(f"  - {file_path.name}")
                    else:
                        print("⚠️  Directory created but no files extracted")
                
                print(f"\n🚀 Next steps:")
                print(f"  cd {output_dir}")
                if (output_dir / "requirements.txt").exists():
                    print(f"  pip install -r requirements.txt")
                main_file = output_dir / f"{output_dir.name}.py"
                if main_file.exists():
                    print(f"  python {main_file.name}")
                else:
                    print(f"  # Check generated files and run appropriate Python file")
                
                if include_docker and (output_dir / "Dockerfile").exists():
                    print(f"\n🐳 Docker commands:")
                    print(f"  docker build -t {output_dir.name} .")
                    print(f"  docker-compose up -d")
                
            else:
                print(f"\n❌ Code generation failed: {result.get('error', 'Unknown error')}")
                if not args.quiet:
                    print(f"💡 Try with --verbose to see detailed error information")
                return 1
            
            # Save results if requested
            if args.save_results:
                results_path = Path(args.save_results)
                with open(results_path, 'w') as f:
                    json.dump(result, f, indent=2, default=str)
                print(f"💾 Results saved to: {results_path}")
            
            return 0
            
        except Exception as e:
            print(f"❌ Generation failed: {e}")
            if args.verbose:
                import traceback
                traceback.print_exc()
            return 1
    
    async def run_test(self, args) -> int:
        """Run the test command."""
        try:
            workspace_path = Path(args.workspace)
            if not workspace_path.exists():
                print(f"❌ Workspace not found: {workspace_path}")
                return 1
            
            print(f"🧪 Testing implementation in: {workspace_path}")
            
            # Initialize orchestrator
            orchestrator = IterativeOrchestrator(str(workspace_path), verbose=args.verbose, show_prompts=getattr(args, 'show_prompts', False))
            await orchestrator.initialize()
            
            # Find the main implementation file
            impl_files = list(workspace_path.glob("*.py"))
            main_files = [f for f in impl_files if not f.name.startswith("test_")]
            
            if not main_files:
                print(f"❌ No implementation files found in {workspace_path}")
                return 1
            
            main_file = main_files[0]
            with open(main_file, 'r') as f:
                code = f.read()
            
            print(f"📝 Testing: {main_file.name}")
            
            # Run quick test
            result = await orchestrator.quick_iteration_test(code, target_score=75)
            
            print(f"\n📊 Test Results:")
            print(f"Quality Score: {result.get('quality_score', 0)}/100")
            
            test_results = result.get('test_results', {})
            print(f"✅ Syntax Valid: {test_results.get('syntax_check', {}).get('valid', 'Unknown')}")
            print(f"📦 Dependencies OK: {test_results.get('dependency_check', {}).get('all_available', 'Unknown')}")
            print(f"🔍 Linting Issues: {test_results.get('linting', {}).get('issues_count', 'Unknown')}")
            
            if args.save_results:
                results_path = Path(args.save_results)
                with open(results_path, 'w') as f:
                    json.dump(result, f, indent=2, default=str)
                print(f"💾 Results saved to: {results_path}")
            
            return 0
            
        except Exception as e:
            print(f"❌ Testing failed: {e}")
            if args.verbose:
                import traceback
                traceback.print_exc()
            return 1
    
    async def run_analyze(self, args) -> int:
        """Run the analyze command."""
        try:
            code_path = Path(args.code_file)
            if not code_path.exists():
                print(f"❌ Code file not found: {code_path}")
                return 1
            
            with open(code_path, 'r') as f:
                code = f.read()
            
            print(f"🔍 Analyzing: {code_path}")
            
            # Initialize orchestrator for analysis
            orchestrator = IterativeOrchestrator("temp_analysis", verbose=args.verbose, show_prompts=getattr(args, 'show_prompts', False))
            await orchestrator.initialize()
            
            # Create mock implementation for analysis
            mock_impl = {
                "main_module": code,
                "test_module": "# No tests",
                "dependencies": [],
                "service_name": code_path.stem
            }
            
            # Run analysis
            analysis_result = await orchestrator._analyze_implementation_quality(mock_impl)
            
            print(f"\n📊 Analysis Results:")
            
            code_quality = analysis_result.get('code_quality', {})
            print(f"Overall Score: {code_quality.get('overall_score', 0)}/100")
            
            if args.include_suggestions:
                suggestions = analysis_result.get('refactoring_suggestions', {})
                if suggestions.get('suggestions'):
                    print(f"\n💡 Refactoring Suggestions:")
                    for i, suggestion in enumerate(suggestions.get('suggestions', [])[:5], 1):
                        print(f"  {i}. {suggestion}")
            
            performance = analysis_result.get('performance_analysis', {})
            if performance.get('efficiency_score'):
                print(f"Performance Score: {performance.get('efficiency_score', 0)}/100")
            
            if args.save_results:
                results_path = Path(args.save_results)
                with open(results_path, 'w') as f:
                    json.dump(analysis_result, f, indent=2, default=str)
                print(f"💾 Results saved to: {results_path}")
            
            return 0
            
        except Exception as e:
            print(f"❌ Analysis failed: {e}")
            return 1
    
    def run_config(self, args) -> int:
        """Run the config command."""
        try:
            if args.show:
                config = get_current_config()
                print("🔧 Current AI Configuration:")
                print(f"Provider: {config.get('provider', 'openai')}")
                print(f"Model: {config.get('model', 'gpt-3.5-turbo')}")
                print(f"OpenAI API Key: {'✅ Set' if os.getenv('OPENAI_API_KEY') else '❌ Not set'}")
                print(f"Anthropic API Key: {'✅ Set' if os.getenv('ANTHROPIC_API_KEY') else '❌ Not set'}")
            
            elif args.list_models:
                models = list_available_models()
                print("🤖 Available AI Models:")
                for provider, provider_models in models.items():
                    print(f"\n{provider.upper()}:")
                    for model in provider_models:
                        print(f"  - {model}")
            
            elif args.test_connection:
                provider = args.provider or 'openai'
                print(f"🔗 Testing {provider} connection...")
                success = test_client(provider)
                if success:
                    print(f"✅ {provider} connection successful")
                else:
                    print(f"❌ {provider} connection failed")
                    return 1
            
            else:
                print("Use --show, --list-models, or --test-connection")
                return 1
            
            return 0
            
        except Exception as e:
            print(f"❌ Config operation failed: {e}")
            return 1
    
    async def run(self, args=None) -> int:
        """Run the CLI application."""
        parser = self.create_parser()
        args = parser.parse_args(args)
        
        if not args.command:
            parser.print_help()
            return 1
        
        # Set logging level based on verbosity
        if hasattr(args, 'verbose') and args.verbose:
            import logging
            logging.getLogger().setLevel(logging.DEBUG)
        elif hasattr(args, 'quiet') and args.quiet:
            import logging
            logging.getLogger().setLevel(logging.ERROR)
        
        # Route to appropriate command handler
        if args.command == 'generate':
            return await self.run_generate(args)
        elif args.command == 'test':
            return await self.run_test(args)
        elif args.command == 'analyze':
            return await self.run_analyze(args)
        elif args.command == 'config':
            return self.run_config(args)
        else:
            print(f"❌ Unknown command: {args.command}")
            return 1


def main():
    """Main entry point."""
    cli = SDDCli()
    try:
        exit_code = asyncio.run(cli.run())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⚠️ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()