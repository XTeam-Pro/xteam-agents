"""Example of using the adversarial agent team."""

import asyncio

from xteam_agents.agents.adversarial_graph import create_adversarial_graph
from xteam_agents.agents.adversarial_state import AdversarialAgentState
from xteam_agents.config import Settings


async def main():
    """Run adversarial agent team example."""
    print("🎭 Adversarial Agent Team Example\n")
    print("=" * 60)

    # Initialize settings
    settings = Settings()

    # Create the graph
    print("\n📊 Creating adversarial graph...")
    graph = create_adversarial_graph(settings)

    # Create initial state
    task = "Add user authentication API with JWT tokens"
    print(f"\n📝 Task: {task}\n")

    state = AdversarialAgentState(
        task_id="example_001",
        original_request=task,
    )

    # Execute the graph
    print("🚀 Starting execution...\n")
    print("-" * 60)

    try:
        # Run the graph
        final_state = await graph.ainvoke(state)

        print("\n" + "=" * 60)
        print("📋 EXECUTION COMPLETE")
        print("=" * 60)

        # Display orchestrator decision
        if final_state.orchestrator_decision:
            print("\n🎯 Orchestrator Decision:")
            print(f"  Summary: {final_state.orchestrator_decision.task_summary}")
            print(f"  Complexity: {final_state.orchestrator_decision.estimated_complexity}")
            print(f"  Selected Pairs: {[p.value for p in final_state.orchestrator_decision.selected_pairs]}")
            print(f"  Success Criteria: {final_state.orchestrator_decision.success_criteria}")

        # Display pair results
        print("\n👥 Pair Results:")
        for pair_type, pair_result in final_state.pair_results.items():
            print(f"\n  {pair_type.value}:")
            print(f"    Status: {pair_result.status.value}")
            print(f"    Iterations: {pair_result.iteration_count}")
            if pair_result.final_evaluation:
                score = pair_result.final_evaluation.average_score()
                print(f"    Final Score: {score:.1f}/10")
                print(f"    Approved: {pair_result.is_approved()}")

        # Display conflicts
        if final_state.conflicts:
            print(f"\n⚠️  Conflicts: {len(final_state.conflicts)}")
            for conflict in final_state.conflicts:
                print(f"    - {conflict.pair_type.value}: {conflict.resolved}")

        # Display final decision
        if final_state.orchestrator_final_decision:
            print("\n✅ Final Decision:")
            print(f"  Approved: {final_state.orchestrator_final_decision.approved}")
            print(f"  Quality Score: {final_state.orchestrator_final_decision.quality_score:.1f}/10")
            print(f"  Rationale: {final_state.orchestrator_final_decision.rationale[:200]}...")

        # Display statistics
        print("\n📊 Statistics:")
        stats = final_state.get_summary_stats()
        print(f"  Total Pairs: {stats['total_pairs']}")
        print(f"  Completed: {stats['completed_pairs']}")
        print(f"  Failed: {stats['failed_pairs']}")
        print(f"  Overall Quality: {stats['overall_quality_score']:.1f}/10")
        print(f"  Approval Rate: {stats['approval_rate']:.1%}")
        print(f"  Avg Iterations: {stats['average_iterations']:.1f}")
        print(f"  Escalation Rate: {stats['escalation_rate']:.1%}")

        print("\n" + "=" * 60)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
