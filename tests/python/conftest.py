"""Shared helpers: the pipeline scripts have digit-prefixed filenames, so
they are loaded by path rather than imported by name."""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "python"))


def load_script(stem: str):
    """Load python/<stem>.py as a module (cached per session)."""
    name = f"script_{stem.replace('-', '_')}"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(
        name, ROOT / "python" / f"{stem}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod
