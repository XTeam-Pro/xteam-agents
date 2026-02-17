"""Tests for SpecLoader and YAML loading."""

from pathlib import Path

from xteam_agents.platform.loader import SpecLoader, get_default_specs_path
from xteam_agents.platform.registry import AgentRegistry, PipelineRegistry, TeamRegistry


class TestGetDefaultSpecsPath:
    def test_returns_path(self):
        p = get_default_specs_path()
        assert isinstance(p, Path)
        assert p.name == "specs"

    def test_default_path_exists(self):
        p = get_default_specs_path()
        assert p.exists(), f"Default specs path {p} does not exist"


class TestSpecLoader:
    def test_load_all_specs(self):
        agent_reg = AgentRegistry()
        pipeline_reg = PipelineRegistry()
        team_reg = TeamRegistry()
        loader = SpecLoader(agent_reg, pipeline_reg, team_reg)

        specs_path = get_default_specs_path()
        counts = loader.load_directory(specs_path)

        # Should have loaded agents from cognitive, adversarial, research
        assert counts["agents"] >= 20, f"Expected >= 20 agents, got {counts['agents']}"
        assert counts["pipelines"] >= 3, f"Expected >= 3 pipelines, got {counts['pipelines']}"
        assert counts["teams"] >= 2, f"Expected >= 2 teams, got {counts['teams']}"

    def test_loaded_agents_have_ids(self):
        agent_reg = AgentRegistry()
        pipeline_reg = PipelineRegistry()
        team_reg = TeamRegistry()
        loader = SpecLoader(agent_reg, pipeline_reg, team_reg)
        loader.load_directory(get_default_specs_path())

        agents = agent_reg.list_all()
        for agent in agents:
            assert agent.id, f"Agent has empty id: {agent}"
            assert agent.name, f"Agent {agent.id} has empty name"
            assert agent.role, f"Agent {agent.id} has empty role"
            assert agent.persona, f"Agent {agent.id} has empty persona"

    def test_cognitive_agents_loaded(self):
        agent_reg = AgentRegistry()
        pipeline_reg = PipelineRegistry()
        team_reg = TeamRegistry()
        loader = SpecLoader(agent_reg, pipeline_reg, team_reg)
        loader.load_directory(get_default_specs_path())

        # Check some cognitive agents exist
        cognitive = agent_reg.find_by_tags(["cognitive"])
        assert len(cognitive) >= 4

    def test_adversarial_agents_loaded(self):
        agent_reg = AgentRegistry()
        pipeline_reg = PipelineRegistry()
        team_reg = TeamRegistry()
        loader = SpecLoader(agent_reg, pipeline_reg, team_reg)
        loader.load_directory(get_default_specs_path())

        adversarial = agent_reg.find_by_tags(["adversarial"])
        assert len(adversarial) >= 8

    def test_pipelines_have_entry_points(self):
        agent_reg = AgentRegistry()
        pipeline_reg = PipelineRegistry()
        team_reg = TeamRegistry()
        loader = SpecLoader(agent_reg, pipeline_reg, team_reg)
        loader.load_directory(get_default_specs_path())

        for pipeline in pipeline_reg.list_all():
            assert pipeline.entry_point, f"Pipeline {pipeline.id} has no entry_point"

    def test_teams_have_pipelines(self):
        agent_reg = AgentRegistry()
        pipeline_reg = PipelineRegistry()
        team_reg = TeamRegistry()
        loader = SpecLoader(agent_reg, pipeline_reg, team_reg)
        loader.load_directory(get_default_specs_path())

        for team in team_reg.list_all():
            assert team.pipeline, f"Team {team.id} has no pipeline"

    def test_load_nonexistent_directory(self):
        agent_reg = AgentRegistry()
        pipeline_reg = PipelineRegistry()
        team_reg = TeamRegistry()
        loader = SpecLoader(agent_reg, pipeline_reg, team_reg)

        counts = loader.load_directory(Path("/nonexistent/path"))
        assert counts == {"agents": 0, "pipelines": 0, "teams": 0}
