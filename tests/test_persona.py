import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from email_cli import PERSONAS, load_persona_mapping, save_persona_mapping


class TestPersonas:
    def test_four_predefined_personas(self):
        assert set(PERSONAS.keys()) == {"sarcastic", "workplace", "customer", "romantic"}

    def test_each_persona_has_required_fields(self):
        for key, persona in PERSONAS.items():
            assert "name" in persona
            assert "instruction" in persona
            assert "example" in persona


class TestLoadPersonaMapping:
    def test_returns_default_when_no_file(self, tmp_path, monkeypatch):
        monkeypatch.setattr("email_cli.SKILL_DIR", str(tmp_path))
        result = load_persona_mapping()
        assert result == {"default_persona": "workplace", "recipients": {}}

    def test_loads_existing_file(self, tmp_path, monkeypatch):
        monkeypatch.setattr("email_cli.SKILL_DIR", str(tmp_path))
        data = {"default_persona": "sarcastic", "recipients": {"a@b.com": "romantic"}}
        (tmp_path / "persona-mapping.json").write_text(json.dumps(data))
        result = load_persona_mapping()
        assert result == data


class TestSavePersonaMapping:
    def test_save_and_load_roundtrip(self, tmp_path, monkeypatch):
        monkeypatch.setattr("email_cli.SKILL_DIR", str(tmp_path))
        data = {"default_persona": "customer", "recipients": {"x@y.com": "workplace"}}
        save_persona_mapping(data)
        loaded = load_persona_mapping()
        assert loaded == data

    def test_save_creates_file(self, tmp_path, monkeypatch):
        monkeypatch.setattr("email_cli.SKILL_DIR", str(tmp_path))
        save_persona_mapping({"default_persona": "workplace", "recipients": {}})
        assert (tmp_path / "persona-mapping.json").exists()

    def test_overwrite_existing(self, tmp_path, monkeypatch):
        monkeypatch.setattr("email_cli.SKILL_DIR", str(tmp_path))
        save_persona_mapping({"default_persona": "workplace", "recipients": {}})
        save_persona_mapping({"default_persona": "sarcastic", "recipients": {}})
        result = load_persona_mapping()
        assert result["default_persona"] == "sarcastic"
