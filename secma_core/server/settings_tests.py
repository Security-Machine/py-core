import os.path
from pathlib import Path

import pytest
from pydantic import ValidationError


def test_settings_raises_if_missing_required(tmp_path: Path):
    cfg_file = os.path.join(tmp_path, "cfg.yaml")
    os.environ["SECURITY_MACHINE_CONFIG"] = cfg_file
    with open(cfg_file, "w") as f:
        f.write("log:\n" "  console_level: 10\n")
    with pytest.raises(ValidationError):
        from .settings import Settings

        Settings()


def test_settings(tmp_path: Path):
    cfg_file = os.path.join(tmp_path, "cfg.yaml")
    os.environ["SECURITY_MACHINE_CONFIG"] = cfg_file
    if "SECURITY_MACHINE_MANAGEMENT__TOKEN_SECRET" in os.environ:
        del os.environ["SECURITY_MACHINE_MANAGEMENT__TOKEN_SECRET"]
    if "SECURITY_MACHINE_MANAGEMENT__SUPER_PASSWORD" in os.environ:
        del os.environ["SECURITY_MACHINE_MANAGEMENT__SUPER_PASSWORD"]
    with open(cfg_file, "w") as f:
        f.write(
            "log:\n"
            "  console_level: 10\n"
            "management:\n"
            "  token_secret: secret\n"
            "  super_password: very-secret\n"
        )
    from .settings import Settings

    tested = Settings()
    assert tested.log.console_level == 10
    assert tested.log.others == {}
    assert tested.management.token_secret.get_secret_value() == "secret"
    assert tested.management.super_password.get_secret_value() == "very-secret"
