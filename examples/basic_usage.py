#!/usr/bin/env python3
"""
drowcoder Basic Usage Example

This example demonstrates how to use the drowcoder package to create and use an AI coding assistant.
"""

import sys
from pathlib import Path

# Import drowcoder (assumes it's installed or in development mode)
try:
    from drowcoder import DrowAgent, VerboseStyle
    from drowcoder.develop import main as develop_main
except ImportError:
    print("❌ drowcoder not available. Please run: pip install -e . or add src to PYTHONPATH")
    sys.exit(1)


def main():
    """Main example function"""

    print("🤖 drowcoder AI Coding Assistant Example")
    print("=" * 50)

    # Set up workspace directory
    workspace = Path.cwd()
    print(f"📁 Workspace: {workspace}")

    # Create Agent instance
    try:
        agent = DrowAgent(
            workspace=str(workspace),
            verbose_style=VerboseStyle.PRETTY,
            # Basic LLM configuration
            model="claude-3-sonnet-20240229",
            # You can add other litellm supported parameters here
        )

        print("✅ DrowAgent created successfully!")

        # Initialize Agent
        agent.init()
        print("✅ Agent initialization completed!")

        # Display available tools
        print(f"🛠️  Available tools count: {len(agent.tools)}")
        tool_names = [tool.get('function', {}).get('name', 'unknown') for tool in agent.tools]
        print(f"🔧 Tool list: {', '.join(tool_names)}")

        # Display system prompt preview (first 200 characters)
        if agent.system_prompt:
            preview = agent.system_prompt[:200] + "..." if len(agent.system_prompt) > 200 else agent.system_prompt
            print(f"📝 System prompt preview: {preview}")

        print("\n🎉 drowcoder package is working correctly!")
        print("💡 You can now use this Agent for AI-assisted programming.")

        # Optional: Start interactive session using develop mode
        start_interactive = input("\n🚀 Start interactive session? (y/N): ").strip().lower()
        if start_interactive == 'y':
            print("\nStarting interactive session using development mode...")
            print("Checkpoints will be saved to ./checkpoints/")
            print("Press Ctrl+C to exit.\n")

            # Use develop_main for consistent checkpoint handling
            return develop_main()

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
