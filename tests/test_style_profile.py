import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from email_cli import (
    load_style_profile,
    save_style_profile,
    clear_style_profile,
    cmd_style_profile_show,
    cmd_style_profile_clear,
    cmd_style_profile_save,
)


class TestLoadStyleProfile:
    def test_returns_none_when_no_file(self, tmp_path, monkeypatch):
        monkeypatch.setattr("email_cli.SKILL_DIR", str(tmp_path))
        assert load_style_profile() is None

    def test_loads_existing_file(self, tmp_path, monkeypatch):
        monkeypatch.setattr("email_cli.SKILL_DIR", str(tmp_path))
        data = {"version": 1, "created": "2026-05-14", "summary": "test", "scenarios": []}
        (tmp_path / "style-profile.json").write_text(json.dumps(data))
        result = load_style_profile()
        assert result["summary"] == "test"


class TestSaveStyleProfile:
    def test_save_creates_file(self, tmp_path, monkeypatch):
        monkeypatch.setattr("email_cli.SKILL_DIR", str(tmp_path))
        save_style_profile("简短风格", [{"context": "闲聊", "example": "嗯"}])
        assert (tmp_path / "style-profile.json").exists()

    def test_save_structure(self, tmp_path, monkeypatch):
        monkeypatch.setattr("email_cli.SKILL_DIR", str(tmp_path))
        save_style_profile("test summary", [{"context": "c", "example": "e"}], source_files=["a.txt"])
        profile = load_style_profile()
        assert profile["version"] == 1
        assert profile["summary"] == "test summary"
        assert profile["scenarios"] == [{"context": "c", "example": "e"}]
        assert profile["source_files"] == ["a.txt"]

    def test_save_without_source_files(self, tmp_path, monkeypatch):
        monkeypatch.setattr("email_cli.SKILL_DIR", str(tmp_path))
        save_style_profile("test", [])
        profile = load_style_profile()
        assert profile["source_files"] == []

    def test_save_overwrites(self, tmp_path, monkeypatch):
        monkeypatch.setattr("email_cli.SKILL_DIR", str(tmp_path))
        save_style_profile("first", [])
        save_style_profile("second", [])
        assert load_style_profile()["summary"] == "second"


class TestClearStyleProfile:
    def test_clear_removes_file(self, tmp_path, monkeypatch):
        monkeypatch.setattr("email_cli.SKILL_DIR", str(tmp_path))
        save_style_profile("test", [])
        clear_style_profile()
        assert load_style_profile() is None

    def test_clear_no_file_is_noop(self, tmp_path, monkeypatch):
        monkeypatch.setattr("email_cli.SKILL_DIR", str(tmp_path))
        clear_style_profile()


class TestCmdStyleProfileShow:
    def test_show_no_profile(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setattr("email_cli.SKILL_DIR", str(tmp_path))
        cmd_style_profile_show(argparse.Namespace())
        assert "No style profile found" in capsys.readouterr().out

    def test_show_existing_profile(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setattr("email_cli.SKILL_DIR", str(tmp_path))
        save_style_profile("test summary", [{"context": "闲聊", "example": "嗯"}])
        cmd_style_profile_show(argparse.Namespace())
        output = capsys.readouterr().out
        assert "test summary" in output


class TestCmdStyleProfileClear:
    def test_clear(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setattr("email_cli.SKILL_DIR", str(tmp_path))
        save_style_profile("test", [])
        cmd_style_profile_clear(argparse.Namespace())
        assert load_style_profile() is None
        assert "cleared" in capsys.readouterr().out


class TestCmdStyleProfileSave:
    def test_save(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setattr("email_cli.SKILL_DIR", str(tmp_path))
        args = argparse.Namespace(
            summary="简洁风格",
            scenarios='[{"context":"闲聊","example":"嗯"}]',
            source_files='["chat.txt"]',
        )
        cmd_style_profile_save(args)
        profile = load_style_profile()
        assert profile["summary"] == "简洁风格"
        assert "saved" in capsys.readouterr().out

    def test_save_without_source_files(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setattr("email_cli.SKILL_DIR", str(tmp_path))
        args = argparse.Namespace(
            summary="test",
            scenarios='[]',
            source_files=None,
        )
        cmd_style_profile_save(args)
        profile = load_style_profile()
        assert profile["source_files"] == []
