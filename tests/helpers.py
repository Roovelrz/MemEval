from __future__ import annotations

import shutil
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4


@contextmanager
def workspace_directory(label: str):
    """Create a writable test directory without tempfile's Windows ACL behavior."""
    root = Path.cwd() / ".test-artifacts" / f"{label}-{uuid4().hex}"
    root.mkdir(parents=True)
    try:
        yield root
    finally:
        shutil.rmtree(root)
