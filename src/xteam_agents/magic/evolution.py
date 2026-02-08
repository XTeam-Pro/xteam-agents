"""EvolutionEngine - Tracks system improvement and progressive autonomy."""

import structlog

from xteam_agents.models.magic import (
    AutonomyLevel,
    EvolutionMetric,
    HumanPreferenceProfile,
)

logger = structlog.get_logger()


class EvolutionEngine:
    """Computes evolution metrics and recommends autonomy adjustments."""

    def __init__(self) -> None:
        self._escalation_count: int = 0
        self._escalation_resolved_count: int = 0
        self._first_pass_approvals: int = 0
        self._total_validations: int = 0
        self._feedback_count: int = 0
        self._guideline_count: int = 0

    def record_escalation(self, resolved: bool = False) -> None:
        self._escalation_count += 1
        if resolved:
            self._escalation_resolved_count += 1

    def record_validation(self, first_pass_approved: bool) -> None:
        self._total_validations += 1
        if first_pass_approved:
            self._first_pass_approvals += 1

    def record_feedback(self, converted_to_guideline: bool = False) -> None:
        self._feedback_count += 1
        if converted_to_guideline:
            self._guideline_count += 1

    def compute_metrics(self, period_days: int = 7) -> list[EvolutionMetric]:
        """Compute evolution metrics for the given period."""
        metrics = []

        # Escalation rate
        if self._total_validations > 0:
            escalation_rate = self._escalation_count / max(
                self._total_validations, 1
            )
            metrics.append(
                EvolutionMetric(
                    name="escalation_rate",
                    value=round(escalation_rate, 3),
                    period_days=period_days,
                    trend=self._compute_trend(escalation_rate, 0.3),
                )
            )

        # First-pass approval rate
        if self._total_validations > 0:
            fpa_rate = self._first_pass_approvals / self._total_validations
            metrics.append(
                EvolutionMetric(
                    name="first_pass_approval_rate",
                    value=round(fpa_rate, 3),
                    period_days=period_days,
                    trend=self._compute_trend(fpa_rate, 0.7, invert=True),
                )
            )

        # Feedback to guideline conversion rate
        if self._feedback_count > 0:
            f2g_rate = self._guideline_count / self._feedback_count
            metrics.append(
                EvolutionMetric(
                    name="feedback_to_guideline_rate",
                    value=round(f2g_rate, 3),
                    period_days=period_days,
                )
            )

        # Escalation resolution rate
        if self._escalation_count > 0:
            resolution_rate = (
                self._escalation_resolved_count / self._escalation_count
            )
            metrics.append(
                EvolutionMetric(
                    name="escalation_resolution_rate",
                    value=round(resolution_rate, 3),
                    period_days=period_days,
                )
            )

        return metrics

    def recommend_autonomy_adjustment(
        self,
        human_id: str,
        profile: HumanPreferenceProfile | None,
        domain: str | None = None,
    ) -> AutonomyLevel | None:
        """Recommend an autonomy level adjustment based on performance.

        - >90% approval over 20+ tasks -> recommend upgrade
        - <50% approval -> recommend downgrade
        """
        if not profile or profile.total_interactions < 10:
            return None

        approval_rate = profile.approval_rate
        interactions = profile.total_interactions
        current = profile.preferred_autonomy

        # Check domain-specific rate if available
        if domain and domain in profile.domains:
            approval_rate = profile.domains[domain]

        # Progressive trust: upgrade
        if interactions >= 20 and approval_rate >= 0.9:
            upgrade_map = {
                AutonomyLevel.SUPERVISED: AutonomyLevel.GUIDED,
                AutonomyLevel.GUIDED: AutonomyLevel.COLLABORATIVE,
                AutonomyLevel.COLLABORATIVE: AutonomyLevel.AUTONOMOUS,
                AutonomyLevel.AUTONOMOUS: AutonomyLevel.TRUSTED,
            }
            new_level = upgrade_map.get(current)
            if new_level:
                logger.info(
                    "autonomy_upgrade_recommended",
                    human_id=human_id,
                    from_level=current.value,
                    to_level=new_level.value,
                    approval_rate=approval_rate,
                )
                return new_level

        # Declining trust: downgrade
        if interactions >= 10 and approval_rate < 0.5:
            downgrade_map = {
                AutonomyLevel.TRUSTED: AutonomyLevel.AUTONOMOUS,
                AutonomyLevel.AUTONOMOUS: AutonomyLevel.COLLABORATIVE,
                AutonomyLevel.COLLABORATIVE: AutonomyLevel.GUIDED,
                AutonomyLevel.GUIDED: AutonomyLevel.SUPERVISED,
            }
            new_level = downgrade_map.get(current)
            if new_level:
                logger.info(
                    "autonomy_downgrade_recommended",
                    human_id=human_id,
                    from_level=current.value,
                    to_level=new_level.value,
                    approval_rate=approval_rate,
                )
                return new_level

        return None

    def generate_improvement_proposals(self) -> list[dict]:
        """Generate proposals for system improvement based on metrics."""
        proposals = []
        metrics = self.compute_metrics()

        metric_map = {m.name: m for m in metrics}

        escalation_rate = metric_map.get("escalation_rate")
        if escalation_rate and escalation_rate.value > 0.5:
            proposals.append({
                "area": "confidence_calibration",
                "proposal": "High escalation rate suggests confidence thresholds may be too low. Consider raising the threshold.",
                "priority": "medium",
            })

        fpa_rate = metric_map.get("first_pass_approval_rate")
        if fpa_rate and fpa_rate.value < 0.5:
            proposals.append({
                "area": "execution_quality",
                "proposal": "Low first-pass approval rate. Review execution prompts and consider adding more domain-specific guidelines.",
                "priority": "high",
            })

        f2g_rate = metric_map.get("feedback_to_guideline_rate")
        if f2g_rate and f2g_rate.value < 0.1 and self._feedback_count > 10:
            proposals.append({
                "area": "learning",
                "proposal": "Low feedback-to-guideline conversion. Encourage users to mark valuable feedback as persistent.",
                "priority": "low",
            })

        return proposals

    def _compute_trend(
        self, value: float, threshold: float, invert: bool = False
    ) -> str:
        if invert:
            if value > threshold:
                return "improving"
            elif value < threshold * 0.7:
                return "declining"
        else:
            if value < threshold:
                return "improving"
            elif value > threshold * 1.3:
                return "declining"
        return "stable"
