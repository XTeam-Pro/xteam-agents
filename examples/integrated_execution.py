"""
Example: Integrated Execution with Cognitive OS + Adversarial Agent Team

This example demonstrates how the integrated system works:
1. Simple tasks → Standard execution (fast, single LLM call)
2. Complex tasks → Adversarial execution (high quality, Agent Team)
"""

import asyncio
import uuid
from datetime import datetime

from xteam_agents.action.executor import ActionExecutor
from xteam_agents.config import Settings
from xteam_agents.graph.builder import build_cognitive_graph
from xteam_agents.llm.provider import LLMProvider
from xteam_agents.memory.manager import MemoryManager
from xteam_agents.models.state import AgentState


async def run_simple_task_example():
    """Example: Simple task using standard execution."""
    print("\n" + "=" * 80)
    print("🔹 EXAMPLE 1: SIMPLE TASK (Standard Execution)")
    print("=" * 80)

    # Initialize system
    settings = Settings()
    llm_provider = LLMProvider(settings)
    memory_manager = MemoryManager(settings)
    action_executor = ActionExecutor(settings)

    # Connect to memory
    await memory_manager.connect()

    try:
        # Build integrated graph
        print("\n📊 Building integrated cognitive graph...")
        graph = build_cognitive_graph(
            settings,
            llm_provider,
            memory_manager,
            action_executor,
        )
        print("✅ Graph built successfully (includes Adversarial Team)")

        # Create simple task
        task = AgentState(
            task_id=uuid.uuid4(),
            description="Fix typo in README.md: change 'recieve' to 'receive' on line 42",
            priority=1,
        )

        print(f"\n📝 Task: {task.description}")
        print(f"🆔 Task ID: {task.task_id}")

        # Execute
        print("\n🚀 Executing task...")
        start_time = datetime.now()

        result = await graph.ainvoke(task)

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Display results
        print("\n" + "=" * 80)
        print("📋 RESULTS")
        print("=" * 80)

        if isinstance(result, dict):
            complexity = result.get("context", {}).get("complexity", "unknown")
            execution_result = result.get("execution_result", "No result")
            is_validated = result.get("is_validated", False)
        else:
            complexity = result.context.get("complexity", "unknown")
            execution_result = result.execution_result or "No result"
            is_validated = result.is_validated

        print(f"\n🎯 Complexity: {complexity}")
        print(f"✅ Validated: {is_validated}")
        print(f"⏱️  Duration: {duration:.2f}s")

        print("\n📄 Execution Result:")
        print("-" * 80)
        print(execution_result)
        print("-" * 80)

        # Verify routing
        if complexity in ["simple", "medium"]:
            print("\n✅ Task was routed to STANDARD EXECUTION (as expected)")
        else:
            print("\n⚠️  Task was routed to ADVERSARIAL EXECUTION (unexpected for simple task)")

    finally:
        await memory_manager.disconnect()


async def run_complex_task_example():
    """Example: Complex task using adversarial execution."""
    print("\n\n" + "=" * 80)
    print("🔸 EXAMPLE 2: COMPLEX TASK (Adversarial Execution)")
    print("=" * 80)

    # Initialize system
    settings = Settings()
    llm_provider = LLMProvider(settings)
    memory_manager = MemoryManager(settings)
    action_executor = ActionExecutor(settings)

    # Connect to memory
    await memory_manager.connect()

    try:
        # Build integrated graph
        print("\n📊 Building integrated cognitive graph...")
        graph = build_cognitive_graph(
            settings,
            llm_provider,
            memory_manager,
            action_executor,
        )
        print("✅ Graph built successfully")

        # Create complex task
        task = AgentState(
            task_id=uuid.uuid4(),
            description=(
                "Design and implement a secure user authentication system with: "
                "JWT tokens, bcrypt password hashing, refresh tokens, "
                "role-based access control (RBAC), and rate limiting. "
                "Include security audit and performance optimization."
            ),
            priority=5,
        )

        print(f"\n📝 Task: {task.description}")
        print(f"🆔 Task ID: {task.task_id}")

        # Execute
        print("\n🚀 Executing task...")
        start_time = datetime.now()

        result = await graph.ainvoke(task)

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Display results
        print("\n" + "=" * 80)
        print("📋 RESULTS")
        print("=" * 80)

        if isinstance(result, dict):
            complexity = result.get("context", {}).get("complexity", "unknown")
            execution_result = result.get("execution_result", "No result")
            is_validated = result.get("is_validated", False)
            adv_metadata = result.get("context", {}).get("adversarial_execution", {})
        else:
            complexity = result.context.get("complexity", "unknown")
            execution_result = result.execution_result or "No result"
            is_validated = result.is_validated
            adv_metadata = result.context.get("adversarial_execution", {})

        print(f"\n🎯 Complexity: {complexity}")
        print(f"✅ Validated: {is_validated}")
        print(f"⏱️  Duration: {duration:.2f}s")

        # Display adversarial execution metadata if available
        if adv_metadata:
            print("\n🎭 Adversarial Team Execution:")
            print(f"  • Quality Score: {adv_metadata.get('quality_score', 'N/A')}/10")
            print(f"  • Total Pairs: {adv_metadata.get('total_pairs', 0)}")
            print(f"  • Approved Pairs: {adv_metadata.get('approved_pairs', 0)}")
            print(f"  • All Passed: {adv_metadata.get('all_pairs_passed', False)}")
            print(f"  • Conflicts Resolved: {adv_metadata.get('conflicts_resolved', 0)}")

        print("\n📄 Execution Result:")
        print("-" * 80)
        # Truncate if too long
        if len(execution_result) > 1000:
            print(execution_result[:1000] + "\n... (truncated)")
        else:
            print(execution_result)
        print("-" * 80)

        # Verify routing
        if complexity in ["complex", "critical"]:
            print("\n✅ Task was routed to ADVERSARIAL EXECUTION (as expected)")
            print("   Agent-Critic pairs worked together to ensure high quality")
        else:
            print("\n⚠️  Task was routed to STANDARD EXECUTION (unexpected for complex task)")

    finally:
        await memory_manager.disconnect()


async def run_comparison():
    """Run both examples to show the difference."""
    print("\n" + "=" * 80)
    print("🔗 INTEGRATED EXECUTION: Cognitive OS + Adversarial Agent Team")
    print("=" * 80)
    print("\nThis example demonstrates the integrated system:")
    print("• Simple tasks → Fast standard execution")
    print("• Complex tasks → High-quality adversarial execution")
    print("\n" + "=" * 80)

    # Run simple task example
    await run_simple_task_example()

    # Run complex task example
    await run_complex_task_example()

    # Summary
    print("\n\n" + "=" * 80)
    print("📊 SUMMARY")
    print("=" * 80)
    print("""
The integrated system provides:

✅ FLEXIBILITY
   - Automatic routing based on task complexity
   - Best execution mode for each task type

✅ EFFICIENCY
   - Simple tasks: Fast, lightweight execution
   - Complex tasks: Thorough, high-quality review

✅ QUALITY
   - Adversarial Team: Agent-Critic pairs
   - 5D scoring: Correctness, Completeness, Quality, Performance, Security
   - Conflict resolution by Orchestrator

✅ UNIFIED RESOURCES
   - Shared Memory Manager across all agents
   - Shared LLM Provider (connection pooling)
   - Memory invariants enforced
   - Complete audit trail

EXECUTION MODES:
┌─────────────┬──────────────┬────────────────────┐
│ Complexity  │ Execution    │ Use Case           │
├─────────────┼──────────────┼────────────────────┤
│ simple      │ Standard     │ Typo fixes, logs   │
│ medium      │ Standard     │ API endpoints      │
│ complex     │ Adversarial  │ Architecture       │
│ critical    │ Adversarial  │ Security, migration│
└─────────────┴──────────────┴────────────────────┘

The system is production-ready! 🚀
""")


async def main():
    """Main entry point."""
    try:
        await run_comparison()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("🎭 Integrated Execution Example")
    print("=" * 80)
    print("\nMake sure you have:")
    print("  • Set OPENAI_API_KEY or ANTHROPIC_API_KEY in .env")
    print("  • Redis, Qdrant, Neo4j, PostgreSQL running (or use mocks)")
    print("\nStarting in 3 seconds...")
    print("=" * 80)

    import time
    time.sleep(3)

    asyncio.run(main())
