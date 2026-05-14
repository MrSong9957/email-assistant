import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from email_cli import load_style_profile, save_style_profile, clear_style_profile


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
