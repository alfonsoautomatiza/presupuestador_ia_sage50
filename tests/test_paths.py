"""Tests for deployment-aware application data paths."""

import os
import sys

import tariff_parser


def test_resolver_prefers_frozen_executable_directory():
    assert tariff_parser._resolver_app_dir(True, "/module", False) == os.path.dirname(os.path.abspath(sys.executable))


def test_resolver_uses_source_module_directory():
    assert tariff_parser._resolver_app_dir(False, "/repo", True) == os.path.abspath("/repo")


def test_resolver_uses_expanded_environment_directory(monkeypatch, tmp_path):
    configured = tmp_path / "configured-data"
    monkeypatch.setenv("TARIFAS_DATA_DIR", str(configured))
    assert tariff_parser._resolver_app_dir(False, "/site-packages", False) == os.path.abspath(configured)


def test_resolver_defaults_to_per_user_directory(monkeypatch, tmp_path):
    monkeypatch.delenv("TARIFAS_DATA_DIR", raising=False)
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "xdg"))
    resolved = tariff_parser._resolver_app_dir(False, "/site-packages", False)
    assert os.path.isabs(resolved)
    assert resolved.endswith(os.path.join("tarifas-sage50"))


def test_init_dirs_creates_all_working_directories(monkeypatch, tmp_path):
    monkeypatch.setattr(tariff_parser, "DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setattr(tariff_parser, "ORIGINALES_DIR", str(tmp_path / "originales"))
    monkeypatch.setattr(tariff_parser, "PDF_DIR", str(tmp_path / "presupuestos"))
    monkeypatch.setattr(tariff_parser, "BACKUP_DIR", str(tmp_path / "backups"))
    monkeypatch.setattr(tariff_parser, "DATA_JSON", str(tmp_path / "data" / "tarifas.json"))
    monkeypatch.setattr(tariff_parser, "_bootstrap_bundled_data", lambda: None)
    monkeypatch.setattr(tariff_parser, "_migrar_datos_legacy", lambda: None)

    tariff_parser.init_dirs()

    for directory in (tariff_parser.DATA_DIR, tariff_parser.ORIGINALES_DIR,
                      tariff_parser.PDF_DIR, tariff_parser.BACKUP_DIR):
        assert os.path.isdir(directory)


def test_migrar_datos_legacy_copies_only_missing_files(monkeypatch, tmp_path):
    legacy = tmp_path / "legacy"
    destination = tmp_path / "new"
    (legacy / "data").mkdir(parents=True)
    destination.mkdir()
    for name in ("tarifas.json", "tarifas_simplificadas.xlsx", ".ultima_tarifa.json", ".ultimo_hash"):
        (legacy / "data" / name).write_text(f"legacy-{name}")
    (destination / "tarifas.json").write_text("existing")
    monkeypatch.setattr(tariff_parser, "__file__", str(legacy / "tariff_parser.py"))
    monkeypatch.setattr(tariff_parser, "DATA_DIR", str(destination))

    tariff_parser._migrar_datos_legacy()

    assert (destination / "tarifas.json").read_text() == "existing"
    assert (destination / ".ultimo_hash").read_text() == "legacy-.ultimo_hash"
    assert (destination / "tarifas_simplificadas.xlsx").exists()
    assert (destination / ".ultima_tarifa.json").exists()


def test_migrar_datos_legacy_is_noop_for_same_directory(monkeypatch, tmp_path):
    monkeypatch.setattr(tariff_parser, "__file__", str(tmp_path / "tariff_parser.py"))
    monkeypatch.setattr(tariff_parser, "DATA_DIR", str(tmp_path / "data"))
    os.makedirs(tariff_parser.DATA_DIR)
    (tmp_path / "data" / "tarifas.json").write_text("original")

    tariff_parser._migrar_datos_legacy()

    assert (tmp_path / "data" / "tarifas.json").read_text() == "original"


def test_migrar_datos_legacy_tolerates_unreadable_source(monkeypatch, tmp_path):
    legacy = tmp_path / "legacy"
    destination = tmp_path / "new"
    (legacy / "data").mkdir(parents=True)
    destination.mkdir()
    (legacy / "data" / "tarifas.json").mkdir()
    monkeypatch.setattr(tariff_parser, "__file__", str(legacy / "tariff_parser.py"))
    monkeypatch.setattr(tariff_parser, "DATA_DIR", str(destination))

    tariff_parser._migrar_datos_legacy()
