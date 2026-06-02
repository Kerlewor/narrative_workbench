"""Tests for core.doctor health checks."""

from pathlib import Path

from core.doctor import Doctor


def test_doctor_reports_missing_required_files(tmp_path: Path):
    root = tmp_path / "empty_project"
    root.mkdir()

    doctor = Doctor(root)
    doctor.check_required_files()

    assert doctor.errors
    assert any("CLAUDE.md" in error for error in doctor.errors)


def test_doctor_render_report_ok_with_warnings(tmp_path: Path):
    root = tmp_path / "project"
    root.mkdir()
    doctor = Doctor(root)
    doctor.warn("sample warning")

    report = doctor.render_report()

    assert "OK with warnings" in report
    assert "sample warning" in report

