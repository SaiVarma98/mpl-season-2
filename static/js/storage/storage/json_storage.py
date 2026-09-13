import json
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path
from threading import RLock

_LOCK = RLock()


@contextmanager
def transaction():
    """Hold the storage lock for an entire read-modify-write sequence.

    read_json/write_json each take the lock individually, which is enough to
    keep a single file write atomic but NOT enough to keep a whole
    "load documents -> mutate in memory -> save documents" operation atomic.
    Two overlapping requests (e.g. a bid racing a sell) could otherwise
    interleave between the read and the write. Callers that perform such a
    sequence should wrap the whole thing in `with transaction():`.
    """
    with _LOCK:
        yield

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
