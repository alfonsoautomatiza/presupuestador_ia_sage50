"""Tests for named quote templates."""
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
import pytest
import templates
from templates import borrar_plantilla, cargar_plantilla, guardar_plantilla, listar_plantillas  # pyright: ignore[reportMissingImports]
def _lineas():
    return [{"codigo": "A", "descripcion": "Servicio", "total": 12.5}]
def test_template_crud_roundtrip_and_payload_is_minimal(tmp_path):
    path = tmp_path / "nested" / "plantillas.json"
    guardar_plantilla(path, "Base", _lineas(), "Notas")
    assert listar_plantillas(path) == ["Base"]
    payload = cargar_plantilla(path, "Base")
    assert payload is not None
    assert payload["lineas"] == _lineas()
    assert payload["notas"] == "Notas"
    assert "iva_pct" not in payload and "cliente" not in payload
    assert borrar_plantilla(path, "Base") is True
    assert cargar_plantilla(path, "Base") is None
    assert borrar_plantilla(path, "Base") is False
def test_template_overwrite(tmp_path):
    path = tmp_path / "plantillas.json"
    guardar_plantilla(path, "Base", _lineas(), "old")
    guardar_plantilla(path, "Base", [], "new")
    payload = cargar_plantilla(path, "Base")
    assert payload is not None
    assert payload["notas"] == "new"
def test_template_missing_or_corrupt_file(tmp_path):
    path = tmp_path / "missing.json"
    assert listar_plantillas(path) == []
    assert cargar_plantilla(path, "Base") is None
    path.write_text("not json", encoding="utf-8")
    assert listar_plantillas(path) == []
    assert cargar_plantilla(path, "Base") is None
def test_template_save_recovers_corrupt_file(tmp_path):
    path = tmp_path / "plantillas.json"
    bad = b"not json"
    path.write_bytes(bad)
    guardar_plantilla(path, "Base", _lineas(), "Notas")
    backups = list(tmp_path.glob("plantillas.json.corrupt-*"))
    assert len(backups) == 1 and backups[0].read_bytes() == bad
    assert json.loads(path.read_text(encoding="utf-8"))["Base"]["notas"] == "Notas"
def test_atomic_replace_failure_preserves_store_and_cleans_temps(tmp_path, monkeypatch):
    path = tmp_path / "plantillas.json"
    guardar_plantilla(path, "Old", [], "unchanged")
    original = path.read_bytes()
    def fail_replace(*args):
        raise OSError("disk full")
    monkeypatch.setattr(templates.os, "replace", fail_replace)
    with pytest.raises(OSError, match="Could not save templates"):
        guardar_plantilla(path, "New", [], "new")
    assert path.read_bytes() == original
    assert not list(tmp_path.glob("plantillas.json.tmp-*"))
def test_old_lock_file_is_preserved_and_does_not_block_save(tmp_path):
    path = tmp_path / "plantillas.json"
    lock = path.with_name("plantillas.json.lock")
    lock.write_bytes(b"0"); os.utime(lock, (1, 1))
    guardar_plantilla(path, "Base", [], "ok")
    assert lock.read_bytes() == b"0"
    assert (cargar_plantilla(path, "Base") or {})["notas"] == "ok"

def test_concurrent_saves_preserve_every_template(tmp_path, monkeypatch):
    path = tmp_path / "plantillas.json"
    original_read = templates.__dict__["_read_store"]
    def delayed_read(ruta):
        time.sleep(0.005)
        return original_read(ruta)
    monkeypatch.setattr(templates, "_read_store", delayed_read)
    names = [f"Template-{index}" for index in range(20)]
    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(lambda name: guardar_plantilla(path, name, [], name), names))
    assert set(listar_plantillas(path)) == set(names)
def test_delete_on_corrupt_file_preserves_bytes(tmp_path):
    path = tmp_path / "plantillas.json"
    bad = b"{broken"
    path.write_bytes(bad)
    with pytest.raises(OSError, match="Could not update templates"):
        borrar_plantilla(path, "Base")
    assert path.read_bytes() == bad
