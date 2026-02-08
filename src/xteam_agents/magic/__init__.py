"""Human MAGIC - Human Machine Artificial General Intelligence Core.

An optional overlay for human-AI collaboration at every pipeline stage.
When disabled (magic_config=None), the system works exactly as before.
"""

from xteam_agents.magic.core import MAGICCore
from xteam_agents.magic.escalation import EscalationRouter
from xteam_agents.magic.evolution import EvolutionEngine
from xteam_agents.magic.feedback import FeedbackCollector
from xteam_agents.magic.metacognition import MetacognitionEngine
from xteam_agents.magic.session import SessionManager

__all__ = [
    "MAGICCore",
    "MetacognitionEngine",
    "EscalationRouter",
    "FeedbackCollector",
    "SessionManager",
    "EvolutionEngine",
]
