"""Regression checks for local quick-start auth bootstrap."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
START_SH = ROOT / "start.sh"
GITIGNORE = ROOT / ".gitignore"


def test_start_script_bootstraps_local_admin_without_fixed_default_password():
    script = START_SH.read_text(encoding="utf-8")

    assert "DEV_ADMIN_PASSWORD_FILE=" in script
    assert "config/.dev_admin_password" in script
    assert "generate_dev_admin_password" in script
    assert "secrets.choice" in script
    assert "path.chmod(0o600)" in script
    assert "export ADMIN_PASSWORD" in script
    assert "admin123" in script
    assert "AG_ALLOW_DEFAULT_ADMIN enabled" in script
    assert "export AG_ALLOW_DEFAULT_ADMIN=1" not in script


def test_dev_admin_password_file_is_gitignored():
    gitignore = GITIGNORE.read_text(encoding="utf-8")

    assert "config/.dev_admin_password" in gitignore
