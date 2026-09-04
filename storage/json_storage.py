import json
import os
import tempfile
from pathlib import Path
from threading import RLock

_LOCK = RLock()

class JSONStorageError(RuntimeError):
    pass

def read_json(path, default=None):
    path = Path(path)
    with _LOCK:
        if not path.exists():
            return default
        try:
            with path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            raise JSONStorageError(f"Unable to read {path}") from exc

def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with _LOCK:
        fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.write("\n")
                f.flush()
                os.fsync(f.fileno())
            os.replace(temp_name, path)
        except (OSError, TypeError, ValueError) as exc:
            raise JSONStorageError(f"Unable to write {path}") from exc
        finally:
            if os.path.exists(temp_name):
                try:
                    os.unlink(temp_name)
                except OSError:
                    pass

def write_many_atomic(files):
    with _LOCK:
        for path, data in files.items():
            write_json(path, data)
