import argparse
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from email_cli import (
    PERSONAS,
    cmd_set_persona,
    cmd_list_personas,
    load_persona_mapping,
    save_persona_mapping,
)


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


class TestCmdSetPersona:
    def test_set_default(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setattr("email_cli.SKILL_DIR", str(tmp_path))
        args = argparse.Namespace(default="sarcastic", to=None, persona=None)
        cmd_set_persona(args)
        assert "sarcastic" in capsys.readouterr().out
        mapping = load_persona_mapping()
        assert mapping["default_persona"] == "sarcastic"

    def test_set_recipient(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setattr("email_cli.SKILL_DIR", str(tmp_path))
        args = argparse.Namespace(default=None, to="a@b.com", persona="romantic")
        cmd_set_persona(args)
        mapping = load_persona_mapping()
        assert mapping["recipients"]["a@b.com"] == "romantic"

    def test_invalid_persona_exits(self, tmp_path, monkeypatch):
        monkeypatch.setattr("email_cli.SKILL_DIR", str(tmp_path))
        args = argparse.Namespace(default="nonexistent", to=None, persona=None)
        with pytest.raises(SystemExit):
            cmd_set_persona(args)

    def test_no_args_exits(self, tmp_path, monkeypatch):
        monkeypatch.setattr("email_cli.SKILL_DIR", str(tmp_path))
        args = argparse.Namespace(default=None, to=None, persona=None)
        with pytest.raises(SystemExit):
            cmd_set_persona(args)

    def test_to_without_persona_exits(self, tmp_path, monkeypatch):
        monkeypatch.setattr("email_cli.SKILL_DIR", str(tmp_path))
        args = argparse.Namespace(default=None, to="a@b.com", persona=None)
        with pytest.raises(SystemExit):
            cmd_set_persona(args)


class TestCmdListPersonas:
    def test_lists_all_persona_keys(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setattr("email_cli.SKILL_DIR", str(tmp_path))
        cmd_list_personas(argparse.Namespace())
        output = capsys.readouterr().out
        assert "sarcastic" in output
        assert "workplace" in output
        assert "customer" in output
        assert "romantic" in output
        assert "全局默认" in output

    def test_shows_recipient_mapping(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setattr("email_cli.SKILL_DIR", str(tmp_path))
        save_persona_mapping({"default_persona": "workplace", "recipients": {"x@y.com": "sarcastic"}})
        cmd_list_personas(argparse.Namespace())
        output = capsys.readouterr().out
        assert "x@y.com" in output
        assert "收件人映射" in output
