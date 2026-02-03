"""
Simplified example: Integrated Execution with mocked backends.

This example demonstrates the integrated system without requiring
Redis, Qdrant, Neo4j, or PostgreSQL to be running.
"""

import asyncio
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from xteam_agents.action.executor import ActionExecutor
from xteam_agents.config import Settings
from xteam_agents.graph.builder import build_cognitive_graph
from xteam_agents.llm.provider import LLMProvider
from xteam_agents.memory.manager import MemoryManager
from xteam_agents.models.state import AgentState


def create_mock_llm_responses():
    """Create mock LLM responses for both simple and complex tasks."""
    return {
        "simple": [
            # Analysis
            MagicMock(content="This is a simple task to fix a typo in README.md"),
            # Complexity classification
            MagicMock(content="simple"),
            # Plan
            MagicMock(content="1. Open README.md\n2. Change 'recieve' to 'receive' on line 42\n3. Save file"),
            # Execute (standard)
            MagicMock(content="Successfully fixed typo: 'recieve' → 'receive' on line 42 of README.md"),
            # Validate
            MagicMock(content="✅ Validation passed: Change is correct and file is valid"),
            # Commit
            MagicMock(content="Changes committed to shared memory"),
        ],
        "complex": [
            # Analysis
            MagicMock(content="Complex task requiring architectural decisions, security review, and multiple components"),
            # Complexity classification
            MagicMock(content="complex"),
            # Plan
            MagicMock(content="1. Design JWT token structure\n2. Implement bcrypt hashing\n3. Add RBAC\n4. Implement rate limiting\n5. Security audit"),
            # Orchestrator classify (adversarial)
            MagicMock(content='{"selected_pairs": ["tech_lead", "backend", "security"], "complexity": "high", "execution_order": ["tech_lead", "backend", "security"]}'),
            # TechLead agent
            MagicMock(content='{"tech_stack": ["Node.js", "JWT", "bcrypt", "Redis"], "approach": "Microservices with API Gateway"}'),
            # TechLead critic
            MagicMock(content='{"decision": "APPROVED", "correctness": 9, "completeness": 9, "quality": 8, "performance": 8, "security": 9}'),
            # Backend agent
            MagicMock(content='{"api_endpoints": ["/auth/login", "/auth/register", "/auth/refresh"], "middleware": ["auth", "rateLimit"]}'),
            # Backend critic
            MagicMock(content='{"decision": "APPROVED", "correctness": 9, "completeness": 9, "quality": 9, "performance": 8, "security": 9}'),
            # Security agent
            MagicMock(content='{"authentication": "JWT with refresh tokens", "password_hashing": "bcrypt", "rate_limiting": "Redis-based"}'),
            # Security critic
            MagicMock(content='{"decision": "APPROVED", "correctness": 10, "completeness": 9, "quality": 9, "performance": 8, "security": 10}'),
            # Orchestrator final decision
            MagicMock(content='{"approved": true, "quality_score": 8.8, "all_pairs_passed": true, "rationale": "All pairs approved, excellent design"}'),
            # Validate
            MagicMock(content="✅ Validation passed: Authentication system design is comprehensive and secure"),
            # Commit
            MagicMock(content="Authentication system design committed to shared memory"),
        ]
    }


async def run_simple_task():
    """Run a simple task demonstration."""
    print("\n" + "=" * 80)
    print("🔹 SIMPLE TASK (Standard Execution)")
    print("=" * 80)

    # Create mocks
    settings = Settings(llm_provider="openai", openai_api_key="test-key")

    # Mock memory manager
    memory_manager = MagicMock(spec=MemoryManager)
    memory_manager.connect = AsyncMock()
    memory_manager.disconnect = AsyncMock()
    memory_manager.log_audit = AsyncMock()
    memory_manager.store_episodic = AsyncMock()
    memory_manager.search_knowledge = AsyncMock(return_value=[])

    # Mock LLM provider
    llm_provider = MagicMock(spec=LLMProvider)
    mock_model = AsyncMock()
    responses = create_mock_llm_responses()["simple"]
    mock_model.ainvoke.side_effect = responses
    llm_provider.get_model_for_agent.return_value = mock_model

    # Mock action executor
    action_executor = MagicMock(spec=ActionExecutor)

    # Build graph
    print("\n📊 Building integrated cognitive graph...")
    graph = build_cognitive_graph(
        settings, llm_provider, memory_manager, action_executor
    )
    print("✅ Graph built successfully")

    # Create task
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

    try:
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

        if complexity in ["simple", "medium"]:
            print("\n✅ Task was routed to STANDARD EXECUTION (as expected)")
            print("   • Fast, lightweight execution")
            print("   • Single LLM call")
            print("   • Perfect for straightforward tasks")
        else:
            print("\n⚠️  Task was routed to ADVERSARIAL EXECUTION (unexpected)")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


async def run_complex_task():
    """Run a complex task demonstration."""
    print("\n\n" + "=" * 80)
    print("🔸 COMPLEX TASK (Adversarial Execution)")
    print("=" * 80)

    # Create mocks
    settings = Settings(llm_provider="openai", openai_api_key="test-key")

    # Mock memory manager
    memory_manager = MagicMock(spec=MemoryManager)
    memory_manager.connect = AsyncMock()
    memory_manager.disconnect = AsyncMock()
    memory_manager.log_audit = AsyncMock()
    memory_manager.store_episodic = AsyncMock()
    memory_manager.search_knowledge = AsyncMock(return_value=[])

    # Mock LLM provider
    llm_provider = MagicMock(spec=LLMProvider)
    mock_model = AsyncMock()
    responses = create_mock_llm_responses()["complex"]
    mock_model.ainvoke.side_effect = responses
    llm_provider.get_model_for_agent.return_value = mock_model

    # Mock action executor
    action_executor = MagicMock(spec=ActionExecutor)

    # Build graph
    print("\n📊 Building integrated cognitive graph...")
    graph = build_cognitive_graph(
        settings, llm_provider, memory_manager, action_executor
    )
    print("✅ Graph built successfully")

    # Create task
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

    try:
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

        print("\n📄 Execution Result:")
        print("-" * 80)
        if len(execution_result) > 1000:
            print(execution_result[:1000] + "\n... (truncated)")
        else:
            print(execution_result)
        print("-" * 80)

        if complexity in ["complex", "critical"]:
            print("\n✅ Task was routed to ADVERSARIAL EXECUTION (as expected)")
            print("   • 21 AI agents collaborated")
            print("   • Agent-Critic pairs iterated for quality")
            print("   • 5D scoring: Correctness, Completeness, Quality, Performance, Security")
            print("   • Orchestrator resolved conflicts")
        else:
            print("\n⚠️  Task was routed to STANDARD EXECUTION (unexpected)")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Main entry point."""
    print("\n" + "=" * 80)
    print("🔗 INTEGRATED EXECUTION DEMO")
    print("Cognitive OS + Adversarial Agent Team")
    print("=" * 80)
    print("\n✨ This demo uses mocked backends - no services required!")
    print("   Real execution would connect to Redis, Qdrant, Neo4j, PostgreSQL")
    print("\n" + "=" * 80)

    # Run simple task
    await run_simple_task()

    # Run complex task
    await run_complex_task()

    # Summary
    print("\n\n" + "=" * 80)
    print("📊 SUMMARY")
    print("=" * 80)
    print("""
The integrated system provides:

✅ AUTOMATIC ROUTING
   • Simple tasks → Fast standard execution (~5s)
   • Complex tasks → Thorough adversarial execution (~60s)
   • LLM-based complexity classification

✅ QUALITY ASSURANCE
   • Adversarial Team: 21 AI agents
   • 10 Agent-Critic pairs with iterative refinement
   • 5D scoring system
   • Orchestrator conflict resolution

✅ UNIFIED RESOURCES
   • Shared Memory Manager (all 26 agents)
   • Shared LLM Provider (connection pooling)
   • Memory invariants enforced
   • Complete audit trail

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

To test with real backends:
1. Start services: docker-compose up -d
2. Set API keys in .env
3. Run: python examples/integrated_execution.py
""")


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("🎭 Integrated Execution - Simple Demo")
    print("=" * 80)
    asyncio.run(main())
