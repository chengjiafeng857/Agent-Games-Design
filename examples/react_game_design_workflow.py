"""Example of using the ReAct agent for game design workflow."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agent_games_design.react_agent.cli_integration import ReActCLIHandler
from agent_games_design.react_agent.state import WorkflowStage


async def main():
    """Run the ReAct game design workflow example."""
    print("🎮 ReAct Game Design Workflow Example")
    print("=" * 50)

    # Initialize the CLI handler
    cli_handler = ReActCLIHandler()

    # Example game design prompts
    example_prompts = [
        "Create a mobile puzzle game with physics-based mechanics for casual players",
        "Design a retro-style platformer game with pixel art aesthetics",
        "Develop a multiplayer strategy game with fantasy theme for PC",
        "Build a virtual pet simulation game for mobile devices",
    ]

    print("Available example prompts:")
    for i, prompt in enumerate(example_prompts, 1):
        print(f"{i}. {prompt}")

    print("\nOr enter your own custom prompt.")

    # Get user input
    choice = input("\nSelect an example (1-4) or press Enter for custom: ").strip()

    if choice and choice.isdigit() and 1 <= int(choice) <= 4:
        user_prompt = example_prompts[int(choice) - 1]
        print(f"\n🎯 Selected: {user_prompt}")
    else:
        user_prompt = input("Enter your game design request: ").strip()
        if not user_prompt:
            print("❌ No prompt provided. Exiting.")
            return

    try:
        # Start the workflow
        print("\n🚀 Starting ReAct workflow...")
        session_id = await cli_handler.start_react_session(user_prompt)
        print(f"✅ Session started: {session_id}")

        # Main workflow loop
        while True:
            status = cli_handler.get_session_status(session_id)
            if not status:
                print("❌ Session not found")
                break

            current_stage = status["current_stage"]
            print(f"\n📍 Current Stage: {current_stage}")

            if current_stage == "human_approval":
                # Display plan for approval
                approval_request = cli_handler.display_approval_request(session_id)
                if approval_request:
                    print(approval_request)

                    # Get human approval
                    response = input("\nYour response: ").strip()
                    cli_handler.process_approval_response(session_id, response)

                    # Continue workflow if approved
                    await cli_handler.continue_workflow(session_id)

            elif current_stage == "react_execution":
                print("\n🤔 Executing ReAct reasoning...")
                progress = cli_handler.display_react_progress(session_id)
                if progress:
                    print(progress)

                await cli_handler.continue_workflow(session_id)

            elif current_stage == "asset_generation":
                print("\n🎨 Generating assets...")
                asset_status = cli_handler.display_assets_status(session_id)
                if asset_status:
                    print(asset_status)

                await cli_handler.continue_workflow(session_id)

            elif current_stage == "evaluation":
                print("\n📊 Evaluating workflow...")
                await cli_handler.continue_workflow(session_id)

                # Display evaluation results
                eval_results = cli_handler.display_evaluation_results(session_id)
                if eval_results:
                    print(eval_results)

            elif current_stage == "completed":
                print("\n✅ Workflow completed!")
                break

            else:
                print(f"❓ Unknown stage: {current_stage}")
                break

            # Brief pause between stages
            await asyncio.sleep(1)

        # Display final results
        print("\n" + "=" * 50)
        print("📋 FINAL RESULTS")
        print("=" * 50)

        results = cli_handler.get_results(session_id)
        if results:
            print(f"\n🎯 Session: {results['session_info']['session_id']}")
            print(f"📝 Original Request: {results['session_info']['user_prompt']}")

            # Display guidelines
            if results["guidelines"]:
                print(f"\n📖 Generated Guidelines:")
                print("-" * 30)
                print(results["guidelines"])

            # Display assets summary
            print(f"\n🎨 Generated Assets: {len(results['generated_assets'])}")
            for asset in results["generated_assets"]:
                status = "✅" if asset["image_url"] else "❌"
                quality = (
                    f"(Quality: {asset['quality_score']:.2f})" if asset["quality_score"] else ""
                )
                print(f"{status} {asset['title']} - {asset['type']} {quality}")

            # Display evaluation scores
            if results["evaluation"]:
                print(
                    f"\n📊 Overall Score: {results['evaluation'].get('overall_score', 0):.2f}/1.00"
                )

            # Ask if user wants to export results
            export = input("\n💾 Export results to JSON? (y/n): ").strip().lower()
            if export == "y":
                json_results = cli_handler.export_session_json(session_id)
                if json_results:
                    filename = f"react_results_{session_id[:8]}.json"
                    with open(filename, "w") as f:
                        f.write(json_results)
                    print(f"✅ Results exported to {filename}")

        # Cleanup
        cli_handler.cleanup_session(session_id)
        print("\n🧹 Session cleaned up. Goodbye!")

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("Make sure you have set your OPENAI_API_KEY in the .env file")


def interactive_demo():
    """Run an interactive demo of the ReAct workflow."""
    print("🎮 Interactive ReAct Game Design Demo")
    print("=" * 40)

    cli_handler = ReActCLIHandler()

    while True:
        print("\nAvailable commands:")
        print("1. start - Start a new workflow")
        print("2. list - List active sessions")
        print("3. status <session_id> - Get session status")
        print("4. continue <session_id> - Continue workflow")
        print("5. results <session_id> - Get results")
        print("6. quit - Exit")

        command = input("\nEnter command: ").strip().lower().split()

        if not command:
            continue

        if command[0] == "start":
            prompt = input("Enter game design request: ").strip()
            if prompt:
                try:
                    session_id = asyncio.run(cli_handler.start_react_session(prompt))
                    print(f"✅ Started session: {session_id}")
                except Exception as e:
                    print(f"❌ Error: {e}")

        elif command[0] == "list":
            sessions = cli_handler.list_active_sessions()
            if sessions:
                print("Active sessions:")
                for sid, status in sessions.items():
                    print(f"  {sid}: {status['current_stage']}")
            else:
                print("No active sessions")

        elif command[0] == "status" and len(command) > 1:
            status = cli_handler.get_session_status(command[1])
            if status:
                print(f"Session {command[1]}:")
                for key, value in status.items():
                    print(f"  {key}: {value}")
            else:
                print("Session not found")

        elif command[0] == "continue" and len(command) > 1:
            success = asyncio.run(cli_handler.continue_workflow(command[1]))
            if success:
                print("✅ Workflow continued")
            else:
                print("❌ Failed to continue workflow")

        elif command[0] == "results" and len(command) > 1:
            results = cli_handler.get_results(command[1])
            if results:
                print("Results:")
                print(f"  Guidelines: {'✅' if results['guidelines'] else '❌'}")
                print(f"  Assets: {len(results['generated_assets'])}")
                print(f"  Evaluation: {'✅' if results['evaluation'] else '❌'}")
            else:
                print("No results available")

        elif command[0] == "quit":
            print("Goodbye!")
            break

        else:
            print("❌ Invalid command")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        interactive_demo()
    else:
        asyncio.run(main())
