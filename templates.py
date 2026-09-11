"""Persistence helpers for named quote templates."""
import datetime
import json
import os
import tempfile
import threading
import time
from contextlib import contextmanager
if os.name == "nt":
    import msvcrt
else:
    import fcntl
_THREAD_LOCK = threading.RLock()
def _read_store(ruta):
    try:
        with open(ruta, "rb") as archivo:
            raw = archivo.read()
        datos = json.loads(raw.decode("utf-8"))
        return (datos if isinstance(datos, dict) else {}), False, raw
    except FileNotFoundError:
        return {}, False, None
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, TypeError):
        try:
            with open(ruta, "rb") as archivo:
                raw = archivo.read()
        except FileNotFoundError:
            raw = None
        return {}, raw is not None, raw
def _leer(ruta):
    return _read_store(ruta)[0]
@contextmanager
def _plantillas_lock(ruta):
    with _THREAD_LOCK:
        try:
            lock_file = os.fdopen(os.open(f"{ruta}.lock", os.O_RDWR | os.O_CREAT), "r+b")
        except OSError as error:
            raise OSError(f"Could not open templates lock: {ruta}") from error
        if not lock_file.read(1):
            lock_file.write(b"0")
            lock_file.flush()
        deadline = time.monotonic() + 10
        acquired = False
        while not acquired:
            try:
                lock_file.seek(0)
                if os.name == "nt":
                    msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                acquired = True
            except OSError:
                if time.monotonic() >= deadline:
                    lock_file.close()
                    raise OSError(f"Could not acquire templates lock: {ruta}")
                time.sleep(0.01)
        try:
            yield
        finally:
            try:
                if os.name == "nt":
                    msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
            finally:
                lock_file.close()
def _atomic_write(ruta, datos):
    parent = os.path.dirname(os.path.abspath(ruta))
    fd, temporary = tempfile.mkstemp(prefix=f"{os.path.basename(ruta)}.tmp-", dir=parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as archivo:
            json.dump(datos, archivo, ensure_ascii=False, indent=2)
            archivo.flush()
            os.fsync(archivo.fileno())
        os.replace(temporary, ruta)
    except (OSError, TypeError, ValueError):
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise

def listar_plantillas(ruta):
    """Return template names in sorted order, or an empty list on invalid storage."""
    return sorted(_leer(ruta))
def guardar_plantilla(ruta, nombre, lineas, notas):
    """Save lines and notes only, replacing an existing template with the same name."""
    try:
        os.makedirs(os.path.dirname(os.path.abspath(ruta)), exist_ok=True)
        with _plantillas_lock(ruta):
            datos, corrupto, raw = _read_store(ruta)
            if corrupto:
                backup = f"{ruta}.corrupt-{datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')}"
                assert raw is not None
                with open(backup, "wb") as archivo:
                    archivo.write(raw)
                    archivo.flush()
                    os.fsync(archivo.fileno())
            datos[nombre] = {"lineas": lineas, "notas": str(notas), "fecha": datetime.datetime.now(datetime.timezone.utc).isoformat()}
            _atomic_write(ruta, datos)
    except (OSError, TypeError, ValueError) as error:
        raise OSError(f"Could not save templates: {ruta}") from error
def cargar_plantilla(ruta, nombre):
    """Load one template or return None when it is unavailable."""
    return _leer(ruta).get(nombre)
def borrar_plantilla(ruta, nombre):
    """Delete one template and report whether it existed."""
    try:
        with _plantillas_lock(ruta):
            datos, corrupto, _ = _read_store(ruta)
            if corrupto:
                raise OSError("corrupt template storage")
            if nombre not in datos:
                return False
            del datos[nombre]
            _atomic_write(ruta, datos)
        return True
    except (OSError, TypeError, ValueError) as error:
        raise OSError(f"Could not update templates: {ruta}") from error
