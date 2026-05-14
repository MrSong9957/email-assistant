import os

import pytest


SKILL_MD_PATH = os.path.join(os.path.dirname(__file__), "..", "SKILL.md")


@pytest.fixture
def skill_content():
    with open(SKILL_MD_PATH) as f:
        return f.read()


class TestPersonaInSkill:
    def test_skill_contains_persona_section(self, skill_content):
        assert "人格化回复" in skill_content

    @pytest.mark.parametrize("key", ["sarcastic", "workplace", "customer", "romantic"])
    def test_skill_contains_all_persona_keys(self, skill_content, key):
        assert key in skill_content

    def test_skill_contains_priority_rule(self, skill_content):
        assert "优先级" in skill_content

    def test_skill_contains_style_profile_commands(self, skill_content):
        assert "style-profile" in skill_content

    def test_skill_contains_set_persona_command(self, skill_content):
        assert "set-persona" in skill_content
