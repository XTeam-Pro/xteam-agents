"""Load agent, pipeline, and team specs from YAML files.

Scans directories for .yml files and registers them with the appropriate registry.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import structlog

from xteam_agents.platform.registry import AgentRegistry, PipelineRegistry, TeamRegistry
from xteam_agents.platform.spec import AgentSpec, PipelineSpec, TeamSpec

logger = structlog.get_logger()


def _read_yaml(path: Path) -> dict[str, Any] | None:
    """Read and parse a YAML file."""
    try:
        import yaml
    except ImportError:
        logger.error("pyyaml_not_installed", hint="pip install pyyaml")
        return None

    try:
        with open(path) as f:
            data = yaml.safe_load(f)
        if not isinstance(data, dict):
            logger.warning("yaml_not_dict", file=str(path))
            return None
        return data
    except Exception as e:
        logger.error("yaml_parse_error", file=str(path), error=str(e))
        return None


class SpecLoader:
    """Loads YAML specifications into registries."""

    def __init__(
        self,
        agent_registry: AgentRegistry,
        pipeline_registry: PipelineRegistry,
        team_registry: TeamRegistry,
    ) -> None:
        self.agent_registry = agent_registry
        self.pipeline_registry = pipeline_registry
        self.team_registry = team_registry

    def load_directory(self, base_path: Path) -> dict[str, int]:
        """Load all specs from a directory tree.

        Expected structure:
            base_path/agents/     -> AgentSpec
            base_path/pipelines/  -> PipelineSpec
            base_path/teams/      -> TeamSpec
        """
        counts = {"agents": 0, "pipelines": 0, "teams": 0}

        agents_dir = base_path / "agents"
        if agents_dir.exists():
            counts["agents"] = self._load_agents(agents_dir)

        pipelines_dir = base_path / "pipelines"
        if pipelines_dir.exists():
            counts["pipelines"] = self._load_pipelines(pipelines_dir)

        teams_dir = base_path / "teams"
        if teams_dir.exists():
            counts["teams"] = self._load_teams(teams_dir)

        logger.info(
            "specs_loaded",
            agents=counts["agents"],
            pipelines=counts["pipelines"],
            teams=counts["teams"],
            base_path=str(base_path),
        )
        return counts

    def _load_agents(self, directory: Path) -> int:
        count = 0
        for yml_file in sorted(directory.rglob("*.yml")):
            try:
                data = _read_yaml(yml_file)
                if data:
                    spec = AgentSpec(**data)
                    self.agent_registry.register(spec)
                    count += 1
            except Exception as e:
                logger.error("agent_spec_load_failed", file=str(yml_file), error=str(e))
        return count

    def _load_pipelines(self, directory: Path) -> int:
        count = 0
        for yml_file in sorted(directory.rglob("*.yml")):
            try:
                data = _read_yaml(yml_file)
                if data:
                    spec = PipelineSpec(**data)
                    self.pipeline_registry.register(spec)
                    count += 1
            except Exception as e:
                logger.error("pipeline_spec_load_failed", file=str(yml_file), error=str(e))
        return count

    def _load_teams(self, directory: Path) -> int:
        count = 0
        for yml_file in sorted(directory.rglob("*.yml")):
            try:
                data = _read_yaml(yml_file)
                if data:
                    spec = TeamSpec(**data)
                    self.team_registry.register(spec)
                    count += 1
            except Exception as e:
                logger.error("team_spec_load_failed", file=str(yml_file), error=str(e))
        return count


def get_default_specs_path() -> Path:
    """Get the default specs directory path."""
    return Path(__file__).parent.parent / "specs"
