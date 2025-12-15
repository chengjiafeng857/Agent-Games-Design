"""Command-line interface for the agent games design system."""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

from langchain_core.messages import HumanMessage

from .config import settings
from .graphs import create_agent_graph
from .logging_config import setup_logging
from .state import AgentState
from .tools import AVAILABLE_TOOLS, calculator, text_analyzer
from .utils.react_cli import SimpleReActCLI


def create_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="Agent Games Design - LangGraph-based agent system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Chat command
    chat_parser = subparsers.add_parser("chat", help="Start an interactive chat session")
    chat_parser.add_argument(
        "--model", default=None, help=f"Model to use (default: {settings.default_model})"
    )
    chat_parser.add_argument(
        "--temperature",
        type=float,
        default=settings.temperature,
        help=f"Temperature for generation (default: {settings.temperature})",
    )

    # Run command
    run_parser = subparsers.add_parser("run", help="Run a single query")
    run_parser.add_argument("query", help="Query to run")
    run_parser.add_argument(
        "--model", default=None, help=f"Model to use (default: {settings.default_model})"
    )
    run_parser.add_argument(
        "--temperature",
        type=float,
        default=settings.temperature,
        help=f"Temperature for generation (default: {settings.temperature})",
    )

    # Tools command
    tools_parser = subparsers.add_parser("tools", help="List available tools")

    # Examples command
    examples_parser = subparsers.add_parser("examples", help="Run example scenarios")
    examples_parser.add_argument(
        "example", nargs="?", choices=["basic", "tools", "react"], help="Example to run"
    )

    # ReAct workflow command
    react_parser = subparsers.add_parser("react", help="Run ReAct game design workflow")
    react_parser.add_argument("prompt", nargs="?", help="Game design request prompt (optional if --file is used)")
    react_parser.add_argument("--file", "-f", help="Read game design request from file")
    react_parser.add_argument("--interactive", action="store_true", help="Run in interactive mode")
    react_parser.add_argument("--evaluate", action="store_true", help="Enable LangSmith evaluation")
    react_parser.add_argument("--eval-only", action="store_true", help="Run evaluation example only")

    # Generate Config command
    gen_config_parser = subparsers.add_parser("generate-config", aliases=["gen-config"], help="Generate config from GDD file")
    gen_config_parser.add_argument("input_file", help="Path to the textual Game Design Document (GDD)")
    gen_config_parser.add_argument("--output", "-o", default="prompt_generation/configs/generated_config.yaml", help="Output YAML file path (default: prompt_generation/configs/generated_config.yaml)")
    gen_config_parser.add_argument(
        "--model", default=None, help=f"Model to use (default: {settings.default_model})"
    )

    # Global options
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Set logging level",
    )

    return parser


def run_chat_session(model: Optional[str] = None, temperature: float = 0.7) -> None:
    """Run an interactive chat session."""
    logger = logging.getLogger(__name__)
    logger.info("Starting interactive chat session...")

    # Check if API key is configured
    if not settings.openai_api_key:
        print("❌ Error: OPENAI_API_KEY not found in environment variables.")
        print("Please set your OpenAI API key in the .env file or environment variables.")
        return

    app = create_agent_graph()
    print("🤖 Agent Games Design Chat")
    print("Type 'quit', 'exit', or 'bye' to end the session.\n")

    session_id = "cli-session"
    config = {"configurable": {"thread_id": session_id}}

    while True:
        try:
            user_input = input("You: ").strip()

            if user_input.lower() in ["quit", "exit", "bye"]:
                print("👋 Goodbye!")
                break

            if not user_input:
                continue

            # Create initial state
            initial_state: AgentState = {
                "messages": [HumanMessage(content=user_input)],
                "current_task": user_input,
                "iterations": 0,
                "final_output": None,
            }

            print("🤔 Thinking...")

            # Stream the response
            for output in app.stream(initial_state, config):
                if "agent" in output:
                    messages = output["agent"].get("messages", [])
                    if messages:
                        last_message = messages[-1]
                        print(f"\n🤖 Agent: {last_message.content}")
                        break

            print()  # Empty line for spacing

        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            logger.error(f"Error in chat session: {e}")
            print(f"❌ Error: {e}")


def run_single_query(query: str, model: Optional[str] = None, temperature: float = 0.7) -> None:
    """Run a single query."""
    logger = logging.getLogger(__name__)
    logger.info(f"Running single query: {query}")

    # Check if API key is configured
    if not settings.openai_api_key:
        print("❌ Error: OPENAI_API_KEY not found in environment variables.")
        print("Please set your OpenAI API key in the .env file or environment variables.")
        return

    app = create_agent_graph()

    initial_state: AgentState = {
        "messages": [HumanMessage(content=query)],
        "current_task": query,
        "iterations": 0,
        "final_output": None,
    }

    config = {"configurable": {"thread_id": "single-query"}}

    print(f"🤖 Query: {query}")
    print("🤔 Processing...\n")

    # Run the agent
    for output in app.stream(initial_state, config):
        if "agent" in output:
            messages = output["agent"].get("messages", [])
            if messages:
                last_message = messages[-1]
                print(f"🤖 Response: {last_message.content}")
                break


def list_tools() -> None:
    """List available tools."""
    print("🔧 Available Tools:\n")

    for i, tool in enumerate(AVAILABLE_TOOLS, 1):
        print(f"{i}. {tool.name}")
        print(f"   Description: {tool.description}")
        print(f"   Args: {tool.args}")
        print()


def run_example(example: Optional[str] = None) -> None:
    """Run example scenarios."""
    if example is None:
        print("📚 Available examples:")
        print("  basic - Run a basic agent example")
        print("  tools - Demonstrate tool usage")
        print("  advanced - Run advanced agent with tool usage")
        print("  react - Run ReAct game design workflow")
        return

    if example == "basic":
        print("Running basic agent example...")
        print("Note: This requires OPENAI_API_KEY to be set.")
        print()

        # Run basic agent inline instead of importing
        if not settings.openai_api_key:
            print("❌ Error: OPENAI_API_KEY not found in environment variables.")
            return

        try:
            app = create_agent_graph()
            initial_state: AgentState = {
                "messages": [HumanMessage(content="What is 2 + 2? Explain your reasoning.")],
                "current_task": "Simple math problem",
                "iterations": 0,
                "final_output": None,
            }

            config = {"configurable": {"thread_id": "cli-basic-example"}}

            print("🤖 Starting Agent...\n")
            for step, output in enumerate(app.stream(initial_state, config), 1):
                print(f"Step {step}:")
                if "agent" in output:
                    messages = output["agent"].get("messages", [])
                    if messages:
                        last_message = messages[-1]
                        print(f"Agent Response: {last_message.content}\n")
                print("-" * 80)
            print("\n✅ Agent completed!")

        except Exception as e:
            print(f"❌ Error running basic example: {e}")

    elif example == "tools":
        print("Running tools example...")
        print()

        # Run tools example inline
        print("🔧 Tool Usage Examples\n")

        # Calculator example
        print("Calculator Tool:")
        result = calculator.invoke({"expression": "2 + 2 * 3"})
        print("  Expression: 2 + 2 * 3")
        print(f"  Result: {result}\n")

        # Text analyzer example
        print("Text Analyzer Tool:")
        text = "Hello world! This is a test. How are you?"
        result = text_analyzer.invoke({"text": text})
        print(f"  Text: {text}")
        print(f"  Analysis: {result}\n")

    elif example == "advanced":
        print("Running advanced agent example...")
        print("Note: This requires OPENAI_API_KEY to be set.")
        print()

        if not settings.openai_api_key:
            print("❌ Error: OPENAI_API_KEY not found in environment variables.")
            return

        # This would run the advanced example - for now just show tools
        print("🚀 Advanced features available!")
        print("- Tool-calling agents")
        print("- Complex workflows")
        print("- Multi-step reasoning")
        print("\nSee examples/advanced_agent.py for full implementation.")

    elif example == "react":
        print("Running ReAct game design workflow example...")
        print("Note: This requires OPENAI_API_KEY to be set.")
        print()

        if not settings.openai_api_key:
            print("❌ Error: OPENAI_API_KEY not found in environment variables.")
            return

        print("🎮 ReAct Game Design Workflow")
        print("This is a comprehensive workflow that:")
        print("1. 📋 Creates detailed execution plans")
        print("2. 👤 Requests human approval")
        print("3. 🤖 Uses ReAct reasoning for guidelines")
        print("4. 🎨 Generates game assets with AI models")
        print("5. 📊 Evaluates the entire workflow")
        print("\nSee examples/react_game_design_workflow.py for full demo.")

    else:
        print(f"❌ Unknown example: {example}")
        print("Available examples: basic, tools, advanced, react")


def run_react_workflow(prompt: str, interactive: bool = False, evaluate: bool = False) -> None:
    """Run the ReAct game design workflow.

    Args:
        prompt: The game design request
        interactive: Whether to run in interactive mode
        evaluate: Whether to enable LangSmith evaluation
    """
    logger = logging.getLogger(__name__)

    if not settings.openai_api_key:
        print("❌ Error: OPENAI_API_KEY not found in environment variables.")
        print("Please set your OpenAI API key in the .env file or environment variables.")
        return

    print("🎮 Starting ReAct Game Design Workflow...")
    print(f"📝 Request: {prompt[:100]}..." if len(prompt) > 100 else f"📝 Request: {prompt}")

    if interactive:
        print("\n🔄 Interactive mode - you'll be asked to approve the plan")
        
    if evaluate:
        print("\n📊 LangSmith evaluation enabled")

    # Run the ReAct workflow
    try:
        import asyncio

        async def run_workflow():
            cli = SimpleReActCLI()
            results = await cli.run_workflow(prompt, interactive)

            print(f"\n✅ Workflow completed!")
            print(f"📍 Status: {results['status']}")
            
            if results['plan_approved']:
                print("✅ Plan was approved")
            
            print(f"📋 Generated {len(results['execution_plan'])} execution steps")
            print(f"🎨 Identified {len(results['asset_requests'])} assets to generate")
            
            # Print asset generation results
            if results.get('generated_assets'):
                successful = len([a for a in results['generated_assets'] if a.get('image_url')])
                print(f"🖼️  Generated {successful}/{len(results['generated_assets'])} assets successfully")
                
                for asset in results['generated_assets']:
                    status = "✅" if asset.get('image_url') else "❌"
                    print(f"  {status} {asset['title']} ({asset['model_used']})")
                    if asset.get('image_url'):
                        print(f"     URL: {asset['image_url']}")
            
            # Print full guidelines to console
            if results['guidelines']:
                print("\n" + "="*80)
                print("📖 COMPREHENSIVE GAME DESIGN GUIDELINES")
                print("="*80 + "\n")
                print(results['guidelines'])
                print("\n" + "="*80)
            
            # Display saved files information
            if results.get('saved_files'):
                from pathlib import Path
                saved = results['saved_files']
                folder = Path(saved['folder'])
                
                print("\n" + "="*80)
                print("💾 OUTPUT FILES")
                print("="*80)
                print(f"\n📂 Output folder: {folder.absolute()}")
                
                if saved['markdown']:
                    print(f"📄 Markdown file: {Path(saved['markdown']).name}")
                
                if saved['assets']:
                    print(f"\n🖼️  Downloaded Assets ({len(saved['assets'])} files):")
                    for asset_path in saved['assets']:
                        asset_name = Path(asset_path).name
                        print(f"   ✅ {asset_name}")
                else:
                    print(f"\n🖼️  No assets downloaded")
                
                print(f"\n💡 Tip: Open {folder.name}/README.md to view the complete report with embedded images!")
                print("="*80)
            
            if results['errors']:
                print(f"\n⚠️ Errors encountered: {len(results['errors'])}")
                for error in results['errors']:
                    print(f"  - {error}")

        asyncio.run(run_workflow())

    except Exception as e:
        logger.error(f"Error in ReAct workflow: {e}")
        print(f"❌ Error: {e}")


def run_evaluation_example() -> None:
    """Run the LangSmith evaluation example."""
    print("🔍 Running LangSmith Evaluation Example...")
    print()
    
    try:
        import asyncio
        import subprocess
        import sys
        
        # Run the evaluation example
        example_path = "examples/langsmith_evaluation_example.py"
        
        async def run_example():
            # Import and run the evaluation example
            try:
                from pathlib import Path
                example_file = Path(example_path)
                
                if example_file.exists():
                    # Execute the example using subprocess to avoid import issues
                    result = subprocess.run([
                        sys.executable, str(example_file)
                    ], capture_output=True, text=True)
                    
                    if result.returncode == 0:
                        print(result.stdout)
                    else:
                        print("❌ Example execution failed:")
                        print(result.stderr)
                else:
                    print(f"❌ Example file not found: {example_path}")
                    print("💡 Create the example by running:")
                    print("uv run agent-games examples")
                    
            except Exception as e:
                print(f"❌ Error running evaluation example: {e}")
        
        asyncio.run(run_example())
        
    except Exception as e:
        print(f"❌ Error: {e}")


def main() -> None:
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()

    # Setup logging
    log_level = "DEBUG" if args.debug else args.log_level
    setup_logging(log_level)

    logger = logging.getLogger(__name__)

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        if args.command == "chat":
            run_chat_session(args.model, args.temperature)
        elif args.command == "run":
            run_single_query(args.query, args.model, args.temperature)
        elif args.command == "tools":
            list_tools()
        elif args.command == "examples":
            run_example(getattr(args, "example", None))
        elif args.command == "react":
            if args.eval_only:
                run_evaluation_example()
            else:
                prompt = args.prompt
                if args.file:
                    file_path = Path(args.file)
                    if not file_path.exists():
                        print(f"❌ Error: Input file not found: {args.file}")
                        sys.exit(1)
                    print(f"📄 Reading prompt from file: {args.file}")
                    try:
                        prompt = file_path.read_text(encoding="utf-8")
                    except Exception as e:
                        print(f"❌ Error reading file: {e}")
                        sys.exit(1)
                
                if not prompt:
                    print("❌ Error: You must provide a prompt or an input file.")
                    parser.parse_args(["react", "--help"])
                    sys.exit(1)

                run_react_workflow(prompt, args.interactive, args.evaluate)
        elif args.command == "generate-config":
            run_generate_config(
                args.input_file,
                args.output,
                args.model
            )
        else:
            parser.print_help()
            sys.exit(1)

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        print("\n👋 Goodbye!")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


def run_generate_config(input_file: str, output_file: str, model: Optional[str] = None) -> None:
    """Run the config generation command."""
    from .config_generator import generate_config_from_text
    
    input_path = Path(input_file)
    output_path = Path(output_file)
    
    if not input_path.exists():
        print(f"❌ Error: Input file not found: {input_file}")
        return

    print(f"📄 Reading GDD from: {input_file}")
    try:
        text = input_path.read_text(encoding="utf-8")
        
        print("🤖 Generating configuration with AI...")
        generated_configs = generate_config_from_text(text, model)
        
        if not generated_configs:
            print("⚠️ No characters found in text.")
            return

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if len(generated_configs) == 1:
            # Single character - use the exact output path specified
            _, yaml_config = generated_configs[0]
            output_path.write_text(yaml_config, encoding="utf-8")
            print(f"✅ Config generated successfully!")
            print(f"💾 Saved to: {output_file}")
        
        else:
            # Multiple characters - append name to filename
            print(f"✅ Found {len(generated_configs)} characters!")
            base_stem = output_path.stem
            ext = output_path.suffix or ".yaml"
            parent_dir = output_path.parent
            
            for char_name, yaml_config in generated_configs:
                # Create sanitized filename: base_name_CharName.yaml
                new_filename = f"{base_stem}_{char_name}{ext}"
                new_path = parent_dir / new_filename
                
                new_path.write_text(yaml_config, encoding="utf-8")
                print(f"💾 Saved: {new_path}")
                
    except Exception as e:
        print(f"❌ Error generating config: {e}")


if __name__ == "__main__":
    main()
